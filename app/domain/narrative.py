"""
NarrativeSpec domain model — the structured description of a story
that drives all generation, review, and consistency operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Genre(str, Enum):
    LITERARY_FICTION = "literary_fiction"
    FANTASY = "fantasy"
    SCI_FI = "sci_fi"
    MYSTERY = "mystery"
    THRILLER = "thriller"
    ROMANCE = "romance"
    HORROR = "horror"
    HISTORICAL = "historical"
    NON_FICTION = "non_fiction"
    SHORT_STORY = "short_story"
    OTHER = "other"


class MacroStructure(str, Enum):
    THREE_ACT = "three_act"
    HERO_JOURNEY = "hero_journey"
    SHORT_STORY = "short_story"
    FIVE_ACT = "five_act"
    EPISODIC = "episodic"
    FRAME_NARRATIVE = "frame_narrative"


class CharacterRole(str, Enum):
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    MENTOR = "mentor"
    SIDEKICK = "sidekick"
    LOVE_INTEREST = "love_interest"
    SUPPORTING = "supporting"


@dataclass
class CoreIdea:
    logline: str = ""
    genre: Genre = Genre.LITERARY_FICTION
    tone: str = ""
    themes: list[str] = field(default_factory=list)
    central_conflict: str = ""
    story_format: str = ""


@dataclass
class WorldSpec:
    world_type: str = "realistic"
    rules: str = ""
    time_period: str = ""
    power_structures: str = ""
    atmosphere: str = ""
    geography_overview: str = ""
    cultural_notes: str = ""
    technology_level: str = ""
    languages: str = ""
    calendar: str = ""
    currency: str = ""
    religions: str = ""
    history_summary: str = ""
    races: str = ""


@dataclass
class CharacterArc:
    start_state: str = ""
    inner_conflict: str = ""
    key_events: list[str] = field(default_factory=list)
    turning_point: str = ""
    end_state: str = ""


@dataclass
class Relationship:
    target_name: str = ""
    nature: str = ""


@dataclass
class CharacterSpec:
    id: Optional[int] = None
    name: str = ""
    role: CharacterRole = CharacterRole.SUPPORTING
    motivation: str = ""
    fear: str = ""
    secret: str = ""
    relationships: list[Relationship] = field(default_factory=list)
    arc: CharacterArc = field(default_factory=CharacterArc)
    appearance: str = ""
    speech_style: str = ""


@dataclass
class TurningPoint:
    name: str = ""
    description: str = ""
    position: float = 0.0  # 0.0–1.0 relative position in the story


@dataclass
class StructuralSpec:
    macro_structure: MacroStructure = MacroStructure.THREE_ACT
    turning_points: list[TurningPoint] = field(default_factory=list)
    climax: str = ""
    resolution: str = ""


@dataclass
class TimeContext:
    time_of_day: str = ""
    season: str = ""
    weather: str = ""


@dataclass
class SceneSpec:
    id: Optional[int] = None
    order: int = 0
    title: str = ""
    participants: list[str] = field(default_factory=list)
    purpose: str = ""
    emotional_state: str = ""
    content: Optional[str] = None
    summary: Optional[str] = None
    location: str = ""
    time_context: Optional[TimeContext] = None


@dataclass
class LocationState:
    after_scene: int = 0
    description_override: str = ""
    change_reason: str = ""


@dataclass
class LocationSpec:
    id: Optional[int] = None
    name: str = ""
    location_type: str = "building"
    parent_id: Optional[int] = None
    description: str = ""
    visual_details: str = ""
    atmosphere: str = ""
    significance: str = ""
    climate: str = ""
    inhabitants: str = ""
    notable_features: str = ""
    connected_to: list[str] = field(default_factory=list)
    travel_notes: str = ""
    states: list[LocationState] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    first_appearance: Optional[int] = None


@dataclass
class NarrativeSpec:
    id: Optional[int] = None
    project_id: Optional[int] = None
    version: int = 1
    core_idea: CoreIdea = field(default_factory=CoreIdea)
    world: WorldSpec = field(default_factory=WorldSpec)
    characters: list[CharacterSpec] = field(default_factory=list)
    structure: StructuralSpec = field(default_factory=StructuralSpec)
    scenes: list[SceneSpec] = field(default_factory=list)

    def get_protagonist(self) -> Optional[CharacterSpec]:
        for c in self.characters:
            if c.role == CharacterRole.PROTAGONIST:
                return c
        return None

    def get_character_by_name(self, name: str) -> Optional[CharacterSpec]:
        for c in self.characters:
            if c.name.lower() == name.lower():
                return c
        return None
