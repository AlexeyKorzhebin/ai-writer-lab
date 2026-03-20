"""UI_UX_OVERVIEW, SCREENS_SPEC, UX_PATTERNS (статика/экраны), экспорт — см. SPEC_COVERAGE.md."""

import io
import zipfile

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

from .helpers import create_project, create_project_with_narrative_and_scenes


@pytest.mark.spec
@pytest.mark.asyncio
async def test_home_settings_and_static_assets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        h = await ac.get("/")
        assert h.status_code == 200

        s = await ac.get("/settings")
        assert s.status_code == 200

        css = await ac.get("/static/css/app.css")
        assert css.status_code == 200

        js = await ac.get("/static/js/app.js")
        assert js.status_code == 200
        assert "toast" in js.text.lower() or "Toast" in js.text or "theme" in js.text.lower()

        loc = await ac.get("/static/i18n/ru.json")
        assert loc.status_code == 200


@pytest.mark.spec
@pytest.mark.asyncio
async def test_project_screens_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pid = await create_project_with_narrative_and_scenes(ac, "screens")

        wizard = await ac.get(f"/projects/{pid}/story/wizard")
        assert wizard.status_code == 200

        workspace = await ac.get(f"/projects/{pid}/story/workspace")
        assert workspace.status_code == 200

        analytics = await ac.get(f"/projects/{pid}/analytics")
        assert analytics.status_code == 200


@pytest.mark.spec
@pytest.mark.asyncio
async def test_export_archive_contains_manifest():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pid = await create_project_with_narrative_and_scenes(ac, "archive zip")
        r = await ac.post(f"/projects/{pid}/export/archive")
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/zip")

        zf = zipfile.ZipFile(io.BytesIO(r.content))
        names = zf.namelist()
        assert "manifest.json" in names
        assert "project.json" in names
        mani = zf.read("manifest.json").decode("utf-8")
        assert "AI Writer Lab" in mani


@pytest.mark.spec
@pytest.mark.asyncio
async def test_export_formats_return_files():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pid = await create_project(ac, "export files")
        for path, substr in (
            (f"/projects/{pid}/export/epub", b"PK"),
            (f"/projects/{pid}/export/pdf", b"%PDF"),
        ):
            r = await ac.get(path)
            assert r.status_code == 200
            assert r.content.startswith(substr)

        docx = await ac.get(f"/projects/{pid}/export/docx")
        assert docx.status_code == 200
        assert docx.content.startswith(b"PK")
