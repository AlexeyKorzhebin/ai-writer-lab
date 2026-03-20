from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.story_formats.base import StoryFormat

if TYPE_CHECKING:
    from app.domain.narrative import NarrativeSpec


class ShortStory(StoryFormat):
    @property
    def name(self) -> str:
        return "Short Story"

    @property
    def description(self) -> str:
        return "Compressed narrative with a single focus and one twist"

    def build_outline_prompt(self, spec: NarrativeSpec) -> str:
        return (
            f"Create a short story outline (3-7 scenes).\n\n"
            f"Logline: {spec.core_idea.logline}\n"
            f"Genre: {spec.core_idea.genre.value}\n"
            f"Tone: {spec.core_idea.tone}\n"
            f"Central conflict: {spec.core_idea.central_conflict}\n\n"
            f"{self._world_block(spec)}\n\n"
            f"{self._characters_block(spec)}\n\n"
            "A short story should have:\n"
            "- Immediate hook\n"
            "- Single focused conflict\n"
            "- Rising tension leading to one twist/revelation\n"
            "- Compact resolution\n\n"
            "Return ONLY valid JSON array of scenes:\n"
            '[\n  {"title": "Scene title", "purpose": "...", '
            '"participants": ["name"], "emotional_state": "..."}\n]\n'
        )

    def build_scene_prompt(self, spec: NarrativeSpec, scene_index: int) -> str:
        if scene_index >= len(spec.scenes):
            return ""
        scene = spec.scenes[scene_index]

        prev_summary = ""
        if scene_index > 0:
            prev = spec.scenes[scene_index - 1]
            prev_summary = f"\nPrevious scene: {prev.summary or prev.purpose}\n"

        return (
            f"Write a scene for a short story.\n\n"
            f"Logline: {spec.core_idea.logline}\n"
            f"Tone: {spec.core_idea.tone}\n"
            f"{self._world_block(spec)}\n"
            f"{self._characters_block(spec)}\n"
            f"{prev_summary}\n"
            f"Scene: {scene.title}\n"
            f"Purpose: {scene.purpose}\n"
            f"Participants: {', '.join(scene.participants)}\n"
            f"Emotional state: {scene.emotional_state}\n\n"
            "Keep it tight and focused. Every sentence should advance "
            "the plot or deepen character.\n"
        )

    def review_rules(self) -> str:
        return (
            "Review criteria for Short Story:\n"
            "- Is the hook immediate and compelling?\n"
            "- Is the conflict singular and focused?\n"
            "- Is there a clear twist or revelation?\n"
            "- Is every sentence essential?\n"
            "- Does the ending resonate?\n"
        )

    def consistency_rules(self) -> str:
        return (
            "Consistency rules for Short Story:\n"
            "- Limited cast of characters (2-4)\n"
            "- Single timeline preferred\n"
            "- No extraneous subplots\n"
            "- Tight thematic unity\n"
        )

    def emotional_model(self) -> str:
        return (
            "Short Story emotional curve:\n"
            "Hook -> Building tension -> Revelation/Twist -> Resonant ending\n"
        )
