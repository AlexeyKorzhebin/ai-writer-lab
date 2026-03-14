import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app, get_llm


class MockLLMValidJSON:
    async def generate(self, prompt: str):
        return '''[
            {"title": "Chapter 1", "summary": "Intro summary", "goals": ["Goal A"]},
            {"title": "Chapter 2", "summary": "Second summary", "goals": ["Goal B"]}
        ]'''


class MockLLMInvalidJSON:
    async def generate(self, prompt: str):
        return "Not a JSON response"


@pytest.mark.asyncio
async def test_generate_outline_valid_json():
    app.dependency_overrides[get_llm] = lambda: MockLLMValidJSON()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        project_resp = await ac.post("/projects", json={
            "title": "Outline Test",
            "description": "Test",
            "model_name": None
        })
        project_id = project_resp.json()["id"]

        resp = await ac.post(f"/projects/{project_id}/generate-outline")
        assert resp.status_code == 200
        assert resp.json().get("status") == "structured outline generated"

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_generate_outline_invalid_json():
    app.dependency_overrides[get_llm] = lambda: MockLLMInvalidJSON()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        project_resp = await ac.post("/projects", json={
            "title": "Outline Fail",
            "description": "Test",
            "model_name": None
        })
        project_id = project_resp.json()["id"]

        resp = await ac.post(f"/projects/{project_id}/generate-outline")
        assert resp.status_code == 200
        assert resp.json().get("error") == "Model did not return valid JSON"

    app.dependency_overrides = {}
