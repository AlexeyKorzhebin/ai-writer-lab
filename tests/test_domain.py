"""Unit tests for domain entities and story format strategies."""

import pytest

from app.domain.entities import ProjectEntity, ChapterEntity, AuthorProfile
from app.domain.narrative import (
    NarrativeSpec, CoreIdea, WorldSpec, CharacterSpec,
    CharacterArc, StructuralSpec, SceneSpec,
    Genre, MacroStructure, CharacterRole,
)
from app.domain.story_formats import StoryFormatRegistry, ThreeActNovel, ShortStory, HeroJourney


def test_project_entity():
    author = AuthorProfile(name="Test Author", style="Formal")
    project = ProjectEntity(
        id=1, title="Test", author=author,
        chapters=[ChapterEntity(id=1, title="Ch1")],
    )
    assert project.author_name == "Test Author"
    assert project.author_style == "Formal"
    assert len(project.chapters) == 1


def test_narrative_spec():
    spec = NarrativeSpec(
        project_id=1,
        core_idea=CoreIdea(logline="Test", genre=Genre.FANTASY),
        characters=[
            CharacterSpec(name="Hero", role=CharacterRole.PROTAGONIST),
            CharacterSpec(name="Villain", role=CharacterRole.ANTAGONIST),
        ],
    )
    assert spec.get_protagonist().name == "Hero"
    assert spec.get_character_by_name("villain").role == CharacterRole.ANTAGONIST
    assert spec.get_character_by_name("nonexistent") is None


def test_story_format_registry():
    formats = StoryFormatRegistry.list_formats()
    assert len(formats) >= 3

    three_act = StoryFormatRegistry.get("three_act")
    assert isinstance(three_act, ThreeActNovel)

    default = StoryFormatRegistry.get_or_default(None)
    assert isinstance(default, ThreeActNovel)

    hero = StoryFormatRegistry.get("hero_journey")
    assert isinstance(hero, HeroJourney)


def test_three_act_prompts():
    spec = NarrativeSpec(
        core_idea=CoreIdea(
            logline="A test story",
            genre=Genre.FANTASY,
            tone="Epic",
            themes=["Courage"],
            central_conflict="Good vs evil",
        ),
        world=WorldSpec(world_type="fantasy", atmosphere="Dark"),
        characters=[CharacterSpec(name="Hero", role=CharacterRole.PROTAGONIST, motivation="Save all")],
        scenes=[SceneSpec(title="Opening", purpose="Setup")],
    )

    fmt = ThreeActNovel()
    outline_prompt = fmt.build_outline_prompt(spec)
    assert "three-act" in outline_prompt.lower()
    assert "A test story" in outline_prompt

    scene_prompt = fmt.build_scene_prompt(spec, 0)
    assert "Opening" in scene_prompt

    assert "Act I" in fmt.review_rules()
    assert "Character" in fmt.consistency_rules()


def test_hero_journey_stages():
    hero = HeroJourney()
    assert len(hero.STAGES) == 12
    assert "Ordinary World" in hero.STAGES
    assert "Return with the Elixir" in hero.STAGES
