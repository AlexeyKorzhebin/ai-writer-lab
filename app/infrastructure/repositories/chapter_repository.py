from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Chapter, Project


class ChapterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_with_project(self, chapter_id: int) -> Chapter | None:
        result = await self.db.execute(
            select(Chapter)
            .options(
                selectinload(Chapter.project)
                .selectinload(Project.chapters)
            )
            .where(Chapter.id == chapter_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: int) -> list[Chapter]:
        result = await self.db.execute(
            select(Chapter).where(Chapter.project_id == project_id)
        )
        return result.scalars().all()

    async def save(self, chapter: Chapter) -> None:
        self.db.add(chapter)
        await self.db.commit()
        await self.db.refresh(chapter)
