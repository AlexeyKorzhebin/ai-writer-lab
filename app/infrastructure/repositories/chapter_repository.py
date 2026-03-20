from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Chapter, Project, ChapterVersion
from app.domain.entities import ChapterEntity
from app.infrastructure.mappers import chapter_to_entity


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

    async def get_entity(self, chapter_id: int) -> ChapterEntity | None:
        orm = await self.get_with_project(chapter_id)
        if not orm:
            return None
        return chapter_to_entity(orm)

    async def list_by_project(self, project_id: int) -> list[Chapter]:
        result = await self.db.execute(
            select(Chapter)
            .where(Chapter.project_id == project_id)
            .order_by(Chapter.id)
        )
        return result.scalars().all()

    async def save(self, chapter: Chapter) -> None:
        self.db.add(chapter)
        await self.db.commit()
        await self.db.refresh(chapter)

    async def save_version(self, chapter: Chapter) -> None:
        """Save current chapter state as a new version."""
        result = await self.db.execute(
            select(ChapterVersion)
            .where(ChapterVersion.chapter_id == chapter.id)
            .order_by(ChapterVersion.version_number.desc())
            .limit(1)
        )
        last_version = result.scalar_one_or_none()
        next_num = (last_version.version_number + 1) if last_version else 1

        version = ChapterVersion(
            chapter_id=chapter.id,
            content=chapter.content,
            summary=chapter.summary,
            version_number=next_num,
        )
        self.db.add(version)
        await self.db.commit()

    async def list_versions(self, chapter_id: int) -> list[ChapterVersion]:
        result = await self.db.execute(
            select(ChapterVersion)
            .where(ChapterVersion.chapter_id == chapter_id)
            .order_by(ChapterVersion.version_number.desc())
        )
        return result.scalars().all()

    async def rollback_to_version(self, chapter_id: int, version_number: int) -> Chapter | None:
        result = await self.db.execute(
            select(ChapterVersion)
            .where(
                ChapterVersion.chapter_id == chapter_id,
                ChapterVersion.version_number == version_number,
            )
        )
        version = result.scalar_one_or_none()
        if not version:
            return None

        ch_result = await self.db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = ch_result.scalar_one_or_none()
        if not chapter:
            return None

        chapter.content = version.content
        chapter.summary = version.summary
        await self.db.commit()
        await self.db.refresh(chapter)
        return chapter
