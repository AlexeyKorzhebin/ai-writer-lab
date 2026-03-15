import json
import re


class ConsistencyAgent:
    def __init__(self, llm):
        self.llm = llm

    async def analyze_book(self, project, chapters):
        summaries_block = "\n".join([
            f"Chapter {idx+1}: {c.title}\nSummary: {c.summary or ''}\n"
            for idx, c in enumerate(chapters)
        ])

        prompt = f"""
You are a senior book editor responsible for global consistency.

Book title: {project.title}
Author style: {project.author_style or 'Neutral professional tone'}

Below are chapter summaries:

{summaries_block}

Return ONLY valid JSON in the following format:
{{
  "global_score": 0-10,
  "inconsistencies": [{{"chapter": number, "description": "text"}}],
  "redundancies": [{{"chapter": number, "description": "text"}}],
  "missing_links": [{{"chapter": number, "description": "text"}}],
  "recommendations": "detailed improvement plan"
}}

Do not include explanations outside JSON.
"""
        raw = await self.llm.generate(prompt=prompt)
        return self._safe_parse(raw)

    def _safe_parse(self, raw_text: str):
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
                "global_score": 5,
                "inconsistencies": [],
                "redundancies": [],
                "missing_links": [],
                "recommendations": raw_text
            }

        score = data.get("global_score", 5)
        try:
            score = int(score)
        except Exception:
            score = 5
        score = max(0, min(10, score))

        return {
            "global_score": score,
            "inconsistencies": data.get("inconsistencies", []),
            "redundancies": data.get("redundancies", []),
            "missing_links": data.get("missing_links", []),
            "recommendations": data.get("recommendations", "")
        }
