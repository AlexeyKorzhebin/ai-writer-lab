from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.story_formats.base import StoryFormat

if TYPE_CHECKING:
    from app.domain.narrative import NarrativeSpec


class HeroJourney(StoryFormat):
    @property
    def name(self) -> str:
        return "Hero's Journey"

    @property
    def description(self) -> str:
        return "Campbell's monomyth: 12 stages of transformation"

    STAGES = [
        "Ordinary World",
        "Call to Adventure",
        "Refusal of the Call",
        "Meeting the Mentor",
        "Crossing the Threshold",
        "Tests, Allies, Enemies",
        "Approach to the Inmost Cave",
        "The Ordeal",
        "Reward",
        "The Road Back",
        "Resurrection",
        "Return with the Elixir",
    ]

    def build_outline_prompt(self, spec: NarrativeSpec) -> str:
        stages_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(self.STAGES))
        protagonist = spec.get_protagonist()
        hero_info = ""
        if protagonist:
            hero_info = (
                f"Hero: {protagonist.name}\n"
                f"Motivation: {protagonist.motivation}\n"
                f"Fear: {protagonist.fear}\n"
                f"Arc: {protagonist.arc.start_state} -> {protagonist.arc.end_state}\n"
            )

        return (
            f"Create a Hero's Journey outline.\n\n"
            f"Logline: {spec.core_idea.logline}\n"
            f"Genre: {spec.core_idea.genre.value}\n"
            f"Tone: {spec.core_idea.tone}\n"
            f"Central conflict: {spec.core_idea.central_conflict}\n\n"
            f"{hero_info}\n"
            f"{self._world_block(spec)}\n\n"
            f"{self._characters_block(spec)}\n\n"
            f"Follow the 12 stages of the Hero's Journey:\n{stages_text}\n\n"
            "Return ONLY valid JSON array of scenes (one per stage):\n"
            '[\n  {"title": "Scene title", "stage": "Stage name", '
            '"purpose": "...", "participants": ["name"], '
            '"emotional_state": "..."}\n]\n'
        )

    def build_scene_prompt(self, spec: NarrativeSpec, scene_index: int) -> str:
        if scene_index >= len(spec.scenes):
            return ""
        scene = spec.scenes[scene_index]
        stage = self.STAGES[scene_index] if scene_index < len(self.STAGES) else ""

        prev_summary = ""
        if scene_index > 0:
            prev = spec.scenes[scene_index - 1]
            prev_summary = f"\nPrevious stage: {prev.summary or prev.purpose}\n"

        protagonist = spec.get_protagonist()
        hero_context = ""
        if protagonist:
            hero_context = (
                f"\nHero: {protagonist.name}\n"
                f"Current inner state: evolving from '{protagonist.arc.start_state}' "
                f"toward '{protagonist.arc.end_state}'\n"
            )

        return (
            f"Write a scene for the Hero's Journey — stage: {stage}\n\n"
            f"Logline: {spec.core_idea.logline}\n"
            f"Tone: {spec.core_idea.tone}\n"
            f"{self._world_block(spec)}\n"
            f"{hero_context}\n"
            f"{self._characters_block(spec)}\n"
            f"{prev_summary}\n"
            f"Scene: {scene.title}\n"
            f"Purpose: {scene.purpose}\n"
            f"Participants: {', '.join(scene.participants)}\n"
            f"Emotional state: {scene.emotional_state}\n\n"
            f"This scene represents the '{stage}' stage. "
            "Show the hero's transformation at this point.\n"
        )

    def review_rules(self) -> str:
        return (
            "Review criteria for Hero's Journey:\n"
            "- Does the Ordinary World establish the hero's normal?\n"
            "- Is the Call to Adventure clear and compelling?\n"
            "- Is the Mentor figure well-defined?\n"
            "- Does the Ordeal test the hero at their core?\n"
            "- Is the transformation earned through trials?\n"
            "- Does the hero return changed?\n"
            "- Are all 12 stages present and meaningful?\n"
        )

    def consistency_rules(self) -> str:
        return (
            "Consistency rules for Hero's Journey:\n"
            "- Hero's character arc must progress through stages\n"
            "- Mentor's teachings must be relevant to the Ordeal\n"
            "- Allies/enemies established in stage 6 must appear in later stages\n"
            "- The Elixir must address the original need\n"
            "- World rules from Ordinary World apply in Special World\n"
        )

    def emotional_model(self) -> str:
        return (
            "Hero's Journey emotional curve:\n"
            "1. Comfort -> 2. Disruption -> 3. Fear -> 4. Hope (mentor)\n"
            "5. Excitement -> 6. Challenge -> 7. Dread -> 8. Crisis\n"
            "9. Triumph -> 10. Urgency -> 11. Rebirth -> 12. Wholeness\n"
        )
