import json
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.core.context_builder import ContextBuilder, parse_references, resolve_reference, estimate_tokens
from app.routers.deps import get_llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["chat"])


async def _get_spec(project_id: int, db: AsyncSession):
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository
    repo = NarrativeRepository(db)
    return await repo.get_by_project(project_id)


@router.post("/send")
async def chat_send(
    project_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
    if not llm:
        return {"error": "LLM not configured"}

    from app.infrastructure.repositories.chat_repository import ChatRepository
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    chat_repo = ChatRepository(db)
    settings_repo = SettingsRepository(db)

    message = data.get("message", "")
    task_name = data.get("task_name", "Общий чат")
    scene_idx = data.get("scene_idx", -1)

    session = await chat_repo.get_or_create_session(project_id, task_name)
    spec = await _get_spec(project_id, db)

    author_style = await settings_repo.get("author_style", "")
    ctx = ContextBuilder(max_tokens=16000)
    ctx.add_system_prompt(author_style=author_style)
    ctx.add_auto_context(spec, scene_idx)

    refs = parse_references(message)
    for ref_type, key in refs:
        content = resolve_reference(ref_type, key, spec)
        if content:
            ctx.add_reference(ref_type, key, content)

    existing_msgs = await chat_repo.get_messages(session.id)
    history = [{"role": m.role, "content": m.content} for m in existing_msgs[-20:]]
    if history:
        ctx.add_history(history)

    ctx.add_user_message(message)
    llm_messages = ctx.build_messages()

    await chat_repo.add_message(session.id, "user", message,
                                references=[{"type": rt, "key": k} for rt, k in refs],
                                tokens=estimate_tokens(message))

    async def event_generator():
        full_response = ""
        try:
            async for chunk in llm.stream_chat(llm_messages):
                full_response += chunk
                yield {"event": "chunk", "data": json.dumps({"content": chunk})}
        except Exception as e:
            logger.exception("SSE stream error")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            return

        await chat_repo.add_message(session.id, "assistant", full_response,
                                    tokens=estimate_tokens(full_response))
        yield {"event": "done", "data": json.dumps({"full_content": full_response})}

    return EventSourceResponse(event_generator())


@router.get("/sessions")
async def list_sessions(project_id: int, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.chat_repository import ChatRepository

    repo = ChatRepository(db)
    sessions = await repo.list_sessions(project_id)
    return [
        {
            "id": s.id,
            "task_name": s.task_name,
            "created_at": str(s.created_at) if s.created_at else None,
        }
        for s in sessions
    ]


@router.get("/messages")
async def get_messages(project_id: int, task_name: str = "Общий чат", db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.chat_repository import ChatRepository

    repo = ChatRepository(db)
    session = await repo.get_or_create_session(project_id, task_name)
    messages = await repo.get_messages(session.id)
    return [
        {
            "role": m.role,
            "content": m.content,
            "references": m.references,
            "created_at": str(m.created_at) if m.created_at else None,
        }
        for m in messages
    ]


@router.post("/new-task")
async def new_task(project_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.chat_repository import ChatRepository

    repo = ChatRepository(db)
    task_name = data.get("task_name", "Новая задача")
    session = await repo.create_new_task(project_id, task_name)
    return {"session_id": session.id, "task_name": session.task_name}


@router.post("/estimate")
async def estimate_tokens_endpoint(
    project_id: int, data: dict, db: AsyncSession = Depends(get_db)
):
    message = data.get("message", "")
    scene_idx = data.get("scene_idx", -1)
    spec = await _get_spec(project_id, db)

    ctx = ContextBuilder(max_tokens=16000)
    ctx.add_system_prompt()
    ctx.add_auto_context(spec, scene_idx)

    refs = parse_references(message)
    for ref_type, key in refs:
        content = resolve_reference(ref_type, key, spec)
        if content:
            ctx.add_reference(ref_type, key, content)

    ctx.add_user_message(message)
    return ctx.get_budget_info()
