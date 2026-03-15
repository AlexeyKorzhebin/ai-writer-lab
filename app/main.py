from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.llm import OpenAIAdapter
from app.core.database import Base, engine, get_db
from app.core.models import Project, Chapter
from app.core.writer_pipeline import WriterPipeline
from app.core.exporter import EPUBExporter
from app.core.pdf_exporter import PDFExporter
from app.core.docx_exporter import DOCXExporter
from app.core.agents.reviewer import ReviewAgent
from app.core.agents.editor import EditorAgent
from app.core.agents.orchestrator import OrchestratorAgent
from app.core.agents.consistency import ConsistencyAgent
from app.core.agents.book_orchestrator import BookOrchestrator
from app.core.agents.book_rewrite_orchestrator import BookRewriteOrchestrator
from fastapi.responses import FileResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Writer Lab")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ---------- Init DB ----------
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---------- LLM Adapter (Dependency Injection) ----------

def get_llm():
    try:
        return OpenAIAdapter()
    except Exception:
        return None

# ---------- Schemas ----------
class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    model_name: str | None = None
    temperature: str | None = None
    max_tokens: str | None = None
    author_name: str | None = None
    author_style: str | None = None

# ---------- Routes ----------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project))
    projects = result.scalars().all()

    return templates.TemplateResponse(
        "home.html",
        {"request": request, "projects": projects}
    )

@app.post("/projects")
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(
        title=data.title,
        description=data.description,
        model_name=data.model_name,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        author_name=data.author_name,
        author_style=data.author_style,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return {"id": project.id}

@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def get_project(project_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return HTMLResponse(content="Project not found", status_code=404)

    result = await db.execute(select(Chapter).where(Chapter.project_id == project_id))
    chapters = result.scalars().all()

    return templates.TemplateResponse(
        "project.html",
        {"request": request, "project": project, "chapters": chapters}
    )

@app.get("/projects/{project_id}/chapters/{chapter_id}", response_class=HTMLResponse)
async def get_chapter(project_id: int, chapter_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return HTMLResponse(content="Project not found", status_code=404)

    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()

    if not chapter:
        return HTMLResponse(content="Chapter not found", status_code=404)

    return templates.TemplateResponse(
        "chapter.html",
        {"request": request, "project": project, "chapter": chapter}
    )

@app.post("/projects/{project_id}/chapters/{chapter_id}/update")
async def update_chapter(project_id: int, chapter_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()

    if not chapter:
        return {"error": "Chapter not found"}

    chapter.content = data.get("content")
    await db.commit()

    return {"status": "saved"}

@app.post("/projects/{project_id}/update-author")
async def update_author(project_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return {"error": "Project not found"}

    project.author_name = data.get("author_name")
    project.author_style = data.get("author_style")

    await db.commit()
    return {"status": "updated"}

@app.post("/projects/{project_id}/chapters")
async def create_chapter(project_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    chapter = Chapter(
        project_id=project_id,
        title=data.get("title"),
        content=None,
    )
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)

    return {"id": chapter.id}

@app.post("/projects/{project_id}/generate-chapter/{chapter_id}")
async def generate_chapter(project_id: int, chapter_id: int, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    # Eager load project to avoid async lazy-loading issues
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Chapter)
        .options(
            selectinload(Chapter.project)
            .selectinload(Project.chapters)
        )
        .where(Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()

    if not chapter:
        return {"error": "Chapter not found"}

    if not llm:
        chapter.content = "LLM not configured"
    else:
        pipeline = WriterPipeline(llm)
        content, summary = await pipeline.generate_chapter(chapter.project, chapter)
        chapter.content = content
        chapter.summary = summary

    await db.commit()
    return {"status": "ok"}

@app.post("/projects/{project_id}/review/{chapter_id}")
async def review_chapter(project_id: int, chapter_id: int, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()

    if not chapter:
        return {"error": "Chapter not found"}

    if not llm:
        return {"error": "LLM not configured"}

    reviewer = ReviewAgent(llm)
    review = await reviewer.review_chapter(chapter.project, chapter)

    return {"review": review}

@app.post("/projects/{project_id}/edit/{chapter_id}")
async def edit_chapter(project_id: int, chapter_id: int, data: dict, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()

    if not chapter:
        return {"error": "Chapter not found"}

    if not llm:
        return {"error": "LLM not configured"}

    review_text = data.get("review")
    if not review_text:
        return {"error": "Review text required"}

    editor = EditorAgent(llm)
    improved = await editor.apply_improvements(chapter.project, chapter, review_text)

    chapter.content = improved
    await db.commit()

    return {"status": "improved"}

@app.post("/projects/{project_id}/produce-hq/{chapter_id}")
async def produce_high_quality(project_id: int, chapter_id: int, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()

    if not chapter:
        return {"error": "Chapter not found"}

    if not llm:
        return {"error": "LLM not configured"}

    writer_pipeline = WriterPipeline(llm)
    reviewer = ReviewAgent(llm)
    editor = EditorAgent(llm)
    orchestrator = OrchestratorAgent(llm, writer_pipeline, reviewer, editor)

    result_data = await orchestrator.produce_high_quality_chapter(chapter.project, chapter)

    await db.commit()

    return result_data

@app.post("/projects/{project_id}/consistency")
async def analyze_consistency(project_id: int, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return {"error": "Project not found"}

    result = await db.execute(select(Chapter).where(Chapter.project_id == project_id))
    chapters = result.scalars().all()

    if not llm:
        return {"error": "LLM not configured"}

    agent = ConsistencyAgent(llm)
    analysis = await agent.analyze_book(project, chapters)

    return analysis

@app.post("/projects/{project_id}/book-plan")
async def produce_book_plan(project_id: int, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return {"error": "Project not found"}

    result = await db.execute(select(Chapter).where(Chapter.project_id == project_id))
    chapters = result.scalars().all()

    if not llm:
        return {"error": "LLM not configured"}

    consistency = ConsistencyAgent(llm)
    orchestrator = BookOrchestrator(consistency)

    plan = await orchestrator.produce_book_improvement_plan(project, chapters)

    return plan

@app.post("/projects/{project_id}/book-rewrite")
async def execute_book_rewrite(project_id: int, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return {"error": "Project not found"}

    result = await db.execute(select(Chapter).where(Chapter.project_id == project_id))
    chapters = result.scalars().all()

    if not llm:
        return {"error": "LLM not configured"}

    consistency = ConsistencyAgent(llm)
    book_orchestrator = BookOrchestrator(consistency)
    plan = await book_orchestrator.produce_book_improvement_plan(project, chapters)

    writer_pipeline = WriterPipeline(llm)
    reviewer = ReviewAgent(llm)
    editor = EditorAgent(llm)
    chapter_orchestrator = OrchestratorAgent(llm, writer_pipeline, reviewer, editor)

    rewrite_orchestrator = BookRewriteOrchestrator(chapter_orchestrator)
    result_data = await rewrite_orchestrator.execute_plan(project, chapters, plan)

    await db.commit()

    return result_data

@app.post("/projects/{project_id}/generate-outline")
async def generate_outline(project_id: int, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    import json

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return {"error": "Project not found"}

    if not llm:
        return {"error": "LLM not configured"}

    prompt = f"""
Create a structured book outline for a book titled '{project.title}'.

Return ONLY valid JSON in the following format:
[
  {{
    "title": "Chapter title",
    "summary": "Short 2-3 sentence summary",
    "goals": ["Goal 1", "Goal 2"]
  }}
]
"""

    temperature = float(project.temperature) if project.temperature else None
    max_tokens = int(project.max_tokens) if project.max_tokens else None

    pipeline = WriterPipeline(llm)
    outline_text = await pipeline.generate_outline(project)

    try:
        outline_data = json.loads(outline_text)
    except Exception:
        return {"error": "Model did not return valid JSON", "raw": outline_text}

    for item in outline_data:
        title = item.get("title")
        summary = item.get("summary")

        chapter = Chapter(
            project_id=project_id,
            title=title,
            content=summary
        )
        db.add(chapter)

    await db.commit()

    return {"status": "structured outline generated"}

@app.get("/projects/{project_id}/export/epub")
async def export_epub(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return {"error": "Project not found"}

    result = await db.execute(select(Chapter).where(Chapter.project_id == project_id))
    chapters = result.scalars().all()

    exporter = EPUBExporter()
    file_path = exporter.export_project(project, chapters)

    return FileResponse(file_path, media_type="application/epub+zip", filename=f"{project.title}.epub")

@app.get("/projects/{project_id}/export/pdf")
async def export_pdf(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return {"error": "Project not found"}

    result = await db.execute(select(Chapter).where(Chapter.project_id == project_id))
    chapters = result.scalars().all()

    exporter = PDFExporter()
    file_path = exporter.export_project(project, chapters)

    return FileResponse(file_path, media_type="application/pdf", filename=f"{project.title}.pdf")

@app.get("/projects/{project_id}/export/docx")
async def export_docx(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return {"error": "Project not found"}

    result = await db.execute(select(Chapter).where(Chapter.project_id == project_id))
    chapters = result.scalars().all()

    exporter = DOCXExporter()
    file_path = exporter.export_project(project, chapters)

    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=f"{project.title}.docx")
