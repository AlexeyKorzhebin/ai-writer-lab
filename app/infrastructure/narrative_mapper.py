"""Mappers between NarrativeSpec ORM models and domain entities."""

from __future__ import annotations

from app.core.models import NarrativeSpecORM, CharacterORM, SceneORM
from app.domain.narrative import (
    NarrativeSpec, CoreIdea, WorldSpec, CharacterSpec, CharacterArc,
    Relationship, StructuralSpec, TurningPoint, SceneSpec,
    Genre, MacroStructure, CharacterRole,
)


def _safe_enum(enum_cls, value, default):
    try:
        return enum_cls(value)
    except (ValueError, KeyError):
        return default


def character_orm_to_domain(orm: CharacterORM) -> CharacterSpec:
    rels = []
    for r in (orm.relationships or []):
        rels.append(Relationship(
            target_name=r.get("target_name", ""),
            nature=r.get("nature", ""),
        ))

    return CharacterSpec(
        id=orm.id,
        name=orm.name,
        role=_safe_enum(CharacterRole, orm.role, CharacterRole.SUPPORTING),
        motivation=orm.motivation or "",
        fear=orm.fear or "",
        secret=orm.secret or "",
        relationships=rels,
        arc=CharacterArc(
            start_state=orm.arc_start_state or "",
            inner_conflict=orm.arc_inner_conflict or "",
            key_events=orm.arc_key_events or [],
            turning_point=orm.arc_turning_point or "",
            end_state=orm.arc_end_state or "",
        ),
    )


def scene_orm_to_domain(orm: SceneORM) -> SceneSpec:
    return SceneSpec(
        id=orm.id,
        order=orm.order,
        title=orm.title or "",
        participants=orm.participants or [],
        purpose=orm.purpose or "",
        emotional_state=orm.emotional_state or "",
        content=orm.content,
        summary=orm.summary,
    )


def narrative_orm_to_domain(orm: NarrativeSpecORM) -> NarrativeSpec:
    tps = []
    for tp in (orm.turning_points or []):
        tps.append(TurningPoint(
            name=tp.get("name", ""),
            description=tp.get("description", ""),
            position=tp.get("position", 0.0),
        ))

    return NarrativeSpec(
        id=orm.id,
        project_id=orm.project_id,
        version=orm.version,
        core_idea=CoreIdea(
            logline=orm.logline or "",
            genre=_safe_enum(Genre, orm.genre, Genre.LITERARY_FICTION),
            tone=orm.tone or "",
            themes=orm.themes or [],
            central_conflict=orm.central_conflict or "",
            story_format=orm.story_format or "",
        ),
        world=WorldSpec(
            world_type=orm.world_type or "realistic",
            rules=orm.world_rules or "",
            time_period=orm.world_time_period or "",
            power_structures=orm.world_power_structures or "",
            atmosphere=orm.world_atmosphere or "",
        ),
        characters=[character_orm_to_domain(c) for c in (orm.characters or [])],
        structure=StructuralSpec(
            macro_structure=_safe_enum(MacroStructure, orm.macro_structure, MacroStructure.THREE_ACT),
            turning_points=tps,
            climax=orm.climax or "",
            resolution=orm.resolution or "",
        ),
        scenes=[scene_orm_to_domain(s) for s in (orm.scenes or [])],
    )


def apply_domain_to_narrative_orm(domain: NarrativeSpec, orm: NarrativeSpecORM) -> None:
    orm.version = domain.version
    orm.logline = domain.core_idea.logline
    orm.genre = domain.core_idea.genre.value
    orm.tone = domain.core_idea.tone
    orm.themes = domain.core_idea.themes
    orm.central_conflict = domain.core_idea.central_conflict
    orm.story_format = domain.core_idea.story_format
    orm.world_type = domain.world.world_type
    orm.world_rules = domain.world.rules
    orm.world_time_period = domain.world.time_period
    orm.world_power_structures = domain.world.power_structures
    orm.world_atmosphere = domain.world.atmosphere
    orm.macro_structure = domain.structure.macro_structure.value
    orm.turning_points = [
        {"name": tp.name, "description": tp.description, "position": tp.position}
        for tp in domain.structure.turning_points
    ]
    orm.climax = domain.structure.climax
    orm.resolution = domain.structure.resolution


def domain_character_to_orm(ch: CharacterSpec, narrative_spec_id: int) -> CharacterORM:
    return CharacterORM(
        narrative_spec_id=narrative_spec_id,
        name=ch.name,
        role=ch.role.value,
        motivation=ch.motivation,
        fear=ch.fear,
        secret=ch.secret,
        relationships=[
            {"target_name": r.target_name, "nature": r.nature}
            for r in ch.relationships
        ],
        arc_start_state=ch.arc.start_state,
        arc_inner_conflict=ch.arc.inner_conflict,
        arc_key_events=ch.arc.key_events,
        arc_turning_point=ch.arc.turning_point,
        arc_end_state=ch.arc.end_state,
    )


def domain_scene_to_orm(scene: SceneSpec, narrative_spec_id: int) -> SceneORM:
    return SceneORM(
        narrative_spec_id=narrative_spec_id,
        order=scene.order,
        title=scene.title,
        participants=scene.participants,
        purpose=scene.purpose,
        emotional_state=scene.emotional_state,
        content=scene.content,
        summary=scene.summary,
    )
