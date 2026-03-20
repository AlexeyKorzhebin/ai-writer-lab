import os
import json
import shutil
import uuid

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import IllustrationPromptORM
from app.routers.deps import get_llm

router = APIRouter(tags=["illustrations"])

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


def _load_templates():
    tpl_dir = os.path.join(_DATA_DIR, "illustration_templates")
    result = []
    if not os.path.isdir(tpl_dir):
        return result
    for fname in sorted(os.listdir(tpl_dir)):
        if fname.endswith(".md"):
            with open(os.path.join(tpl_dir, fname), encoding="utf-8") as f:
                content = f.read()
                name = fname.rsplit(".", 1)[0]
                title = content.split("\n")[0].lstrip("# ").strip() if content else name
                result.append({"key": name, "name": title, "content": content})
    return result


@router.get("/illustration-templates")
async def list_templates():
    return _load_templates()


@router.post("/projects/{project_id}/narrative-spec/illustration-variants/{scene_idx}")
async def generate_illustration_variants(
    project_id: int, scene_idx: int,
    db: AsyncSession = Depends(get_db), llm=Depends(get_llm)
):
    if not llm:
        return {"error": "LLM not configured"}

    from app.infrastructure.repositories.narrative_repository import NarrativeRepository

    repo = NarrativeRepository(db)
    spec = await repo.get_by_project(project_id)
    if not spec or scene_idx >= len(spec.scenes):
        return {"error": "Scene not found"}

    scene = spec.scenes[scene_idx]
    characters = ", ".join(scene.participants) if scene.participants else "не указаны"

    prompt = f"""Предложи 3 варианта визуальной композиции для иллюстрации этой сцены.

Сцена: {scene.title}
Текст: {(scene.content or scene.summary or '')[:1000]}
Персонажи: {characters}

Для каждого варианта опиши: composition, camera_angle, lighting, key_details, emotional_focus.
Верни JSON-массив из 3 объектов:
[{{"variant": "A", "composition": "...", "camera_angle": "...", "lighting": "...", "key_details": "...", "emotional_focus": "..."}}]"""

    text = await llm.generate(prompt)
    try:
        variants = json.loads(text)
        prompt_orm = IllustrationPromptORM(
            project_id=project_id, scene_index=scene_idx,
            variant_data=variants,
        )
        db.add(prompt_orm)
        await db.commit()
        return {"variants": variants}
    except Exception:
        return {"error": "Не удалось разобрать ответ", "raw": text[:500]}


@router.post("/projects/{project_id}/narrative-spec/illustration-prompt/{scene_idx}")
async def generate_illustration_prompt(
    project_id: int, scene_idx: int, data: dict,
    db: AsyncSession = Depends(get_db), llm=Depends(get_llm)
):
    if not llm:
        return {"error": "LLM not configured"}

    from app.infrastructure.repositories.narrative_repository import NarrativeRepository

    repo = NarrativeRepository(db)
    spec = await repo.get_by_project(project_id)
    if not spec or scene_idx >= len(spec.scenes):
        return {"error": "Scene not found"}

    scene = spec.scenes[scene_idx]
    template_key = data.get("template", "realistic_book")
    variant_desc = data.get("description", "")

    templates = _load_templates()
    tpl = next((t for t in templates if t["key"] == template_key), None)
    tpl_content = tpl["content"] if tpl else ""

    characters = ", ".join(scene.participants) if scene.participants else ""

    prompt = f"""Сгенерируй финальный промпт для создания иллюстрации.

Шаблон стиля:
{tpl_content}

Описание сцены: {variant_desc or scene.content or scene.summary or scene.title}
Персонажи: {characters}
Настроение: {scene.emotional_state or ''}

Замени переменные {{{{scene_description}}}}, {{{{characters}}}}, {{{{mood}}}}, {{{{setting}}}}, {{{{time_of_day}}}} в шаблоне.
Верни только итоговый промпт на английском."""

    result_text = await llm.generate(prompt)

    prompt_orm = IllustrationPromptORM(
        project_id=project_id, scene_index=scene_idx,
        template=template_key, prompt_text=result_text.strip(),
    )
    db.add(prompt_orm)
    await db.commit()

    return {"prompt": result_text.strip()}


@router.post("/projects/{project_id}/illustrations/upload")
async def upload_illustration(project_id: int, file: UploadFile = File(...)):
    project_dir = os.path.join(_UPLOAD_DIR, "projects", str(project_id), "illustrations")
    os.makedirs(project_dir, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "png"
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(project_dir, filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"path": f"/uploads/projects/{project_id}/illustrations/{filename}", "filename": filename}


@router.get("/projects/{project_id}/illustrations")
async def list_illustrations(project_id: int):
    project_dir = os.path.join(_UPLOAD_DIR, "projects", str(project_id), "illustrations")
    if not os.path.isdir(project_dir):
        return []
    return [
        {"filename": f, "path": f"/uploads/projects/{project_id}/illustrations/{f}"}
        for f in sorted(os.listdir(project_dir))
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]
