import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_project():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/projects", json={
            "title": "Test Book",
            "description": "Testing project",
            "model_name": "just-ai/openai-proxy/gpt-5.2-chat-latest"
        })

    assert response.status_code == 200
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_get_project_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/projects/999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_outline_requires_project():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/projects/999999/generate-outline")

    assert response.status_code == 200
    data = response.json()
    assert data.get("error") == "Project not found"
