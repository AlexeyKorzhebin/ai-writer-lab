class OrchestratorAgent:
    def __init__(self, llm, writer_pipeline, reviewer, editor):
        self.llm = llm
        self.writer_pipeline = writer_pipeline
        self.reviewer = reviewer
        self.editor = editor

    async def produce_high_quality_chapter(self, project, chapter, max_iterations=3):
        iterations = 0

        # Initial generation if empty
        if not chapter.content:
            content, summary = await self.writer_pipeline.generate_chapter(project, chapter)
            chapter.content = content
            chapter.summary = summary

        current_text = chapter.content
        final_score = 0

        while iterations < max_iterations:
            review = await self.reviewer.review_chapter(project, chapter)
            final_score = review.get("score", 5)
            major_issues = review.get("major_issues", True)

            if final_score >= 8 and not major_issues:
                break

            improved = await self.editor.apply_improvements(project, chapter, review.get("feedback", ""))

            # Safety: avoid degrading too much
            if not improved or len(improved) < len(current_text) * 0.5:
                break

            chapter.content = improved
            current_text = improved

            iterations += 1

        return {
            "content": chapter.content,
            "iterations": iterations,
            "final_score": final_score
        }
