"""AI_CHAT_AND_CONTEXT (API), ILLUSTRATION_*, аналитика — см. SPEC_COVERAGE.md."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app, get_llm

from .helpers import create_project_with_narrative_and_scenes


class MockStreamLLM:
    async def generate(self, prompt: str, **kwargs):
        return "mock"

    async def stream_chat(self, messages):
        yield "фрагмент "
        yield "ответа"


@pytest.mark.spec
@pytest.mark.asyncio
async def test_chat_estimate_sessions_new_task():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pid = await create_project_with_narrative_and_scenes(ac, "chat estimate")

        est = await ac.post(
            f"/projects/{pid}/chat/estimate",
            json={"message": "@scene:0 что дальше?", "scene_idx": 0},
        )
        assert est.status_code == 200
        body = est.json()
        assert "used_tokens" in body
        assert body["max_tokens"] == 16000

        nt = await ac.post(
            f"/projects/{pid}/chat/new-task",
            json={"task_name": "Редактура главы"},
        )
        assert nt.status_code == 200
        assert nt.json().get("task_name") == "Редактура главы"

        sess = await ac.get(f"/projects/{pid}/chat/sessions")
        assert sess.status_code == 200
        assert len(sess.json()) >= 1

        msg = await ac.get(
            f"/projects/{pid}/chat/messages",
            params={"task_name": "Редактура главы"},
        )
        assert msg.status_code == 200
        assert msg.json() == []


@pytest.mark.spec
@pytest.mark.asyncio
async def test_chat_send_returns_sse():
    app.dependency_overrides[get_llm] = lambda: MockStreamLLM()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            pid = await create_project_with_narrative_and_scenes(ac, "chat sse")
            r = await ac.post(
                f"/projects/{pid}/chat/send",
                json={"message": "Короткий совет", "task_name": "Общий чат", "scene_idx": 0},
            )
            assert r.status_code == 200
            ct = r.headers.get("content-type", "")
            assert "text/event-stream" in ct
    finally:
        app.dependency_overrides.pop(get_llm, None)


@pytest.mark.spec
@pytest.mark.asyncio
async def test_illustration_templates_and_generation():
    class MockIll:
        async def generate(self, prompt: str, **kwargs):
            if "варианта визуальной" in prompt or "композиции" in prompt:
                return (
                    '[{"variant": "A", "composition": "center", "camera_angle": "low", '
                    '"lighting": "soft", "key_details": "x", "emotional_focus": "hope"}]'
                )
            return "Final English prompt for illustration with mood and setting."

    app.dependency_overrides[get_llm] = lambda: MockIll()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            tpl = await ac.get("/illustration-templates")
            assert tpl.status_code == 200
            templates = tpl.json()
            assert isinstance(templates, list)

            pid = await create_project_with_narrative_and_scenes(ac, "illus")

            v = await ac.post(f"/projects/{pid}/narrative-spec/illustration-variants/0")
            assert v.status_code == 200
            assert "variants" in v.json()

            p = await ac.post(
                f"/projects/{pid}/narrative-spec/illustration-prompt/0",
                json={"template": templates[0]["key"] if templates else "realistic_book", "description": ""},
            )
            assert p.status_code == 200
            assert "prompt" in p.json()
    finally:
        app.dependency_overrides.pop(get_llm, None)


@pytest.mark.spec
@pytest.mark.asyncio
async def test_analytics_data_json():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pid = await create_project_with_narrative_and_scenes(ac, "analytics")
        r = await ac.get(f"/projects/{pid}/analytics/data")
        assert r.status_code == 200
        data = r.json()
        assert "scenes" in data
        assert "characters" in data
        assert data["total_scenes"] >= 1
