"""
Character Consistency Agent — verifies that character behavior
in scenes matches their defined arcs from the NarrativeSpec.
"""

import json
import re
import logging

logger = logging.getLogger(__name__)


class CharacterConsistencyAgent:
    def __init__(self, llm):
        self.llm = llm

    async def check_scene(self, character_spec, scene_content: str, scene_title: str) -> dict:
        """Check a single scene for character consistency."""
        arc_description = ""
        if character_spec.arc:
            arc_description = (
                f"Character arc:\n"
                f"  Start: {character_spec.arc.start_state}\n"
                f"  Inner conflict: {character_spec.arc.inner_conflict}\n"
                f"  Turning point: {character_spec.arc.turning_point}\n"
                f"  End: {character_spec.arc.end_state}\n"
            )

        prompt = (
            f"You are a narrative consistency editor.\n\n"
            f"Character: {character_spec.name}\n"
            f"Role: {character_spec.role.value}\n"
            f"Motivation: {character_spec.motivation}\n"
            f"Fear: {character_spec.fear}\n"
            f"{arc_description}\n"
            f"Scene: {scene_title}\n"
            f"Scene content:\n{scene_content}\n\n"
            "Analyze whether this character's behavior in the scene is consistent "
            "with their defined personality and arc. Return ONLY valid JSON:\n"
            '{\n'
            '  "consistent": true/false,\n'
            '  "score": 0-10,\n'
            '  "issues": ["issue 1", "issue 2"],\n'
            '  "suggestions": "improvement suggestions"\n'
            '}\n'
        )

        raw = await self.llm.generate(prompt=prompt)
        return self._safe_parse(raw)

    async def check_full_story(self, narrative_spec) -> dict:
        """Check character consistency across all scenes with content."""
        results = []

        for char in narrative_spec.characters:
            for scene in narrative_spec.scenes:
                if not scene.content:
                    continue
                if char.name.lower() not in [p.lower() for p in scene.participants]:
                    continue

                check = await self.check_scene(char, scene.content, scene.title)
                results.append({
                    "character": char.name,
                    "scene": scene.title,
                    "scene_index": scene.order,
                    **check,
                })

        inconsistent = [r for r in results if not r.get("consistent", True)]
        avg_score = sum(r.get("score", 5) for r in results) / max(len(results), 1)

        return {
            "total_checks": len(results),
            "inconsistent_count": len(inconsistent),
            "average_score": round(avg_score, 1),
            "details": results,
        }

    def _safe_parse(self, raw_text: str) -> dict:
        try:
            data = json.loads(raw_text)
        except Exception:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    data = None
            else:
                data = None

        if not isinstance(data, dict):
            return {
                "consistent": True,
                "score": 5,
                "issues": [],
                "suggestions": raw_text,
            }

        return {
            "consistent": bool(data.get("consistent", True)),
            "score": max(0, min(10, int(data.get("score", 5)))),
            "issues": data.get("issues", []),
            "suggestions": data.get("suggestions", ""),
        }
