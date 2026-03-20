from __future__ import annotations

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import NarrativeSpecORM, CharacterORM, SceneORM
from app.domain.narrative import NarrativeSpec, CharacterSpec, SceneSpec
from app.infrastructure.narrative_mapper import (
    narrative_orm_to_domain,
    apply_domain_to_narrative_orm,
    domain_character_to_orm,
    domain_scene_to_orm,
)


class NarrativeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_project(self, project_id: int) -> NarrativeSpec | None:
        result = await self.db.execute(
            select(NarrativeSpecORM)
            .options(
                selectinload(NarrativeSpecORM.characters),
                selectinload(NarrativeSpecORM.scenes),
            )
            .where(NarrativeSpecORM.project_id == project_id)
        )
        orm = result.scalar_one_or_none()
        if not orm:
            return None
        return narrative_orm_to_domain(orm)

    async def save(self, spec: NarrativeSpec) -> NarrativeSpec:
        """Create or update the full NarrativeSpec for a project."""
        result = await self.db.execute(
            select(NarrativeSpecORM)
            .options(
                selectinload(NarrativeSpecORM.characters),
                selectinload(NarrativeSpecORM.scenes),
            )
            .where(NarrativeSpecORM.project_id == spec.project_id)
        )
        orm = result.scalar_one_or_none()

        if orm is None:
            orm = NarrativeSpecORM(project_id=spec.project_id)
            self.db.add(orm)

        apply_domain_to_narrative_orm(spec, orm)
        await self.db.flush()

        # Replace characters
        await self.db.execute(
            delete(CharacterORM).where(CharacterORM.narrative_spec_id == orm.id)
        )
        for ch in spec.characters:
            ch_orm = domain_character_to_orm(ch, orm.id)
            self.db.add(ch_orm)

        # Replace scenes
        await self.db.execute(
            delete(SceneORM).where(SceneORM.narrative_spec_id == orm.id)
        )
        for scene in spec.scenes:
            s_orm = domain_scene_to_orm(scene, orm.id)
            self.db.add(s_orm)

        await self.db.commit()

        return await self.get_by_project(spec.project_id)

    async def add_character(self, project_id: int, character: CharacterSpec) -> NarrativeSpec | None:
        spec = await self.get_by_project(project_id)
        if not spec:
            return None
        spec.characters.append(character)
        return await self.save(spec)

    async def update_scene_content(self, scene_id: int, content: str, summary: str | None = None) -> None:
        result = await self.db.execute(
            select(SceneORM).where(SceneORM.id == scene_id)
        )
        scene = result.scalar_one_or_none()
        if scene:
            scene.content = content
            if summary is not None:
                scene.summary = summary
            await self.db.commit()

    async def delete_for_project(self, project_id: int) -> None:
        result = await self.db.execute(
            select(NarrativeSpecORM).where(NarrativeSpecORM.project_id == project_id)
        )
        orm = result.scalar_one_or_none()
        if orm:
            await self.db.delete(orm)
            await self.db.commit()
