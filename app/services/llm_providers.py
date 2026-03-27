"""Сборка списка LLM-провайдеров (встроенные + пользовательские), маскирование ключей."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

USER_PROVIDERS_KEY = "user_providers"
LLM_PROFILES_KEY = "llm_profiles"


def mask_api_key(value: str | None) -> str:
    if not value:
        return ""
    if "••••" in value:
        return value
    if len(value) <= 8:
        return "••••••••"
    return value[:8] + "••••••••"


def is_masked_api_key(value: str | None) -> bool:
    return bool(value and "••••" in value)


def slug_key(name: str, existing_keys: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "provider"
    key = base
    n = 1
    while key in existing_keys:
        n += 1
        key = f"{base}-{n}"
    return key


def _parse_json_list(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


async def load_user_providers(repo) -> list[dict[str, Any]]:
    raw = await repo.get(USER_PROVIDERS_KEY, "[]")
    return _parse_json_list(raw)


def normalize_user_provider_records(
    user_list: list[dict[str, Any]],
    builtin_keys: set[str],
) -> tuple[list[dict[str, Any]], bool, list[tuple[str, str, str]]]:
    """Заполняет id и уникальный key; снимает коллизии имён со встроенными и между пользовательскими.

    rename_events: (old_key, new_key, base_url_norm) — для обновления профилей и глобального provider.
    """
    out: list[dict[str, Any]] = []
    dirty = False
    rename_events: list[tuple[str, str, str]] = []
    used: set[str] = set(builtin_keys)

    for p in user_list:
        if not isinstance(p, dict):
            continue
        q = dict(p)
        if not str(q.get("id") or "").strip():
            q["id"] = new_id()
            dirty = True
        base_url_norm = (q.get("base_url") or "").strip().rstrip("/")
        k = (q.get("key") or "").strip()
        if not k:
            name = (q.get("name") or "").strip() or base_url_norm or "endpoint"
            nk = slug_key(name, used)
            q["key"] = nk
            used.add(nk)
            dirty = True
        elif k in used:
            old_k = k
            nk = slug_key(f"{k}-endpoint", used)
            q["key"] = nk
            used.add(nk)
            dirty = True
            rename_events.append((old_k, nk, base_url_norm))
        else:
            used.add(k)
        out.append(q)
    return out, dirty, rename_events


def apply_provider_key_renames_to_profiles(
    profiles: list[dict[str, Any]],
    rename_events: list[tuple[str, str, str]],
) -> bool:
    """Подставляет новый provider_key в профилях после переименования эндпоинта."""
    dirty = False
    for old_k, new_k, base_url_norm in rename_events:
        for prof in profiles:
            if not isinstance(prof, dict):
                continue
            if (prof.get("provider_key") or "").strip() != old_k:
                continue
            p_base = (prof.get("base_url") or "").strip().rstrip("/")
            if base_url_norm and p_base != base_url_norm:
                continue
            prof["provider_key"] = new_k
            dirty = True
    return dirty


async def _migrate_global_provider_after_rename(
    repo,
    rename_events: list[tuple[str, str, str]],
) -> None:
    current = (await repo.get("provider", "") or "").strip()
    if not current:
        return
    global_base = (await repo.get("base_url", "") or "").strip().rstrip("/")
    for old_k, new_k, base_url_norm in rename_events:
        if current != old_k:
            continue
        if base_url_norm and global_base != base_url_norm:
            continue
        await repo.put("provider", new_k)
        break


async def ensure_user_providers_migrated(repo, builtin: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Загружает user_providers, при необходимости мигрирует и сохраняет в БД."""
    raw = await load_user_providers(repo)
    builtin_keys = {str(p["key"]) for p in builtin if p.get("key")}
    normalized, dirty, rename_events = normalize_user_provider_records(raw, builtin_keys)
    if not dirty and not rename_events:
        return normalized
    await save_user_providers(repo, normalized)
    if rename_events:
        profiles = await load_profiles(repo)
        if apply_provider_key_renames_to_profiles(profiles, rename_events):
            await save_profiles(repo, profiles)
        await _migrate_global_provider_after_rename(repo, rename_events)
    return normalized


async def save_user_providers(repo, providers: list[dict[str, Any]]) -> None:
    await repo.put(USER_PROVIDERS_KEY, json.dumps(providers, ensure_ascii=False))


async def load_profiles(repo) -> list[dict[str, Any]]:
    raw = await repo.get(LLM_PROFILES_KEY, "[]")
    return _parse_json_list(raw)


async def save_profiles(repo, profiles: list[dict[str, Any]]) -> None:
    await repo.put(LLM_PROFILES_KEY, json.dumps(profiles, ensure_ascii=False))


def mask_user_provider(p: dict[str, Any]) -> dict[str, Any]:
    out = dict(p)
    if out.get("api_key"):
        out["api_key"] = mask_api_key(out["api_key"])
    return out


def mask_profile(p: dict[str, Any]) -> dict[str, Any]:
    out = dict(p)
    if out.get("api_key"):
        out["api_key"] = mask_api_key(out["api_key"])
    if out.get("extra_headers"):
        out["extra_headers"] = mask_extra_headers_json(out["extra_headers"])
    return out


def merge_providers_for_api(builtin: list[dict[str, Any]], user_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for p in builtin:
        merged.append(
            {
                "id": p["key"],
                "key": p["key"],
                "name": p["name"],
                "base_url": p.get("base_url") or "",
                "models": p.get("models") or [],
                "source": "builtin",
                "readonly": True,
            }
        )
    for p in user_list:
        merged.append(
            {
                "id": p.get("id") or p.get("key"),
                "key": p.get("key"),
                "name": p.get("name", ""),
                "base_url": p.get("base_url") or "",
                "api_key": mask_api_key(p.get("api_key", "")),
                "models": p.get("models") or [],
                "source": "user",
                "readonly": False,
            }
        )
    return merged


def resolve_provider_base_url(
    provider_key: str,
    builtin: list[dict[str, Any]],
    user_list: list[dict[str, Any]],
) -> str | None:
    for p in builtin:
        if p.get("key") == provider_key:
            return (p.get("base_url") or "").strip() or None
    for p in user_list:
        if p.get("key") == provider_key or p.get("id") == provider_key:
            return (p.get("base_url") or "").strip() or None
    return None


def resolve_provider_display_name(
    provider_key: str,
    builtin: list[dict[str, Any]],
    user_list: list[dict[str, Any]],
) -> str:
    for p in builtin:
        if p.get("key") == provider_key:
            return p.get("name") or provider_key
    for p in user_list:
        if p.get("key") == provider_key or p.get("id") == provider_key:
            return p.get("name") or provider_key
    return provider_key


def suggested_profile_name(provider_key: str, model: str, builtin: list[dict], user_list: list[dict]) -> str:
    name = resolve_provider_display_name(provider_key, builtin, user_list)
    m = model.strip() or "model"
    return f"{name} / {m}"


def new_id() -> str:
    return str(uuid.uuid4())


def mask_extra_headers_json(raw: str | None) -> str:
    """Маскирует значения в JSON объекта заголовков."""
    if not raw or not str(raw).strip():
        return "{}"
    try:
        o = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if not isinstance(o, dict):
        return raw
    out: dict[str, Any] = {}
    for k, v in o.items():
        if isinstance(v, str) and v.strip():
            out[str(k)] = mask_api_key(v)
        else:
            out[str(k)] = v
    return json.dumps(out, ensure_ascii=False)


def merge_extra_headers_json(incoming: str | None, stored: str | None) -> str:
    """Подставляет сохранённые значения для ключей с маской ••••."""
    try:
        inc = json.loads(incoming or "{}")
    except json.JSONDecodeError:
        inc = {}
    try:
        sto = json.loads(stored or "{}")
    except json.JSONDecodeError:
        sto = {}
    if not isinstance(inc, dict):
        inc = {}
    if not isinstance(sto, dict):
        sto = {}
    out = dict(inc)
    for k, v in list(out.items()):
        if isinstance(v, str) and "••••" in v and k in sto:
            out[k] = sto[k]
    return json.dumps(out, ensure_ascii=False)


def parse_extra_headers_dict(raw: str | None) -> dict[str, str]:
    try:
        o = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    if not isinstance(o, dict):
        return {}
    result: dict[str, str] = {}
    for k, v in o.items():
        if v is None:
            continue
        s = str(v).strip()
        if s:
            result[str(k)] = s
    return result
