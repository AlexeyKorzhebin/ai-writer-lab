from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Setting


class SettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, key: str, default: str | None = None) -> str | None:
        result = await self.db.execute(select(Setting).where(Setting.key == key))
        row = result.scalar_one_or_none()
        return row.value if row else default

    async def get_all(self) -> dict[str, str]:
        result = await self.db.execute(select(Setting))
        rows = result.scalars().all()
        return {r.key: r.value for r in rows}

    async def put(self, key: str, value: str, encrypted: bool = False) -> None:
        result = await self.db.execute(select(Setting).where(Setting.key == key))
        row = result.scalar_one_or_none()
        if row:
            row.value = value
            row.encrypted = encrypted
        else:
            self.db.add(Setting(key=key, value=value, encrypted=encrypted))
        await self.db.commit()

    async def put_many(self, data: dict[str, str]) -> None:
        for key, value in data.items():
            encrypted = key in ("api_key",)
            result = await self.db.execute(select(Setting).where(Setting.key == key))
            row = result.scalar_one_or_none()
            if row:
                row.value = value
                row.encrypted = encrypted
            else:
                self.db.add(Setting(key=key, value=value, encrypted=encrypted))
        await self.db.commit()

    async def delete(self, key: str) -> None:
        result = await self.db.execute(select(Setting).where(Setting.key == key))
        row = result.scalar_one_or_none()
        if row:
            await self.db.delete(row)
            await self.db.commit()
