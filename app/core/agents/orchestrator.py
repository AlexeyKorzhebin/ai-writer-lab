import logging
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    def __init__(self, llm, writer_pipeline, reviewer, editor):
        self.llm = llm
        self.writer_pipeline = writer_pipeline
        self.reviewer = reviewer
        self.editor = editor

    async def produce_high_quality_chapter(
        self,
        project,
        chapter,
        max_iterations: Optional[int] = None,
        min_score: Optional[int] = None,
    ):
        settings = get_settings()
        if max_iterations is None:
            max_iterations = getattr(project, "max_iterations", None) or settings.max_orchestrator_iterations
        if min_score is None:
            min_score = settings.orchestrator_min_score

        iterations = 0
        iteration_log: list[dict] = []

        if not chapter.content:
            logger.info("Chapter %s is empty, generating initial draft", chapter.id)
            content, summary = await self.writer_pipeline.generate_chapter(project, chapter)
            chapter.content = content
            chapter.summary = summary

        current_text = chapter.content
        final_score = 0

        while iterations < max_iterations:
            logger.info("Iteration %d/%d for chapter %s", iterations + 1, max_iterations, chapter.id)

            review = await self.reviewer.review_chapter(project, chapter)
            final_score = review.get("score", 5)
            major_issues = review.get("major_issues", True)

            iteration_log.append({
                "iteration": iterations + 1,
                "score": final_score,
                "major_issues": major_issues,
                "action": "stop" if (final_score >= min_score and not major_issues) else "edit",
            })

            logger.info(
                "Review result: score=%d, major_issues=%s",
                final_score, major_issues,
            )

            if final_score >= min_score and not major_issues:
                logger.info("Quality threshold met, stopping")
                break

            improved = await self.editor.apply_improvements(
                project, chapter, review.get("feedback", "")
            )

            if not improved or len(improved) < len(current_text) * 0.5:
                logger.warning("Edit degraded content, stopping for safety")
                iteration_log[-1]["action"] = "safety_stop"
                break

            chapter.content = improved
            current_text = improved
            iterations += 1

        return {
            "content": chapter.content,
            "iterations": iterations,
            "final_score": final_score,
            "iteration_log": iteration_log,
        }
