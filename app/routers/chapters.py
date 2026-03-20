from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import Project, Chapter
from app.core.writer_pipeline import WriterPipeline
from app.core.agents.reviewer import ReviewAgent
from app.core.agents.editor import EditorAgent
from app.core.agents.orchestrator import OrchestratorAgent
from app.core.agents.consistency import ConsistencyAgent
from app.core.agents.book_orchestrator import BookOrchestrator
from app.core.agents.book_rewrite_orchestrator import BookRewriteOrchestrator
from app.routers.deps import templates, get_llm

router = APIRouter(prefix="/projects/{project_id}", tags=["chapters"])


@router.get("/chapters/{chapter_id}", response_class=HTMLResponse)
async def get_chapter(
    project_id: int,
    chapter_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
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
        {"request": request, "project": project, "chapter": chapter},
    )


@router.post("/chapters/{chapter_id}/update")
async def update_chapter(
    project_id: int, chapter_id: int, data: dict, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        return {"error": "Chapter not found"}

    chapter.content = data.get("content")
    await db.commit()
    return {"status": "saved"}


@router.post("/chapters")
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


@router.post("/generate-chapter/{chapter_id}")
async def generate_chapter(
    project_id: int,
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
    from app.infrastructure.repositories.chapter_repository import ChapterRepository
    from app.application.use_cases.generate_chapter import GenerateChapterUseCase

    chapter_repo = ChapterRepository(db)
    use_case = GenerateChapterUseCase(chapter_repo, llm, db_session=db)
    return await use_case.execute(chapter_id)


@router.post("/review/{chapter_id}")
async def review_chapter(
    project_id: int,
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
    from app.infrastructure.repositories.chapter_repository import ChapterRepository
    from app.application.use_cases.review_chapter import ReviewChapterUseCase

    chapter_repo = ChapterRepository(db)
    use_case = ReviewChapterUseCase(chapter_repo, llm)
    return await use_case.execute(chapter_id)


@router.post("/edit/{chapter_id}")
async def edit_chapter(
    project_id: int,
    chapter_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
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

    from app.infrastructure.repositories.chapter_repository import ChapterRepository

    chapter_repo = ChapterRepository(db)
    await chapter_repo.save_version(chapter)
    return {"status": "improved"}


@router.post("/produce-hq/{chapter_id}")
async def produce_high_quality(
    project_id: int,
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
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

    from app.infrastructure.repositories.chapter_repository import ChapterRepository

    chapter_repo = ChapterRepository(db)
    await chapter_repo.save_version(chapter)
    return result_data


@router.post("/consistency")
async def analyze_consistency(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return {"error": "Project not found"}

    result = await db.execute(select(Chapter).where(Chapter.project_id == project_id))
    chapters = result.scalars().all()
    if not llm:
        return {"error": "LLM not configured"}

    agent = ConsistencyAgent(llm)
    return await agent.analyze_book(project, chapters)


@router.post("/book-plan")
async def produce_book_plan(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
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
    return await orchestrator.produce_book_improvement_plan(project, chapters)


@router.post("/book-rewrite")
async def execute_book_rewrite(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
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


@router.post("/generate-outline")
async def generate_outline(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
    import json

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return {"error": "Project not found"}
    if not llm:
        return {"error": "LLM not configured"}

    pipeline = WriterPipeline(llm)
    outline_text = await pipeline.generate_outline(project)

    try:
        outline_data = json.loads(outline_text)
    except Exception:
        return {"error": "Model did not return valid JSON", "raw": outline_text}

    for item in outline_data:
        chapter = Chapter(
            project_id=project_id,
            title=item.get("title"),
            content=item.get("summary"),
        )
        db.add(chapter)
    await db.commit()
    return {"status": "structured outline generated"}


@router.get("/chapters/{chapter_id}/versions")
async def list_chapter_versions(
    project_id: int, chapter_id: int, db: AsyncSession = Depends(get_db)
):
    from app.infrastructure.repositories.chapter_repository import ChapterRepository

    chapter_repo = ChapterRepository(db)
    versions = await chapter_repo.list_versions(chapter_id)
    return [
        {
            "id": v.id,
            "version_number": v.version_number,
            "content_preview": (v.content or "")[:200],
            "summary": v.summary,
        }
        for v in versions
    ]


@router.post("/chapters/{chapter_id}/rollback/{version_number}")
async def rollback_chapter(
    project_id: int,
    chapter_id: int,
    version_number: int,
    db: AsyncSession = Depends(get_db),
):
    from app.infrastructure.repositories.chapter_repository import ChapterRepository

    chapter_repo = ChapterRepository(db)
    chapter = await chapter_repo.rollback_to_version(chapter_id, version_number)
    if not chapter:
        return {"error": "Version not found"}
    return {"status": "rolled back", "version_number": version_number}
