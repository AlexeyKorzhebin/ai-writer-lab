from app.core.agents.reviewer import ReviewAgent


class ReviewChapterUseCase:
    def __init__(self, chapter_repository, llm):
        self.chapter_repository = chapter_repository
        self.llm = llm

    async def execute(self, chapter_id: int):
        chapter = await self.chapter_repository.get_with_project(chapter_id)

        if not chapter:
            return {"error": "Chapter not found"}

        if not self.llm:
            return {"error": "LLM not configured"}

        reviewer = ReviewAgent(self.llm)
        review = await reviewer.review_chapter(chapter.project, chapter)

        return {"review": review}
