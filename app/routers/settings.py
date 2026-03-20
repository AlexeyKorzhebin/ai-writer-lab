import os

import httpx
import yaml
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.routers.deps import templates

router = APIRouter(tags=["settings"])

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _load_providers():
    path = os.path.join(_DATA_DIR, "providers.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f).get("providers", [])


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    current = await repo.get_all()
    providers = _load_providers()

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "settings": current,
            "providers": providers,
        },
    )


@router.get("/api/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    current = await repo.get_all()
    if "api_key" in current and current["api_key"]:
        current["api_key"] = current["api_key"][:8] + "••••••••"
    return current


@router.put("/api/settings")
async def update_settings(data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    clean = {k: v for k, v in data.items() if v is not None}
    if "api_key" in clean and "••••" in clean["api_key"]:
        del clean["api_key"]
    await repo.put_many(clean)
    return {"status": "saved"}


@router.get("/api/settings/providers")
async def list_providers():
    return _load_providers()


@router.get("/api/settings/models/{provider_key}")
async def list_models(provider_key: str):
    providers = _load_providers()
    for p in providers:
        if p["key"] == provider_key:
            return {"models": p.get("models", [])}
    return {"models": []}


@router.post("/api/settings/test-connection")
async def test_connection(data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    base_url = data.get("base_url") or await repo.get("base_url", "")
    api_key = data.get("api_key") or await repo.get("api_key", "")
    model = data.get("model") or await repo.get("model", "")

    if not base_url:
        return {"success": False, "error": "Base URL не указан"}

    headers = {"Content-Type": "application/json"}
    if api_key and "••••" not in api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model or "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Say hi"}],
        "max_tokens": 5,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
        return {"success": True, "message": "Подключение успешно!"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)[:300]}
