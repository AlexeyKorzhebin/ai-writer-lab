import json
import os

import httpx
import yaml
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.routers.deps import templates
from app.services import llm_providers as lp

router = APIRouter(tags=["settings"])

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _load_builtin_providers():
    path = os.path.join(_DATA_DIR, "providers.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f).get("providers", [])


def _prepare_settings_response(raw: dict[str, str]) -> dict:
    """Маскирует api_key и вложенные ключи в JSON-настройках."""
    out = dict(raw)
    if "api_key" in out and out["api_key"]:
        out["api_key"] = lp.mask_api_key(out["api_key"])
    if "user_providers" in out and out["user_providers"]:
        try:
            arr = json.loads(out["user_providers"])
            out["user_providers"] = [lp.mask_user_provider(p) for p in arr if isinstance(p, dict)]
        except json.JSONDecodeError:
            out["user_providers"] = []
    else:
        out["user_providers"] = []
    if "llm_profiles" in out and out["llm_profiles"]:
        try:
            arr = json.loads(out["llm_profiles"])
            out["llm_profiles"] = [lp.mask_profile(p) for p in arr if isinstance(p, dict)]
        except json.JSONDecodeError:
            out["llm_profiles"] = []
    else:
        out["llm_profiles"] = []
    out["active_profile_id"] = out.get("active_profile_id") or ""
    if "llm_extra_headers" in out and out["llm_extra_headers"]:
        out["llm_extra_headers"] = lp.mask_extra_headers_json(out["llm_extra_headers"])
    else:
        out["llm_extra_headers"] = out.get("llm_extra_headers") or "{}"
    return out


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    current = await repo.get_all()
    builtin = _load_builtin_providers()
    user_list = await lp.ensure_user_providers_migrated(repo, builtin)
    providers = lp.merge_providers_for_api(builtin, user_list)
    settings_for_template = _prepare_settings_response(current)

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "settings": settings_for_template,
            "providers": providers,
        },
    )


@router.get("/api/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    current = await repo.get_all()
    return _prepare_settings_response(current)


@router.put("/api/settings")
async def update_settings(data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    skip = {"user_providers", "llm_profiles"}
    clean = {k: v for k, v in data.items() if v is not None and k not in skip}
    if "api_key" in clean and lp.is_masked_api_key(clean["api_key"]):
        del clean["api_key"]
    if "base_url" in clean and not str(clean["base_url"]).strip():
        del clean["base_url"]
    if "api_key" in clean and not str(clean["api_key"]).strip():
        del clean["api_key"]

    if "llm_extra_headers" in clean:
        raw_in = clean["llm_extra_headers"]
        if isinstance(raw_in, dict):
            raw_in = json.dumps(raw_in, ensure_ascii=False)
        elif raw_in is not None:
            raw_in = str(raw_in)
        else:
            raw_in = "{}"
        try:
            json.loads(raw_in)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Дополнительные заголовки: невалидный JSON",
            ) from None
        clean["llm_extra_headers"] = lp.merge_extra_headers_json(
            raw_in,
            await repo.get("llm_extra_headers", ""),
        )

    touches_connection = bool(
        {"provider", "base_url", "api_key"} & clean.keys()
    )
    if touches_connection:
        prov_key = (clean.get("provider") or await repo.get("provider", "") or "").strip()
        builtin = _load_builtin_providers()
        user_list = await lp.ensure_user_providers_migrated(repo, builtin)
        if prov_key and "api_key" not in clean:
            for p in user_list:
                if p.get("key") == prov_key and p.get("api_key"):
                    clean["api_key"] = p["api_key"]
                    break
        merged_base = (clean.get("base_url") or await repo.get("base_url", "") or "").strip()
        merged_key = (clean.get("api_key") or await repo.get("api_key", "") or "").strip()
        if not merged_base:
            raise HTTPException(status_code=400, detail="Поле base_url обязательно")
        if not merged_key or lp.is_masked_api_key(merged_key):
            raise HTTPException(
                status_code=400,
                detail="Поле api_key обязательно (введите ключ целиком, если видите маску)",
            )
    await repo.put_many(clean)
    return {"status": "saved"}


@router.get("/api/settings/providers")
async def list_providers(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    builtin = _load_builtin_providers()
    user_list = await lp.ensure_user_providers_migrated(repo, builtin)
    return lp.merge_providers_for_api(builtin, user_list)


@router.post("/api/settings/user-providers")
async def create_user_provider(data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    name = (data.get("name") or "").strip()
    base_url = (data.get("base_url") or "").strip()
    api_key = (data.get("api_key") or "").strip()
    if not name or not base_url:
        raise HTTPException(status_code=400, detail="Обязательны поля name и base_url")
    if api_key and lp.is_masked_api_key(api_key):
        raise HTTPException(status_code=400, detail="Некорректный api_key")

    repo = SettingsRepository(db)
    builtin = _load_builtin_providers()
    user_list = await lp.ensure_user_providers_migrated(repo, builtin)
    keys = {p["key"] for p in user_list if p.get("key")}
    key = (data.get("key") or "").strip() or lp.slug_key(name, keys)
    if key in keys:
        raise HTTPException(status_code=400, detail="Провайдер с таким key уже есть")
    user_list.append(
        {
            "id": lp.new_id(),
            "key": key,
            "name": name,
            "base_url": base_url.rstrip("/"),
            "api_key": api_key,
            "models": [],
        }
    )
    await lp.save_user_providers(repo, user_list)
    return lp.mask_user_provider(user_list[-1])


@router.put("/api/settings/user-providers/{provider_id}")
async def update_user_provider(provider_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    builtin = _load_builtin_providers()
    user_list = await lp.ensure_user_providers_migrated(repo, builtin)
    found = None
    for i, p in enumerate(user_list):
        if p.get("id") == provider_id or p.get("key") == provider_id:
            found = i
            break
    if found is None:
        raise HTTPException(status_code=404, detail="Провайдер не найден")

    p = user_list[found]
    if "name" in data and data["name"] is not None:
        p["name"] = str(data["name"]).strip()
    if "base_url" in data and data["base_url"] is not None:
        p["base_url"] = str(data["base_url"]).strip().rstrip("/")
    if "key" in data and data["key"] is not None:
        nk = str(data["key"]).strip()
        if nk and nk != p["key"]:
            others = {x["key"] for j, x in enumerate(user_list) if j != found}
            if nk in others:
                raise HTTPException(status_code=400, detail="Провайдер с таким key уже есть")
            p["key"] = nk
    if "api_key" in data and data["api_key"] is not None:
        ak = str(data["api_key"]).strip()
        if ak and not lp.is_masked_api_key(ak):
            p["api_key"] = ak

    if not (p.get("name") and p.get("base_url")):
        raise HTTPException(status_code=400, detail="Обязательны name и base_url")

    await lp.save_user_providers(repo, user_list)
    return lp.mask_user_provider(p)


@router.delete("/api/settings/user-providers/{provider_id}")
async def delete_user_provider(provider_id: str, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    builtin = _load_builtin_providers()
    user_list = await lp.ensure_user_providers_migrated(repo, builtin)
    new_list = [p for p in user_list if p.get("id") != provider_id and p.get("key") != provider_id]
    if len(new_list) == len(user_list):
        raise HTTPException(status_code=404, detail="Провайдер не найден")
    await lp.save_user_providers(repo, new_list)
    return {"status": "deleted"}


@router.get("/api/settings/models/{provider_key}")
async def list_models(provider_key: str, db: AsyncSession = Depends(get_db)):
    """Статический список из YAML (fallback). Динамическая загрузка — POST /api/settings/fetch-models."""
    builtin = _load_builtin_providers()
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    user_list = await lp.ensure_user_providers_migrated(repo, builtin)
    for p in builtin:
        if p["key"] == provider_key:
            return {"models": p.get("models", [])}
    for p in user_list:
        if p.get("key") == provider_key or p.get("id") == provider_key:
            return {"models": p.get("models", [])}
    return {"models": []}


def _extract_model_ids_from_response(body: object) -> list[str]:
    """Разбор OpenAI-compatible и близких ответов /v1/models."""
    models: list[str] = []
    if not isinstance(body, dict):
        return models
    items = body.get("data")
    if items is None:
        items = body.get("models")
    if not isinstance(items, list):
        return models
    for item in items:
        if isinstance(item, str) and item.strip():
            models.append(item.strip())
        elif isinstance(item, dict):
            mid = item.get("id") or item.get("name") or item.get("model")
            if mid:
                models.append(str(mid).strip())
    return models


def _build_llm_http_headers(api_key: str, extra_raw: str | None) -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key and not lp.is_masked_api_key(api_key):
        headers["Authorization"] = f"Bearer {api_key}"
    headers.update(lp.parse_extra_headers_dict(extra_raw))
    return headers


@router.post("/api/settings/fetch-models")
async def fetch_models(data: dict, db: AsyncSession = Depends(get_db)):
    """GET {base_url}/models в формате OpenAI-compatible."""
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    base_url = (data.get("base_url") or "").strip().rstrip("/")
    api_key = (data.get("api_key") or "").strip()
    if lp.is_masked_api_key(api_key):
        api_key = (await repo.get("api_key", "") or "").strip()
    extra_in = data.get("llm_extra_headers")
    if isinstance(extra_in, dict):
        extra_in = json.dumps(extra_in, ensure_ascii=False)
    elif extra_in is None:
        extra_in = await repo.get("llm_extra_headers", "") or "{}"
    else:
        extra_in = str(extra_in)
    extra_merged = lp.merge_extra_headers_json(extra_in, await repo.get("llm_extra_headers", ""))
    if not base_url:
        return {"models": [], "error": "Укажите base_url"}
    url = f"{base_url}/models"
    headers = _build_llm_http_headers(api_key, extra_merged)
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        body = resp.json()
        models = _extract_model_ids_from_response(body)
        return {"models": sorted(set(models))}
    except httpx.HTTPStatusError as e:
        return {
            "models": [],
            "error": f"HTTP {e.response.status_code}: {(e.response.text or '')[:300]}",
        }
    except Exception as e:
        return {"models": [], "error": str(e)[:400]}


@router.get("/api/settings/profiles")
async def list_profiles(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    profiles = await lp.load_profiles(repo)
    return [lp.mask_profile(p) for p in profiles]


@router.post("/api/settings/profiles")
async def create_profile(data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    provider_key = (data.get("provider_key") or "").strip()
    model = (data.get("model") or "").strip()
    api_key = (data.get("api_key") or "").strip()
    base_url = (data.get("base_url") or "").strip().rstrip("/")

    if not model or not base_url:
        raise HTTPException(status_code=400, detail="Обязательны base_url и model")
    if api_key and lp.is_masked_api_key(api_key):
        raise HTTPException(status_code=400, detail="Некорректный api_key")

    repo = SettingsRepository(db)
    builtin = _load_builtin_providers()
    user_list = await lp.ensure_user_providers_migrated(repo, builtin)

    name = (data.get("name") or "").strip()
    if not name:
        name = lp.suggested_profile_name(provider_key or "custom", model, builtin, user_list)

    extra_headers_raw = data.get("extra_headers")
    if isinstance(extra_headers_raw, dict):
        extra_headers_raw = json.dumps(extra_headers_raw, ensure_ascii=False)
    extra_headers = (extra_headers_raw or "{}").strip() or "{}"
    try:
        json.loads(extra_headers)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="extra_headers: невалидный JSON") from None

    profiles = await lp.load_profiles(repo)
    profiles.append(
        {
            "id": lp.new_id(),
            "name": name,
            "provider_key": provider_key,
            "base_url": base_url,
            "model": model,
            "api_key": api_key,
            "extra_headers": extra_headers,
        }
    )
    await lp.save_profiles(repo, profiles)
    return lp.mask_profile(profiles[-1])


@router.put("/api/settings/profiles/{profile_id}")
async def update_profile(profile_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    profiles = await lp.load_profiles(repo)
    idx = next((i for i, p in enumerate(profiles) if p.get("id") == profile_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    p = profiles[idx]
    if "name" in data and data["name"] is not None:
        p["name"] = str(data["name"]).strip()
    if "provider_key" in data and data["provider_key"] is not None:
        p["provider_key"] = str(data["provider_key"]).strip()
    if "base_url" in data and data["base_url"] is not None:
        p["base_url"] = str(data["base_url"]).strip().rstrip("/")
    if "model" in data and data["model"] is not None:
        p["model"] = str(data["model"]).strip()
    if "api_key" in data and data["api_key"] is not None:
        ak = str(data["api_key"]).strip()
        if ak and not lp.is_masked_api_key(ak):
            p["api_key"] = ak
    if "extra_headers" in data and data["extra_headers"] is not None:
        eh_raw = data["extra_headers"]
        if isinstance(eh_raw, dict):
            eh_raw = json.dumps(eh_raw, ensure_ascii=False)
        else:
            eh_raw = str(eh_raw).strip() or "{}"
        eh_merged = lp.merge_extra_headers_json(eh_raw, p.get("extra_headers", ""))
        p["extra_headers"] = eh_merged

    if not (p.get("name") and p.get("base_url") and p.get("model")):
        raise HTTPException(status_code=400, detail="Заполните name, base_url, model")

    await lp.save_profiles(repo, profiles)
    return lp.mask_profile(p)


@router.delete("/api/settings/profiles/{profile_id}")
async def delete_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    profiles = await lp.load_profiles(repo)
    new_list = [p for p in profiles if p.get("id") != profile_id]
    if len(new_list) == len(profiles):
        raise HTTPException(status_code=404, detail="Профиль не найден")
    await lp.save_profiles(repo, new_list)
    return {"status": "deleted"}


@router.post("/api/settings/profiles/{profile_id}/apply")
async def apply_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    profiles = await lp.load_profiles(repo)
    profile = next((p for p in profiles if p.get("id") == profile_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    pk = profile.get("provider_key") or ""
    base_url = (profile.get("base_url") or "").strip().rstrip("/")
    if not base_url:
        # fallback: derive from provider_key for old-format profiles
        builtin = _load_builtin_providers()
        user_list = await lp.ensure_user_providers_migrated(repo, builtin)
        base_url = lp.resolve_provider_base_url(pk, builtin, user_list) or ""
    if not base_url:
        raise HTTPException(status_code=400, detail="Не удалось определить base_url профиля")
    extra_headers = (profile.get("extra_headers") or "{}").strip() or "{}"
    await repo.put_many(
        {
            "provider": pk,
            "base_url": base_url,
            "model": profile.get("model") or "",
            "api_key": profile.get("api_key") or "",
            "llm_extra_headers": extra_headers,
            "active_profile_id": profile_id,
        }
    )
    return {"status": "applied"}


@router.post("/api/settings/suggest-profile-name")
async def suggest_profile_name(data: dict, db: AsyncSession = Depends(get_db)):
    provider_key = (data.get("provider_key") or "").strip()
    model = (data.get("model") or "").strip()
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    builtin = _load_builtin_providers()
    user_list = await lp.ensure_user_providers_migrated(repo, builtin)
    return {"name": lp.suggested_profile_name(provider_key, model, builtin, user_list)}


@router.post("/api/settings/test-connection")
async def test_connection(data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.settings_repository import SettingsRepository

    repo = SettingsRepository(db)
    base_url = (data.get("base_url") or "").strip() or await repo.get("base_url", "")
    api_key = (data.get("api_key") or "").strip() or await repo.get("api_key", "")
    model = (data.get("model") or "").strip() or await repo.get("model", "")

    if lp.is_masked_api_key(api_key):
        api_key = await repo.get("api_key", "") or ""

    extra_in = data.get("llm_extra_headers")
    if isinstance(extra_in, dict):
        extra_in = json.dumps(extra_in, ensure_ascii=False)
    elif extra_in is None:
        extra_in = await repo.get("llm_extra_headers", "") or "{}"
    else:
        extra_in = str(extra_in)
    extra_merged = lp.merge_extra_headers_json(extra_in, await repo.get("llm_extra_headers", ""))

    if not base_url:
        return {"success": False, "error": "Base URL не указан"}

    headers = _build_llm_http_headers(api_key, extra_merged)
    url = f"{base_url.rstrip('/')}/models"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code in (401, 403):
            return {"success": False, "error": f"Ошибка авторизации (HTTP {resp.status_code}). Проверьте API-ключ и дополнительные заголовки."}
        if resp.status_code >= 400:
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}

        try:
            body = resp.json()
            models = _extract_model_ids_from_response(body)
            count = len(models)
            msg = f"Подключение успешно! Доступно моделей: {count}." if count else "Подключение успешно!"
        except Exception:
            msg = "Подключение успешно!"
        return {"success": True, "message": msg}
    except httpx.ConnectError:
        return {"success": False, "error": f"Не удалось подключиться к {base_url}. Проверьте Base URL."}
    except httpx.TimeoutException:
        return {"success": False, "error": "Превышено время ожидания (15 с). Сервер недоступен."}
    except Exception as e:
        return {"success": False, "error": str(e)[:300]}
