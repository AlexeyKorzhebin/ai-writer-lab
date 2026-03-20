"""Use cases for NarrativeSpec CRUD and scene generation."""

from __future__ import annotations

import json
import re
import logging
from typing import Optional

from app.domain.narrative import (
    NarrativeSpec, CoreIdea, WorldSpec, CharacterSpec, CharacterArc,
    StructuralSpec, SceneSpec, Genre, MacroStructure, CharacterRole,
)
from app.domain.story_formats.registry import StoryFormatRegistry

logger = logging.getLogger(__name__)


class CreateNarrativeSpecUseCase:
    """Create a new NarrativeSpec for a project from wizard data."""

    def __init__(self, narrative_repo, project_repo):
        self.narrative_repo = narrative_repo
        self.project_repo = project_repo

    async def execute(self, project_id: int, data: dict) -> NarrativeSpec | None:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return None

        spec = NarrativeSpec(project_id=project_id, version=1)

        idea = data.get("core_idea", {})
        spec.core_idea = CoreIdea(
            logline=idea.get("logline", ""),
            genre=_safe_genre(idea.get("genre")),
            tone=idea.get("tone", ""),
            themes=idea.get("themes", []),
            central_conflict=idea.get("central_conflict", ""),
            story_format=idea.get("story_format", "three_act"),
        )

        world = data.get("world", {})
        spec.world = WorldSpec(
            world_type=world.get("world_type", "realistic"),
            rules=world.get("rules", ""),
            time_period=world.get("time_period", ""),
            power_structures=world.get("power_structures", ""),
            atmosphere=world.get("atmosphere", ""),
        )

        for ch_data in data.get("characters", []):
            ch = CharacterSpec(
                name=ch_data.get("name", ""),
                role=_safe_role(ch_data.get("role")),
                motivation=ch_data.get("motivation", ""),
                fear=ch_data.get("fear", ""),
                secret=ch_data.get("secret", ""),
                arc=CharacterArc(
                    start_state=ch_data.get("arc_start", ""),
                    inner_conflict=ch_data.get("arc_conflict", ""),
                    turning_point=ch_data.get("arc_turning", ""),
                    end_state=ch_data.get("arc_end", ""),
                ),
            )
            spec.characters.append(ch)

        structure = data.get("structure", {})
        spec.structure = StructuralSpec(
            macro_structure=_safe_macro(structure.get("macro_structure")),
            climax=structure.get("climax", ""),
            resolution=structure.get("resolution", ""),
        )

        return await self.narrative_repo.save(spec)


class UpdateNarrativeSpecUseCase:
    """Update an existing NarrativeSpec (partial updates supported)."""

    def __init__(self, narrative_repo):
        self.narrative_repo = narrative_repo

    async def execute(self, project_id: int, data: dict) -> NarrativeSpec | None:
        spec = await self.narrative_repo.get_by_project(project_id)
        if not spec:
            return None

        spec.version += 1

        if "core_idea" in data:
            idea = data["core_idea"]
            if "logline" in idea:
                spec.core_idea.logline = idea["logline"]
            if "genre" in idea:
                spec.core_idea.genre = _safe_genre(idea["genre"])
            if "tone" in idea:
                spec.core_idea.tone = idea["tone"]
            if "themes" in idea:
                spec.core_idea.themes = idea["themes"]
            if "central_conflict" in idea:
                spec.core_idea.central_conflict = idea["central_conflict"]
            if "story_format" in idea:
                spec.core_idea.story_format = idea["story_format"]

        if "world" in data:
            w = data["world"]
            for key in ("world_type", "rules", "time_period", "power_structures", "atmosphere"):
                if key in w:
                    setattr(spec.world, key, w[key])

        if "characters" in data:
            spec.characters = []
            for ch_data in data["characters"]:
                ch = CharacterSpec(
                    name=ch_data.get("name", ""),
                    role=_safe_role(ch_data.get("role")),
                    motivation=ch_data.get("motivation", ""),
                    fear=ch_data.get("fear", ""),
                    secret=ch_data.get("secret", ""),
                    arc=CharacterArc(
                        start_state=ch_data.get("arc_start", ""),
                        inner_conflict=ch_data.get("arc_conflict", ""),
                        turning_point=ch_data.get("arc_turning", ""),
                        end_state=ch_data.get("arc_end", ""),
                    ),
                )
                spec.characters.append(ch)

        if "structure" in data:
            s = data["structure"]
            if "macro_structure" in s:
                spec.structure.macro_structure = _safe_macro(s["macro_structure"])
            if "climax" in s:
                spec.structure.climax = s["climax"]
            if "resolution" in s:
                spec.structure.resolution = s["resolution"]

        return await self.narrative_repo.save(spec)


class GenerateOutlineFromSpecUseCase:
    """Use the story format strategy to generate an outline from NarrativeSpec."""

    def __init__(self, narrative_repo, llm):
        self.narrative_repo = narrative_repo
        self.llm = llm

    async def execute(self, project_id: int) -> dict:
        spec = await self.narrative_repo.get_by_project(project_id)
        if not spec:
            return {"error": "NarrativeSpec not found"}

        if not self.llm:
            return {"error": "LLM not configured"}

        fmt = StoryFormatRegistry.get_or_default(spec.core_idea.story_format)
        prompt = fmt.build_outline_prompt(spec)

        raw = await self.llm.generate(prompt=prompt)
        scenes_data = _safe_parse_json_array(raw)

        if not scenes_data:
            return {"error": "Failed to parse outline", "raw": raw}

        scenes = []
        for idx, item in enumerate(scenes_data):
            scenes.append(SceneSpec(
                order=idx,
                title=item.get("title", f"Scene {idx + 1}"),
                participants=item.get("participants", []),
                purpose=item.get("purpose", ""),
                emotional_state=item.get("emotional_state", ""),
            ))

        spec.scenes = scenes
        await self.narrative_repo.save(spec)

        return {"status": "outline generated", "scene_count": len(scenes)}


class GenerateSceneUseCase:
    """Generate content for a specific scene using the story format strategy."""

    def __init__(self, narrative_repo, llm):
        self.narrative_repo = narrative_repo
        self.llm = llm

    async def execute(self, project_id: int, scene_index: int, *, variants: int = 1) -> dict:
        spec = await self.narrative_repo.get_by_project(project_id)
        if not spec:
            return {"error": "NarrativeSpec not found"}

        if scene_index >= len(spec.scenes):
            return {"error": "Scene index out of range"}

        if not self.llm:
            return {"error": "LLM not configured"}

        fmt = StoryFormatRegistry.get_or_default(spec.core_idea.story_format)
        prompt = fmt.build_scene_prompt(spec, scene_index)

        results = []
        for _ in range(variants):
            content = await self.llm.generate(prompt=prompt)
            results.append(content)

        if variants == 1:
            scene = spec.scenes[scene_index]
            scene.content = results[0]
            await self.narrative_repo.update_scene_content(scene.id, results[0])
            return {"status": "scene generated", "content": results[0]}

        return {"status": "variants generated", "variants": results}


# --- helpers ---

def _safe_genre(val: Optional[str]) -> Genre:
    if val:
        try:
            return Genre(val)
        except ValueError:
            pass
    return Genre.LITERARY_FICTION


def _safe_role(val: Optional[str]) -> CharacterRole:
    if val:
        try:
            return CharacterRole(val)
        except ValueError:
            pass
    return CharacterRole.SUPPORTING


def _safe_macro(val: Optional[str]) -> MacroStructure:
    if val:
        try:
            return MacroStructure(val)
        except ValueError:
            pass
    return MacroStructure.THREE_ACT


def _safe_parse_json_array(raw: str) -> list[dict] | None:
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return None
