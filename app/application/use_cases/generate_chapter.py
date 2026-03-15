from app.core.writer_pipeline import WriterPipeline


class GenerateChapterUseCase:
    def __init__(self, chapter_repository, llm):
        self.chapter_repository = chapter_repository
        self.llm = llm

    async def execute(self, chapter_id: int):
        result = await self.chapter_repository.get_with_project(chapter_id)

        if not result:
            return {"error": "Chapter not found"}

        chapter_entity, orm_chapter = result

        if not self.llm:
            orm_chapter.content = "LLM not configured"
            await self.chapter_repository.save(orm_chapter)
            return {"status": "ok"}

        pipeline = WriterPipeline(self.llm)

        # Temporary: pipeline still operates on ORM objects
        content, summary = await pipeline.generate_chapter(
            orm_chapter.project,
            orm_chapter,
        )

        # Update domain entity
        chapter_entity.content = content
        chapter_entity.summary = summary

        # Update ORM for persistence
        orm_chapter.content = content
        orm_chapter.summary = summary

        await self.chapter_repository.save(orm_chapter)

        return {"status": "ok"}
