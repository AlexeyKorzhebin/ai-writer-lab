from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import Project
from app.routers.deps import templates

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    model_name: str | None = None
    temperature: str | None = None
    max_tokens: str | None = None
    author_name: str | None = None
    author_style: str | None = None


@router.post("")
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


@router.get("/{project_id}", response_class=HTMLResponse)
async def get_project(project_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.project_repository import ProjectRepository
    from app.infrastructure.repositories.chapter_repository import ChapterRepository

    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if not project:
        return HTMLResponse(content="Project not found", status_code=404)

    chapter_repo = ChapterRepository(db)
    chapters = await chapter_repo.list_by_project(project_id)

    return templates.TemplateResponse(
        "project.html",
        {"request": request, "project": project, "chapters": chapters},
    )


@router.post("/{project_id}/update-author")
async def update_author(project_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return {"error": "Project not found"}

    project.author_name = data.get("author_name")
    project.author_style = data.get("author_style")
    await db.commit()
    return {"status": "updated"}


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return {"error": "Project not found"}

    await db.delete(project)
    await db.commit()
    return {"status": "deleted"}
