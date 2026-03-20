from app.core.writer_pipeline import WriterPipeline
from app.core.memory import MemoryService


class GenerateChapterUseCase:
    def __init__(self, chapter_repository, llm, db_session=None):
        self.chapter_repository = chapter_repository
        self.llm = llm
        self.db_session = db_session

    async def execute(self, chapter_id: int):
        chapter = await self.chapter_repository.get_with_project(chapter_id)

        if not chapter:
            return {"error": "Chapter not found"}

        if not self.llm:
            chapter.content = "LLM not configured"
            await self.chapter_repository.save(chapter)
            return {"status": "ok"}

        memory = MemoryService(self.db_session) if self.db_session else None
        pipeline = WriterPipeline(self.llm, memory=memory)

        content, summary = await pipeline.generate_chapter(
            chapter.project,
            chapter,
        )

        chapter.content = content
        chapter.summary = summary

        await self.chapter_repository.save(chapter)
        await self.chapter_repository.save_version(chapter)

        if memory:
            await memory.index_chapter(chapter)

        return {"status": "ok"}
