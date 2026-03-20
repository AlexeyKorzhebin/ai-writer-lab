from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.routers.deps import templates

router = APIRouter(tags=["home"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.project_repository import ProjectRepository

    project_repo = ProjectRepository(db)
    projects = await project_repo.list_all()

    return templates.TemplateResponse(
        "home.html",
        {"request": request, "projects": projects},
    )
