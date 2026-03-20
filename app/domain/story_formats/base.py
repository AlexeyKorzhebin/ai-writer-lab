"""Abstract base for story format strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.narrative import NarrativeSpec


class StoryFormat(ABC):
    """
    A story format defines the narrative rules for a specific genre/structure.
    It provides prompt templates, review criteria, and consistency rules
    that adapt generation and evaluation to the chosen format.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def build_outline_prompt(self, spec: NarrativeSpec) -> str:
        """Build a prompt for generating the story outline."""
        ...

    @abstractmethod
    def build_scene_prompt(self, spec: NarrativeSpec, scene_index: int) -> str:
        """Build a prompt for generating a specific scene."""
        ...

    @abstractmethod
    def review_rules(self) -> str:
        """Return review criteria specific to this format."""
        ...

    @abstractmethod
    def consistency_rules(self) -> str:
        """Return consistency checking rules specific to this format."""
        ...

    @abstractmethod
    def emotional_model(self) -> str:
        """Describe the expected emotional arc for this format."""
        ...

    def _characters_block(self, spec: NarrativeSpec) -> str:
        if not spec.characters:
            return ""
        lines = ["Characters:"]
        for ch in spec.characters:
            lines.append(f"- {ch.name} ({ch.role.value}): {ch.motivation}")
            if ch.arc.start_state:
                lines.append(f"  Arc: {ch.arc.start_state} -> {ch.arc.end_state}")
        return "\n".join(lines)

    def _world_block(self, spec: NarrativeSpec) -> str:
        w = spec.world
        parts = [f"World: {w.world_type}"]
        if w.time_period:
            parts.append(f"Time: {w.time_period}")
        if w.atmosphere:
            parts.append(f"Atmosphere: {w.atmosphere}")
        if w.rules:
            parts.append(f"Rules: {w.rules}")
        return "\n".join(parts)
