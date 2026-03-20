from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.story_formats.base import StoryFormat

if TYPE_CHECKING:
    from app.domain.narrative import NarrativeSpec


class ThreeActNovel(StoryFormat):
    @property
    def name(self) -> str:
        return "Three-Act Novel"

    @property
    def description(self) -> str:
        return "Classic three-act structure: Setup, Confrontation, Resolution"

    def build_outline_prompt(self, spec: NarrativeSpec) -> str:
        return (
            f"Create a three-act novel outline.\n\n"
            f"Logline: {spec.core_idea.logline}\n"
            f"Genre: {spec.core_idea.genre.value}\n"
            f"Tone: {spec.core_idea.tone}\n"
            f"Central conflict: {spec.core_idea.central_conflict}\n"
            f"Themes: {', '.join(spec.core_idea.themes)}\n\n"
            f"{self._world_block(spec)}\n\n"
            f"{self._characters_block(spec)}\n\n"
            "Structure the outline in three acts:\n"
            "Act I (Setup ~25%): Introduce world, characters, inciting incident\n"
            "Act II (Confrontation ~50%): Rising action, midpoint reversal, escalation\n"
            "Act III (Resolution ~25%): Climax, falling action, resolution\n\n"
            "Return ONLY valid JSON array of scenes:\n"
            '[\n  {"title": "Scene title", "act": 1, "purpose": "...", '
            '"participants": ["name"], "emotional_state": "..."}\n]\n'
        )

    def build_scene_prompt(self, spec: NarrativeSpec, scene_index: int) -> str:
        if scene_index >= len(spec.scenes):
            return ""
        scene = spec.scenes[scene_index]

        prev_summary = ""
        if scene_index > 0:
            prev = spec.scenes[scene_index - 1]
            prev_summary = f"\nPrevious scene summary: {prev.summary or prev.purpose}\n"

        return (
            f"Write a detailed scene for the novel.\n\n"
            f"Logline: {spec.core_idea.logline}\n"
            f"Tone: {spec.core_idea.tone}\n"
            f"{self._world_block(spec)}\n"
            f"{self._characters_block(spec)}\n"
            f"{prev_summary}\n"
            f"Scene: {scene.title}\n"
            f"Purpose: {scene.purpose}\n"
            f"Participants: {', '.join(scene.participants)}\n"
            f"Emotional state: {scene.emotional_state}\n\n"
            "Write the full scene text. Maintain the established tone and style.\n"
        )

    def review_rules(self) -> str:
        return (
            "Review criteria for Three-Act Novel:\n"
            "- Does Act I establish the world and characters effectively?\n"
            "- Is there a clear inciting incident?\n"
            "- Does Act II escalate conflict with a midpoint reversal?\n"
            "- Is the climax earned and satisfying?\n"
            "- Does the resolution address the central conflict?\n"
            "- Are character arcs completed?\n"
            "- Is pacing appropriate (25/50/25 ratio)?\n"
        )

    def consistency_rules(self) -> str:
        return (
            "Consistency rules for Three-Act Novel:\n"
            "- Character motivations must remain coherent\n"
            "- World rules established in Act I must be respected\n"
            "- Foreshadowing in Act I should pay off in Act III\n"
            "- Emotional arc should follow tension curve\n"
            "- No unresolved subplots by the end\n"
        )

    def emotional_model(self) -> str:
        return (
            "Three-Act emotional curve:\n"
            "Act I: Curiosity -> Engagement -> Shock (inciting incident)\n"
            "Act II: Tension rising -> Hope at midpoint -> Despair at low point\n"
            "Act III: Determination -> Catharsis at climax -> Satisfaction\n"
        )
