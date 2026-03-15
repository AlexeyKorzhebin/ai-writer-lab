from app.core.writer_pipeline import WriterPipeline


class GenerateChapterUseCase:
    def __init__(self, chapter_repository, llm):
        self.chapter_repository = chapter_repository
        self.llm = llm

    async def execute(self, chapter_id: int):
        chapter = await self.chapter_repository.get_with_project(chapter_id)

        if not chapter:
            return {"error": "Chapter not found"}

        if not self.llm:
            chapter.content = "LLM not configured"
            await self.chapter_repository.save(chapter)
            return {"status": "ok"}

        pipeline = WriterPipeline(self.llm)
        content, summary = await pipeline.generate_chapter(
            chapter.project,
            chapter,
        )

        chapter.content = content
        chapter.summary = summary

        await self.chapter_repository.save(chapter)

        return {"status": "ok"}
