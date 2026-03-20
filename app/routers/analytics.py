from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import Project
from app.routers.deps import templates, get_llm

router = APIRouter(tags=["analytics"])


@router.get("/projects/{project_id}/analytics", response_class=HTMLResponse)
async def analytics_page(
    project_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    from app.infrastructure.repositories.project_repository import ProjectRepository
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository

    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if not project:
        return HTMLResponse(content="Project not found", status_code=404)

    narrative_repo = NarrativeRepository(db)
    spec = await narrative_repo.get_by_project(project_id)

    scenes = spec.scenes if spec else []
    total_words = sum(
        len((s.content or "").split()) for s in scenes
    )
    scenes_with_content = sum(1 for s in scenes if s.content)
    characters_count = len(spec.characters) if spec else 0

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "project": project,
            "spec": spec,
            "total_scenes": len(scenes),
            "scenes_with_content": scenes_with_content,
            "total_words": total_words,
            "characters_count": characters_count,
        },
    )


@router.get("/projects/{project_id}/analytics/data")
async def analytics_data(project_id: int, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository

    narrative_repo = NarrativeRepository(db)
    spec = await narrative_repo.get_by_project(project_id)
    if not spec:
        return {"error": "NarrativeSpec not found"}

    scene_data = []
    for i, s in enumerate(spec.scenes):
        words = len((s.content or "").split()) if s.content else 0
        scene_data.append({
            "index": i,
            "title": s.title,
            "words": words,
            "emotional_state": s.emotional_state or "",
            "has_content": bool(s.content),
            "participants": s.participants or [],
        })

    character_data = []
    for c in spec.characters:
        appearances = sum(
            1 for s in spec.scenes
            if s.participants and c.name in s.participants
        )
        character_data.append({
            "name": c.name,
            "role": c.role.value if hasattr(c.role, 'value') else str(c.role),
            "appearances": appearances,
        })

    return {
        "scenes": scene_data,
        "characters": character_data,
        "total_words": sum(s["words"] for s in scene_data),
        "total_scenes": len(scene_data),
        "scenes_with_content": sum(1 for s in scene_data if s["has_content"]),
    }
