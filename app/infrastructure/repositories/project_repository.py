from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Project
from app.domain.entities import ProjectEntity
from app.infrastructure.mappers import project_to_entity


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, project_id: int) -> Project | None:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_entity(self, project_id: int) -> ProjectEntity | None:
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.chapters))
            .where(Project.id == project_id)
        )
        orm = result.scalar_one_or_none()
        if not orm:
            return None
        return project_to_entity(orm)

    async def list_all(self) -> list[Project]:
        result = await self.db.execute(select(Project))
        return result.scalars().all()

    async def save(self, project: Project) -> None:
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
