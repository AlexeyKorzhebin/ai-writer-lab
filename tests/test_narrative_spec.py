import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app, get_llm


class MockLLMOutline:
    async def generate(self, prompt: str, **kwargs):
        return '''[
            {"title": "Opening", "purpose": "Introduce the world", "participants": ["Hero"], "emotional_state": "curiosity"},
            {"title": "Conflict", "purpose": "Escalate tension", "participants": ["Hero", "Villain"], "emotional_state": "tension"},
            {"title": "Resolution", "purpose": "Resolve conflict", "participants": ["Hero"], "emotional_state": "relief"}
        ]'''


@pytest.mark.asyncio
async def test_create_narrative_spec():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        project_resp = await ac.post("/projects", json={
            "title": "Test Story",
            "description": "A test story",
        })
        project_id = project_resp.json()["id"]

        spec_data = {
            "core_idea": {
                "logline": "A hero saves the world",
                "genre": "fantasy",
                "tone": "Epic and hopeful",
                "themes": ["Courage", "Sacrifice"],
                "central_conflict": "Evil threatens the land",
                "story_format": "three_act",
            },
            "world": {
                "world_type": "fantasy",
                "rules": "Magic exists",
                "atmosphere": "Dark but hopeful",
            },
            "characters": [
                {
                    "name": "Hero",
                    "role": "protagonist",
                    "motivation": "Save the world",
                    "fear": "Losing loved ones",
                    "arc_start": "Ordinary farmer",
                    "arc_end": "Legendary warrior",
                },
            ],
            "structure": {
                "macro_structure": "three_act",
                "climax": "Final battle",
                "resolution": "Peace restored",
            },
        }

        resp = await ac.post(f"/projects/{project_id}/narrative-spec", json=spec_data)
        assert resp.status_code == 200
        assert resp.json()["status"] == "created"

        get_resp = await ac.get(f"/projects/{project_id}/narrative-spec")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["core_idea"]["logline"] == "A hero saves the world"
        assert len(data["characters"]) == 1
        assert data["characters"][0]["name"] == "Hero"


@pytest.mark.asyncio
async def test_update_narrative_spec():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        project_resp = await ac.post("/projects", json={"title": "Update Test"})
        project_id = project_resp.json()["id"]

        await ac.post(f"/projects/{project_id}/narrative-spec", json={
            "core_idea": {"logline": "Original logline", "story_format": "three_act"},
        })

        resp = await ac.put(f"/projects/{project_id}/narrative-spec", json={
            "core_idea": {"logline": "Updated logline"},
        })
        assert resp.status_code == 200
        assert resp.json()["version"] == 2


@pytest.mark.asyncio
async def test_generate_narrative_outline():
    app.dependency_overrides[get_llm] = lambda: MockLLMOutline()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        project_resp = await ac.post("/projects", json={"title": "Outline Test"})
        project_id = project_resp.json()["id"]

        await ac.post(f"/projects/{project_id}/narrative-spec", json={
            "core_idea": {
                "logline": "A quest for truth",
                "genre": "fantasy",
                "story_format": "three_act",
            },
            "characters": [{"name": "Hero", "role": "protagonist"}],
        })

        resp = await ac.post(f"/projects/{project_id}/narrative-spec/generate-outline")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "outline generated"
        assert data["scene_count"] == 3

    app.dependency_overrides.pop(get_llm, None)


@pytest.mark.asyncio
async def test_story_formats_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/story-formats")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 3
        keys = [f["key"] for f in data]
        assert "three_act" in keys
        assert "short_story" in keys
        assert "hero_journey" in keys
