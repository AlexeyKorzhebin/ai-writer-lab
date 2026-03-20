from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import ChatSessionORM, ChatMessageORM


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_session(self, project_id: int, task_name: str = "Общий чат") -> ChatSessionORM:
        result = await self.db.execute(
            select(ChatSessionORM)
            .where(ChatSessionORM.project_id == project_id, ChatSessionORM.task_name == task_name)
            .options(selectinload(ChatSessionORM.messages))
            .order_by(ChatSessionORM.created_at.desc())
        )
        session = result.scalar_one_or_none()
        if not session:
            session = ChatSessionORM(project_id=project_id, task_name=task_name)
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
        return session

    async def list_sessions(self, project_id: int) -> list[ChatSessionORM]:
        result = await self.db.execute(
            select(ChatSessionORM)
            .where(ChatSessionORM.project_id == project_id)
            .order_by(ChatSessionORM.created_at.desc())
        )
        return list(result.scalars().all())

    async def add_message(self, session_id: int, role: str, content: str,
                          references: list | None = None, tokens: int = 0) -> ChatMessageORM:
        msg = ChatMessageORM(
            session_id=session_id,
            role=role,
            content=content,
            references=references,
            tokens=tokens,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_messages(self, session_id: int) -> list[ChatMessageORM]:
        result = await self.db.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at)
        )
        return list(result.scalars().all())

    async def create_new_task(self, project_id: int, task_name: str) -> ChatSessionORM:
        session = ChatSessionORM(project_id=project_id, task_name=task_name)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
