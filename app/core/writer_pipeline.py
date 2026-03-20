from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.memory import MemoryService


class WriterPipeline:
    def __init__(self, llm, *, memory: "MemoryService | None" = None):
        self.llm = llm
        self.memory = memory

    def _build_author_context(self, project):
        if not project.author_name and not project.author_style:
            return ""
        return (
            f"You are writing as {project.author_name or 'the author'}.\n"
            f"Writing style:\n{project.author_style or 'Neutral professional tone.'}\n"
        )

    async def generate_chapter(self, project, chapter):
        draft = await self._draft(project, chapter)
        refined = await self._refine(project, draft)
        summary = await self._summarize(refined)
        return refined, summary

    async def _draft(self, project, chapter):
        context = self._build_author_context(project)

        previous_context = ""
        if hasattr(project, "chapters") and project.chapters:
            previous = [c for c in project.chapters if c.id != chapter.id]
            if previous:
                MAX_CONTEXT_CHARS = 2000
                collected = []
                total = 0

                last_chapter = previous[-1]
                full_text = f"FULL PREVIOUS CHAPTER:\n{last_chapter.content or ''}\n"
                collected.append(full_text)
                total += len(full_text)

                for c in reversed(previous[:-1]):
                    snippet = f"SUMMARY - {c.title}: {c.summary or ''}\n"
                    if total + len(snippet) > MAX_CONTEXT_CHARS:
                        break
                    collected.append(snippet)
                    total += len(snippet)

                previous_context = f"\nPrevious context:\n{''.join(collected)}\n"

        memory_context = ""
        if self.memory:
            query = f"{chapter.title} {project.title}"
            memory_context = await self.memory.build_context(
                query,
                exclude_chapter_id=chapter.id,
                max_chars=1500,
            )
            if memory_context:
                memory_context = f"\n{memory_context}\n"

        prompt = (
            f"{context}"
            f"Book title: {project.title}\n"
            f"{previous_context}"
            f"{memory_context}"
            f"Chapter title: {chapter.title}\n\n"
            "Write a detailed draft of this chapter that maintains "
            "continuity with previous chapters.\n"
        )
        return await self.llm.generate(prompt=prompt)

    async def _refine(self, project, draft_text):
        context = self._build_author_context(project)
        prompt = (
            f"{context}"
            "Refine the following draft into a more structured and coherent chapter.\n"
            "Improve clarity, flow, and argument strength.\n\n"
            f"Draft:\n{draft_text}\n"
        )
        return await self.llm.generate(prompt=prompt)

    async def _summarize(self, text):
        prompt = f"Summarize the following chapter in 3-5 concise sentences.\n\n{text}\n"
        return await self.llm.generate(prompt=prompt)

    async def generate_outline(self, project):
        prompt = (
            f"Create a structured book outline for a book titled '{project.title}'.\n\n"
            "Return ONLY valid JSON in the following format:\n"
            "[\n"
            '  {\n    "title": "Chapter title",\n'
            '    "summary": "Short 2-3 sentence summary",\n'
            '    "goals": ["Goal 1", "Goal 2"]\n  }\n'
            "]\n"
        )
        return await self.llm.generate(prompt=prompt)
