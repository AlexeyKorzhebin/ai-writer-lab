import os

import yaml
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.routers.deps import get_llm

router = APIRouter(tags=["locations"])

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _load_world_presets():
    presets_dir = os.path.join(_DATA_DIR, "world_presets")
    result = []
    if not os.path.isdir(presets_dir):
        return result
    for fname in sorted(os.listdir(presets_dir)):
        if fname.endswith((".yaml", ".yml")):
            with open(os.path.join(presets_dir, fname), encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    data["key"] = fname.rsplit(".", 1)[0]
                    result.append(data)
    return result


@router.get("/world-presets")
async def list_world_presets():
    return _load_world_presets()


@router.get("/world-presets/{key}")
async def get_world_preset(key: str):
    for p in _load_world_presets():
        if p.get("key") == key:
            return p
    return {"error": "Preset not found"}


@router.get("/projects/{project_id}/locations")
async def list_locations(project_id: int, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.location_repository import LocationRepository

    repo = LocationRepository(db)
    locations = await repo.list_by_project(project_id)
    return [
        {
            "id": loc.id, "name": loc.name, "location_type": loc.location_type,
            "parent_id": loc.parent_id, "description": loc.description,
            "atmosphere": loc.atmosphere, "tags": loc.tags or [],
        }
        for loc in locations
    ]


@router.post("/projects/{project_id}/locations")
async def create_location(project_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.location_repository import LocationRepository

    repo = LocationRepository(db)
    loc = await repo.create(project_id, data)
    return {"id": loc.id, "name": loc.name}


@router.put("/projects/{project_id}/locations/{location_id}")
async def update_location(project_id: int, location_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.location_repository import LocationRepository

    repo = LocationRepository(db)
    loc = await repo.update(location_id, data)
    if not loc:
        return {"error": "Location not found"}
    return {"status": "updated"}


@router.delete("/projects/{project_id}/locations/{location_id}")
async def delete_location(project_id: int, location_id: int, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.location_repository import LocationRepository

    repo = LocationRepository(db)
    ok = await repo.delete(location_id)
    if not ok:
        return {"error": "Location not found"}
    return {"status": "deleted"}


@router.post("/projects/{project_id}/narrative-spec/generate-locations")
async def generate_locations(project_id: int, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    if not llm:
        return {"error": "LLM not configured"}

    from app.infrastructure.repositories.narrative_repository import NarrativeRepository

    spec_repo = NarrativeRepository(db)
    spec = await spec_repo.get_by_project(project_id)
    if not spec:
        return {"error": "NarrativeSpec not found"}

    prompt = f"""На основе этой истории предложи 5-8 ключевых локаций.

Логлайн: {spec.core_idea.logline}
Жанр: {spec.core_idea.genre.value}
Мир: {spec.world.world_type}, период: {spec.world.time_period}

Верни JSON-массив:
[{{"name": "...", "location_type": "region|city|building|room|natural|road", "description": "...", "atmosphere": "...", "significance": "..."}}]

Только JSON, без пояснений."""

    import json
    text = await llm.generate(prompt)
    try:
        locations = json.loads(text)
    except Exception:
        return {"error": "Не удалось разобрать ответ LLM", "raw": text[:500]}

    from app.infrastructure.repositories.location_repository import LocationRepository
    repo = LocationRepository(db)
    created = []
    for loc_data in locations:
        loc = await repo.create(project_id, loc_data)
        created.append({"id": loc.id, "name": loc.name})
    return {"locations": created}


@router.post("/projects/{project_id}/locations/{location_id}/expand")
async def expand_location(project_id: int, location_id: int, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    if not llm:
        return {"error": "LLM not configured"}

    from app.infrastructure.repositories.location_repository import LocationRepository

    repo = LocationRepository(db)
    loc = await repo.get_by_id(location_id)
    if not loc:
        return {"error": "Location not found"}

    prompt = f"""Расширь описание локации для художественного произведения.

Название: {loc.name}
Тип: {loc.location_type}
Текущее описание: {loc.description}

Добавь: visual_details, atmosphere, significance, climate, inhabitants, notable_features.
Верни JSON: {{"visual_details": "...", "atmosphere": "...", "significance": "...", "climate": "...", "inhabitants": "...", "notable_features": "..."}}"""

    import json
    text = await llm.generate(prompt)
    try:
        expanded = json.loads(text)
        await repo.update(location_id, expanded)
        return {"status": "expanded", "data": expanded}
    except Exception:
        return {"error": "Не удалось разобрать ответ", "raw": text[:500]}


@router.post("/projects/{project_id}/world/import")
async def import_world(project_id: int, data: dict, db: AsyncSession = Depends(get_db), llm=Depends(get_llm)):
    """Import world by name, by text, or from preset."""
    import_type = data.get("type", "name")
    content = data.get("content", "")

    if import_type == "preset":
        key = data.get("preset_key", "")
        for p in _load_world_presets():
            if p.get("key") == key:
                return {"world": p, "locations": p.get("locations", [])}
        return {"error": "Preset not found"}

    if not llm:
        return {"error": "LLM not configured"}

    if import_type == "name":
        prompt = f"""Восстанови мир из произведения по названию/описанию: "{content}"

Верни JSON:
{{"world_type": "...", "time_period": "...", "atmosphere": "...", "rules": "...",
  "locations": [{{"name": "...", "location_type": "...", "description": "..."}}]}}"""
    else:
        prompt = f"""Структурируй описание мира из текста:

{content[:3000]}

Верни JSON:
{{"world_type": "...", "time_period": "...", "atmosphere": "...", "rules": "...",
  "locations": [{{"name": "...", "location_type": "...", "description": "..."}}]}}"""

    import json
    text = await llm.generate(prompt)
    try:
        result = json.loads(text)
        return result
    except Exception:
        return {"error": "Не удалось разобрать ответ", "raw": text[:500]}
