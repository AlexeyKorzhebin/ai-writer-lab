import dataclasses
import os

import yaml
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from app.core.database import get_db
from app.routers.deps import templates, get_llm

router = APIRouter(tags=["narrative"])

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


@router.get("/projects/{project_id}/story/wizard", response_class=HTMLResponse)
async def story_wizard(
    project_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    from app.infrastructure.repositories.project_repository import ProjectRepository
    from app.domain.story_formats.registry import StoryFormatRegistry

    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if not project:
        return HTMLResponse(content="Project not found", status_code=404)

    formats = StoryFormatRegistry.list_formats()
    return templates.TemplateResponse(
        "story_wizard.html",
        {"request": request, "project": project, "formats": formats},
    )


@router.get("/projects/{project_id}/story/workspace", response_class=HTMLResponse)
async def story_workspace(
    project_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    from app.infrastructure.repositories.project_repository import ProjectRepository
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository

    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if not project:
        return HTMLResponse(content="Project not found", status_code=404)

    narrative_repo = NarrativeRepository(db)
    spec = await narrative_repo.get_by_project(project_id)
    if not spec:
        return RedirectResponse(url=f"/projects/{project_id}/story/wizard")

    spec_scenes_plain = [dataclasses.asdict(s) for s in spec.scenes] if spec else []

    return templates.TemplateResponse(
        "story_workspace.html",
        {
            "request": request,
            "project": project,
            "spec": spec,
            "spec_scenes_plain": spec_scenes_plain,
        },
    )


@router.get("/projects/{project_id}/narrative-spec")
async def get_narrative_spec(project_id: int, db: AsyncSession = Depends(get_db)):
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository
    import dataclasses
    import json

    narrative_repo = NarrativeRepository(db)
    spec = await narrative_repo.get_by_project(project_id)
    if not spec:
        return {"error": "NarrativeSpec not found"}
    return json.loads(json.dumps(dataclasses.asdict(spec), default=str))


@router.post("/projects/{project_id}/narrative-spec")
async def create_narrative_spec(
    project_id: int, data: dict, db: AsyncSession = Depends(get_db)
):
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository
    from app.infrastructure.repositories.project_repository import ProjectRepository
    from app.application.use_cases.narrative_spec import CreateNarrativeSpecUseCase

    narrative_repo = NarrativeRepository(db)
    project_repo = ProjectRepository(db)
    use_case = CreateNarrativeSpecUseCase(narrative_repo, project_repo)
    spec = await use_case.execute(project_id, data)
    if not spec:
        return {"error": "Project not found"}
    return {"status": "created", "version": spec.version}


@router.put("/projects/{project_id}/narrative-spec")
async def update_narrative_spec(
    project_id: int, data: dict, db: AsyncSession = Depends(get_db)
):
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository
    from app.application.use_cases.narrative_spec import UpdateNarrativeSpecUseCase

    narrative_repo = NarrativeRepository(db)
    use_case = UpdateNarrativeSpecUseCase(narrative_repo)
    spec = await use_case.execute(project_id, data)
    if not spec:
        return {"error": "NarrativeSpec not found"}
    return {"status": "updated", "version": spec.version}


@router.post("/projects/{project_id}/narrative-spec/generate-outline")
async def generate_narrative_outline(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository
    from app.application.use_cases.narrative_spec import GenerateOutlineFromSpecUseCase

    narrative_repo = NarrativeRepository(db)
    use_case = GenerateOutlineFromSpecUseCase(narrative_repo, llm)
    return await use_case.execute(project_id)


@router.post("/projects/{project_id}/narrative-spec/generate-scene/{scene_index}")
async def generate_scene(
    project_id: int,
    scene_index: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository
    from app.application.use_cases.narrative_spec import GenerateSceneUseCase

    narrative_repo = NarrativeRepository(db)
    use_case = GenerateSceneUseCase(narrative_repo, llm)
    return await use_case.execute(project_id, scene_index)


@router.post(
    "/projects/{project_id}/narrative-spec/generate-scene-variants/{scene_index}"
)
async def generate_scene_variants(
    project_id: int,
    scene_index: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository
    from app.application.use_cases.narrative_spec import GenerateSceneUseCase

    narrative_repo = NarrativeRepository(db)
    use_case = GenerateSceneUseCase(narrative_repo, llm)
    return await use_case.execute(project_id, scene_index, variants=3)


@router.post("/projects/{project_id}/narrative-spec/character-consistency")
async def check_character_consistency(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm),
):
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository
    from app.core.agents.character_consistency import CharacterConsistencyAgent

    narrative_repo = NarrativeRepository(db)
    spec = await narrative_repo.get_by_project(project_id)
    if not spec:
        return {"error": "NarrativeSpec not found"}
    if not llm:
        return {"error": "LLM not configured"}

    agent = CharacterConsistencyAgent(llm)
    return await agent.check_full_story(spec)


@router.post("/projects/{project_id}/narrative-spec/check-consistency")
async def check_narrative_consistency(
    project_id: int, db: AsyncSession = Depends(get_db)
):
    from app.infrastructure.repositories.narrative_repository import NarrativeRepository
    from app.domain.story_formats.registry import StoryFormatRegistry

    narrative_repo = NarrativeRepository(db)
    spec = await narrative_repo.get_by_project(project_id)
    if not spec:
        return {"error": "NarrativeSpec not found"}

    fmt = StoryFormatRegistry.get_or_default(spec.core_idea.story_format)
    stale_scenes = []
    for i, scene in enumerate(spec.scenes):
        if scene.content:
            stale_scenes.append(
                {
                    "index": i,
                    "title": scene.title,
                    "reason": "Scene was written under a previous NarrativeSpec version and may be inconsistent",
                }
            )
    return {
        "spec_version": spec.version,
        "total_scenes": len(spec.scenes),
        "stale_scenes": stale_scenes,
        "consistency_rules": fmt.consistency_rules(),
    }


@router.get("/story-formats")
async def list_story_formats():
    from app.domain.story_formats.registry import StoryFormatRegistry

    return StoryFormatRegistry.list_formats()


def _load_author_presets():
    path = os.path.join(_DATA_DIR, "author_presets.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f).get("presets", [])


@router.get("/author-presets")
async def get_author_presets():
    return _load_author_presets()


@router.post("/author-presets/generate-sample")
async def generate_author_sample(data: dict, llm=Depends(get_llm)):
    if not llm:
        return {"error": "LLM not configured"}

    style_prompt = data.get("style_prompt", "")
    logline = data.get("logline", "история о путешествии и самопознании")

    prompt = f"""Ты — литературный стилист. Напиши короткий абзац (3-5 предложений) в следующем стиле:

{style_prompt}

Тема: {logline}

Напиши только текст, без комментариев и пояснений."""

    text = await llm.generate(prompt, temperature=0.8)
    return {"sample": text.strip()}
