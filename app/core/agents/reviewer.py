import json
import re


class ReviewAgent:
    def __init__(self, llm):
        self.llm = llm

    async def review_chapter(self, project, chapter):
        prompt = f"""
You are a professional book editor.

Evaluate the following chapter.

Book title: {project.title}
Author style: {project.author_style or 'Neutral professional tone'}
Chapter title: {chapter.title}

Chapter content:
{chapter.content}

Return ONLY valid JSON in the following format:
{{
  "score": 0-10,
  "major_issues": true or false,
  "feedback": "detailed markdown feedback"
}}

Do not include explanations outside JSON.
Do not include markdown formatting outside JSON.
"""
        raw = await self.llm.generate(prompt=prompt)

        data = self._safe_parse(raw)
        return data

    def _safe_parse(self, raw_text: str):
        # First attempt: direct JSON parse
        try:
            data = json.loads(raw_text)
        except Exception:
            # Try to extract JSON object via regex
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
                "score": 5,
                "major_issues": True,
                "feedback": raw_text
            }

        # Normalize score
        score = data.get("score", 5)
        try:
            score = int(score)
        except Exception:
            score = 5
        score = max(0, min(10, score))

        # Normalize major_issues
        major = data.get("major_issues", True)
        if isinstance(major, str):
            major = major.lower() in ["true", "1", "yes"]
        major = bool(major)

        feedback = data.get("feedback", "")

        return {
            "score": score,
            "major_issues": major,
            "feedback": feedback
        }
