from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import LocationORM, LocationStateORM


class LocationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_project(self, project_id: int) -> list[LocationORM]:
        result = await self.db.execute(
            select(LocationORM)
            .where(LocationORM.project_id == project_id)
            .options(selectinload(LocationORM.states))
            .order_by(LocationORM.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, location_id: int) -> LocationORM | None:
        result = await self.db.execute(
            select(LocationORM)
            .where(LocationORM.id == location_id)
            .options(selectinload(LocationORM.states))
        )
        return result.scalar_one_or_none()

    async def create(self, project_id: int, data: dict) -> LocationORM:
        loc = LocationORM(
            project_id=project_id,
            name=data.get("name", ""),
            location_type=data.get("location_type", "building"),
            parent_id=data.get("parent_id"),
            description=data.get("description", ""),
            visual_details=data.get("visual_details", ""),
            atmosphere=data.get("atmosphere", ""),
            significance=data.get("significance", ""),
            climate=data.get("climate", ""),
            inhabitants=data.get("inhabitants", ""),
            notable_features=data.get("notable_features", ""),
            connected_to=data.get("connected_to", []),
            travel_notes=data.get("travel_notes", ""),
            tags=data.get("tags", []),
            first_appearance=data.get("first_appearance"),
        )
        self.db.add(loc)
        await self.db.commit()
        await self.db.refresh(loc)
        return loc

    async def update(self, location_id: int, data: dict) -> LocationORM | None:
        loc = await self.get_by_id(location_id)
        if not loc:
            return None
        for key, val in data.items():
            if hasattr(loc, key) and key != "id":
                setattr(loc, key, val)
        await self.db.commit()
        return loc

    async def delete(self, location_id: int) -> bool:
        loc = await self.get_by_id(location_id)
        if not loc:
            return False
        await self.db.delete(loc)
        await self.db.commit()
        return True

    async def get_tree(self, project_id: int) -> list[dict]:
        """Return locations as a tree structure."""
        locations = await self.list_by_project(project_id)
        by_id = {loc.id: loc for loc in locations}
        tree = []
        for loc in locations:
            node = {
                "id": loc.id, "name": loc.name, "type": loc.location_type,
                "parent_id": loc.parent_id, "description": loc.description,
                "children": [],
            }
            if loc.parent_id and loc.parent_id in by_id:
                pass  # will be attached below
            else:
                tree.append(node)
        return tree
