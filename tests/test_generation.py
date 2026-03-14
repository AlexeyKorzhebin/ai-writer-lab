import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app, get_llm


class MockLLM:
    async def generate(self, prompt: str):
        return "Mocked content"


@pytest.mark.asyncio
async def test_generate_chapter_with_mock():
    app.dependency_overrides[get_llm] = lambda: MockLLM()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create project
        project_resp = await ac.post("/projects", json={
            "title": "Test Book",
            "description": "Test",
            "model_name": None
        })
        project_id = project_resp.json()["id"]

        # Create chapter
        chapter_resp = await ac.post(f"/projects/{project_id}/chapters", json={
            "title": "Chapter 1"
        })
        chapter_id = chapter_resp.json()["id"]

        # Generate chapter content
        gen_resp = await ac.post(f"/projects/{project_id}/generate-chapter/{chapter_id}")
        assert gen_resp.status_code == 200

    app.dependency_overrides = {}
