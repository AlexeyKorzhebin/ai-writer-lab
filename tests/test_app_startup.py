"""Smoke tests: app imports, ORM mapping, critical HTTP routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_llm


def test_get_llm_exported_for_dependency_overrides():
    """Tests and routers must share the same get_llm object."""
    from app.routers.deps import get_llm as deps_get_llm

    assert get_llm is deps_get_llm


@pytest.mark.asyncio
async def test_orm_configures_without_error():
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.core.models import Project

    async with AsyncSessionLocal() as session:
        await session.execute(select(Project).limit(1))


@pytest.mark.parametrize("path,expected", [("/", 200), ("/settings", 200), ("/static/css/app.css", 200)])
def test_public_routes(path, expected):
    client = TestClient(app)
    response = client.get(path)
    assert response.status_code == expected, response.text[:500]
