"""SETTINGS_AND_CONFIG, AUTHOR_STYLE_PRESETS, WORLD_AND_LOCATIONS — см. SPEC_COVERAGE.md."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app, get_llm

from .helpers import (
    create_project_with_narrative,
    generate_locations_with_mock_llm,
    seed_outline_scenes,
)


@pytest.mark.spec
@pytest.mark.asyncio
async def test_settings_page_and_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        html = await ac.get("/settings")
        assert html.status_code == 200
        assert "settings" in html.text.lower() or "настрой" in html.text.lower()

        cur = await ac.get("/api/settings")
        assert cur.status_code == 200
        assert isinstance(cur.json(), dict)

        put = await ac.put("/api/settings", json={"model": "gpt-4o-mini"})
        assert put.status_code == 200
        assert put.json().get("status") == "saved"

        prov = await ac.get("/api/settings/providers")
        assert prov.status_code == 200
        assert isinstance(prov.json(), list)
        assert len(prov.json()) >= 1

        models = await ac.get("/api/settings/models/caila")
        assert models.status_code == 200
        assert "models" in models.json()

        no_url = await ac.post("/api/settings/test-connection", json={})
        assert no_url.status_code == 200
        assert no_url.json().get("success") is False


@pytest.mark.spec
@pytest.mark.asyncio
async def test_author_presets_list_and_sample():
    class Mock:
        async def generate(self, prompt: str, **kwargs):
            return "Образец текста в заданном стиле."

    app.dependency_overrides[get_llm] = lambda: Mock()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/author-presets")
            assert r.status_code == 200
            presets = r.json()
            assert isinstance(presets, list)
            if presets:
                assert "name" in presets[0] or "key" in presets[0] or "id" in presets[0]

            gen = await ac.post(
                "/author-presets/generate-sample",
                json={"style_prompt": "лаконичный стиль", "logline": "про героя"},
            )
            assert gen.status_code == 200
            assert "sample" in gen.json()
            assert len(gen.json()["sample"]) > 0
    finally:
        app.dependency_overrides.pop(get_llm, None)


@pytest.mark.spec
@pytest.mark.asyncio
async def test_world_presets_and_import_preset():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        lst = await ac.get("/world-presets")
        assert lst.status_code == 200
        presets = lst.json()
        assert isinstance(presets, list)
        assert len(presets) >= 1
        key = presets[0].get("key")
        assert key

        one = await ac.get(f"/world-presets/{key}")
        assert one.status_code == 200
        assert one.json().get("key") == key or "name" in one.json()

        pid = await create_project_with_narrative(ac, "world import")
        imp = await ac.post(
            f"/projects/{pid}/world/import",
            json={"type": "preset", "preset_key": key},
        )
        assert imp.status_code == 200
        body = imp.json()
        assert "world" in body or "locations" in body


@pytest.mark.spec
@pytest.mark.asyncio
async def test_locations_crud_and_generate():
    class MockLoc:
        async def generate(self, prompt: str, **kwargs):
            return (
                '[{"name": "Лес", "location_type": "natural", '
                '"description": "тёмный лес", "atmosphere": "мгла", '
                '"significance": "завязка"}]'
            )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pid = await create_project_with_narrative(ac, "locations gen")
        await generate_locations_with_mock_llm(ac, pid, MockLoc())

        locs = await ac.get(f"/projects/{pid}/locations")
        assert locs.status_code == 200
        assert len(locs.json()) >= 1
        first_id = locs.json()[0]["id"]

        upd = await ac.put(
            f"/projects/{pid}/locations/{first_id}",
            json={"description": "обновлённое описание"},
        )
        assert upd.status_code == 200

        new_loc = await ac.post(
            f"/projects/{pid}/locations",
            json={
                "name": "Ручей",
                "location_type": "natural",
                "description": "мелкий ручей",
            },
        )
        assert new_loc.status_code == 200
        new_id = new_loc.json()["id"]

        deleted = await ac.delete(f"/projects/{pid}/locations/{new_id}")
        assert deleted.status_code == 200


@pytest.mark.spec
@pytest.mark.asyncio
async def test_expand_location_with_mock():
    class MockExpand:
        async def generate(self, prompt: str, **kwargs):
            return (
                '{"visual_details": "мох", "atmosphere": "сыро", '
                '"significance": "важно", "climate": "умеренный", '
                '"inhabitants": "птицы", "notable_features": "камни"}'
            )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pid = await create_project_with_narrative(ac, "expand loc")
        await ac.post(
            f"/projects/{pid}/locations",
            json={"name": "Пещера", "location_type": "natural", "description": "темно"},
        )
        locs = await ac.get(f"/projects/{pid}/locations")
        lid = locs.json()[0]["id"]

        app.dependency_overrides[get_llm] = lambda: MockExpand()
        try:
            r = await ac.post(f"/projects/{pid}/locations/{lid}/expand")
            assert r.status_code == 200
            assert r.json().get("status") == "expanded"
        finally:
            app.dependency_overrides.pop(get_llm, None)


@pytest.mark.spec
@pytest.mark.asyncio
async def test_generate_locations_requires_llm_or_returns_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pid = await create_project_with_narrative(ac, "no llm loc")
        await seed_outline_scenes(ac, pid)
        app.dependency_overrides[get_llm] = lambda: None
        try:
            r = await ac.post(f"/projects/{pid}/narrative-spec/generate-locations")
            assert r.status_code == 200
            assert "error" in r.json()
        finally:
            app.dependency_overrides.pop(get_llm, None)
