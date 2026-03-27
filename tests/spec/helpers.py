"""Общие фикстуры данных для спек-тестов."""

import json

from app.main import app, get_llm

NARRATIVE_SPEC_MINIMAL = {
    "core_idea": {
        "logline": "Тестовая история",
        "genre": "fantasy",
        "tone": "ироничный",
        "themes": ["дружба"],
        "central_conflict": "конфликт",
        "story_format": "three_act",
    },
    "world": {
        "world_type": "fantasy",
        "rules": "магия редка",
        "time_period": "средневековье",
        "atmosphere": "мрачно",
    },
    "characters": [
        {
            "name": "Герой",
            "role": "protagonist",
            "motivation": "победить",
            "fear": "проиграть",
        },
    ],
    "structure": {
        "macro_structure": "three_act",
        "climax": "битва",
        "resolution": "финал",
    },
}


async def create_project(ac, title: str = "Spec test project") -> int:
    r = await ac.post("/projects", json={"title": title, "description": "from spec tests"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


async def create_project_with_narrative(ac, title: str = "With narrative") -> int:
    pid = await create_project(ac, title)
    r = await ac.post(f"/projects/{pid}/narrative-spec", json=NARRATIVE_SPEC_MINIMAL)
    assert r.status_code == 200, r.text
    return pid


async def seed_outline_scenes(ac, project_id: int, *, scene_titles: list[str] | None = None) -> dict:
    """CreateNarrativeSpec не сохраняет scenes из JSON — заполняем через generate-outline с mock LLM."""
    if scene_titles is None:
        scene_titles = ["Сцена 1"]

    outline = [
        {
            "title": t,
            "purpose": "завязка",
            "participants": ["Герой"],
            "emotional_state": "напряжение",
        }
        for t in scene_titles
    ]
    payload = json.dumps(outline, ensure_ascii=False)

    class _Mock:
        async def generate(self, prompt: str, **kwargs):
            return payload

    prev = app.dependency_overrides.get(get_llm)
    app.dependency_overrides[get_llm] = lambda: _Mock()
    try:
        r = await ac.post(f"/projects/{project_id}/narrative-spec/generate-outline")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("status") == "outline generated"
        return data
    finally:
        if prev is not None:
            app.dependency_overrides[get_llm] = prev
        else:
            app.dependency_overrides.pop(get_llm, None)


async def create_project_with_narrative_and_scenes(ac, title: str = "With scenes") -> int:
    pid = await create_project_with_narrative(ac, title)
    await seed_outline_scenes(ac, pid)
    return pid


async def generate_locations_with_mock_llm(ac, project_id: int, mock_llm_instance) -> dict:
    """POST generate-locations с подменённым LLM (возвращает JSON-массив локаций)."""
    prev = app.dependency_overrides.get(get_llm)
    app.dependency_overrides[get_llm] = lambda: mock_llm_instance
    try:
        r = await ac.post(f"/projects/{project_id}/narrative-spec/generate-locations")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "locations" in data and len(data["locations"]) >= 1
        return data
    finally:
        if prev is not None:
            app.dependency_overrides[get_llm] = prev
        else:
            app.dependency_overrides.pop(get_llm, None)
