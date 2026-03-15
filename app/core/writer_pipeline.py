class WriterPipeline:
    def __init__(self, llm):
        self.llm = llm

    def _build_author_context(self, project):
        if not project.author_name and not project.author_style:
            return ""
        return f"""
You are writing as {project.author_name or 'the author'}.
Writing style:
{project.author_style or 'Neutral professional tone.'}
"""

    async def generate_chapter(self, project, chapter):
        draft = await self._draft(project, chapter)
        refined = await self._refine(project, draft)
        summary = await self._summarize(refined)
        return refined, summary

    async def _draft(self, project, chapter):
        context = self._build_author_context(project)

        # Continuity: include summaries of previous chapters
        previous_context = ""
        if hasattr(project, 'chapters') and project.chapters:
            previous = [c for c in project.chapters if c.id != chapter.id]
            if previous:
                MAX_CONTEXT_CHARS = 2000
                collected = []
                total = 0

                # Include full previous chapter
                last_chapter = previous[-1]
                full_text = f"FULL PREVIOUS CHAPTER:\n{last_chapter.content or ''}\n"
                collected.append(full_text)
                total += len(full_text)

                # Include summaries of older chapters
                for c in reversed(previous[:-1]):
                    snippet = f"SUMMARY - {c.title}: {c.summary or ''}\n"
                    if total + len(snippet) > MAX_CONTEXT_CHARS:
                        break
                    collected.append(snippet)
                    total += len(snippet)

                previous_context = f"\nPrevious context:\n{''.join(collected)}\n"

        prompt = f"""
{context}
Book title: {project.title}
{previous_context}
Chapter title: {chapter.title}

Write a detailed draft of this chapter that maintains continuity with previous chapters.
"""
        return await self.llm.generate(prompt=prompt)

    async def _refine(self, project, draft_text):
        context = self._build_author_context(project)
        prompt = f"""
{context}
Refine the following draft into a more structured and coherent chapter.
Improve clarity, flow, and argument strength.

Draft:
{draft_text}
"""
        return await self.llm.generate(prompt=prompt)

    async def _summarize(self, text):
        prompt = f"""
Summarize the following chapter in 3-5 concise sentences.

{text}
"""
        return await self.llm.generate(prompt=prompt)

    async def generate_outline(self, project):
        prompt = f"""
Create a structured book outline for a book titled '{project.title}'.

Return ONLY valid JSON in the following format:
[
  {{
    "title": "Chapter title",
    "summary": "Short 2-3 sentence summary",
    "goals": ["Goal 1", "Goal 2"]
  }}
]
"""
        return await self.llm.generate(prompt=prompt)
