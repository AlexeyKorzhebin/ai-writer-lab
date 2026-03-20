import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app, get_llm


class MockLLM:
    async def generate(self, prompt: str, **kwargs):
        return "Generated chapter content"


@pytest.mark.asyncio
async def test_chapter_versioning():
    app.dependency_overrides[get_llm] = lambda: MockLLM()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        project_resp = await ac.post("/projects", json={
            "title": "Version Test",
            "description": "Test versioning",
        })
        project_id = project_resp.json()["id"]

        chapter_resp = await ac.post(f"/projects/{project_id}/chapters", json={
            "title": "Chapter 1"
        })
        chapter_id = chapter_resp.json()["id"]

        gen_resp = await ac.post(f"/projects/{project_id}/generate-chapter/{chapter_id}")
        assert gen_resp.status_code == 200

        versions_resp = await ac.get(f"/projects/{project_id}/chapters/{chapter_id}/versions")
        assert versions_resp.status_code == 200
        versions = versions_resp.json()
        assert len(versions) >= 1
        assert versions[0]["version_number"] == 1

    app.dependency_overrides.pop(get_llm, None)


@pytest.mark.asyncio
async def test_chapter_rollback():
    app.dependency_overrides[get_llm] = lambda: MockLLM()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        project_resp = await ac.post("/projects", json={"title": "Rollback Test"})
        project_id = project_resp.json()["id"]

        chapter_resp = await ac.post(f"/projects/{project_id}/chapters", json={"title": "Ch1"})
        chapter_id = chapter_resp.json()["id"]

        await ac.post(f"/projects/{project_id}/generate-chapter/{chapter_id}")

        rollback_resp = await ac.post(
            f"/projects/{project_id}/chapters/{chapter_id}/rollback/1"
        )
        assert rollback_resp.status_code == 200
        assert rollback_resp.json()["status"] == "rolled back"

        bad_rollback = await ac.post(
            f"/projects/{project_id}/chapters/{chapter_id}/rollback/999"
        )
        assert bad_rollback.json()["error"] == "Version not found"

    app.dependency_overrides.pop(get_llm, None)
