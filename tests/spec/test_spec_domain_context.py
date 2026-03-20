"""Доменная логика AI_CHAT_AND_CONTEXT (ContextBuilder, @-ссылки) — см. SPEC_COVERAGE.md."""

import pytest

from app.core.context_builder import (
    ContextBuilder,
    estimate_tokens,
    parse_references,
    resolve_reference,
)
from app.domain.narrative import (
    CharacterRole,
    CharacterSpec,
    CoreIdea,
    Genre,
    MacroStructure,
    NarrativeSpec,
    SceneSpec,
    StructuralSpec,
    WorldSpec,
)


def _minimal_spec() -> NarrativeSpec:
    spec = NarrativeSpec(project_id=1)
    spec.core_idea = CoreIdea(
        logline="проба",
        genre=Genre.FANTASY,
        tone="сдержанный",
        central_conflict="борьба",
    )
    spec.world = WorldSpec(
        world_type="fantasy",
        time_period="древность",
        atmosphere="дождь",
        rules="одна магия",
    )
    spec.characters = [
        CharacterSpec(name="Анна", role=CharacterRole.PROTAGONIST, motivation="найти", fear="потерять"),
    ]
    spec.structure = StructuralSpec(macro_structure=MacroStructure.THREE_ACT, climax="пик", resolution="конец")
    spec.scenes = [
        SceneSpec(order=0, title="Начало", participants=["Анна"], content="Текст сцены ноль."),
        SceneSpec(order=1, title="Середина", participants=["Анна"], content="Продолжение."),
    ]
    return spec


@pytest.mark.spec
def test_parse_references_extracts_types():
    text = "Посмотри @scene:0 и @char:Анна, ещё @world и @plot"
    refs = parse_references(text)
    types = [t for t, _ in refs]
    assert "scene" in types
    assert "char" in types
    assert "world" in types
    assert "plot" in types


@pytest.mark.spec
def test_resolve_reference_scene_char_world_plot():
    spec = _minimal_spec()
    assert "Сцена 0" in resolve_reference("scene", "0", spec)
    assert "Анна" in resolve_reference("char", "Анна", spec)
    assert "fantasy" in resolve_reference("world", "", spec).lower()
    assert "проба" in resolve_reference("plot", "", spec)


@pytest.mark.spec
def test_resolve_reference_structure_and_style():
    spec = _minimal_spec()
    s = resolve_reference("structure", "", spec)
    assert "three_act" in s or "THREE" in s.upper()
    assert resolve_reference("style", "", spec) == "сдержанный"


@pytest.mark.spec
def test_resolve_reference_prev_and_all_chars():
    spec = _minimal_spec()
    prev = resolve_reference("prev", "", spec)
    assert "Середина" in prev or "Продолжение" in prev
    allc = resolve_reference("all-chars", "", spec)
    assert "Анна" in allc


@pytest.mark.spec
def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1


@pytest.mark.spec
def test_context_builder_budget_and_blocks():
    spec = _minimal_spec()
    ctx = ContextBuilder(max_tokens=16000)
    ctx.add_system_prompt(author_style="лаконично")
    ctx.add_auto_context(spec, scene_idx=0)
    ctx.add_user_message("Напиши продолжение")
    info = ctx.get_budget_info()
    assert info["max_tokens"] == 16000
    assert info["used_tokens"] > 0
    assert "blocks" in info
    names = {b["name"] for b in info["blocks"]}
    assert "user_message" in names
