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
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()

    if not chapter:
        return {"error": "Chapter not found"}

    if not llm:
        chapter.content = "LLM not configured"
    else:
        prompt = f"Write a detailed book chapter titled '{chapter.title}'."

        temperature = float(chapter.project.temperature) if chapter.project.temperature else None
        max_tokens = int(chapter.project.max_tokens) if chapter.project.max_tokens else None

        content = await llm.generate(prompt=prompt)
        chapter.content = content

    await db.commit()
    return {"status": "ok"}

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

    outline_text = await llm.generate(prompt=prompt)

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
