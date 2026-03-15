class BookRewriteOrchestrator:
    """
    Controlled execution of book-level improvement plan.
    V1: Single-pass rewrite for affected chapters only.
    """

    def __init__(self, chapter_orchestrator):
        self.chapter_orchestrator = chapter_orchestrator

    async def execute_plan(self, project, chapters, plan):
        actions = plan.get("actions", [])

        # Group actions by chapter
        chapter_map = {}
        for action in actions:
            chapter_id = action.get("chapter")
            if chapter_id is None:
                continue
            chapter_map.setdefault(chapter_id, []).append(action)

        results = []

        for chapter in chapters:
            # Chapter numbering assumed 1-based index order
            chapter_index = chapters.index(chapter) + 1

            if chapter_index not in chapter_map:
                continue

            # Build combined instruction
            instructions = "\n".join([
                f"- {a.get('type')}: {a.get('description')}"
                for a in chapter_map[chapter_index]
            ])

            # Inject instructions as temporary review feedback
            fake_review = {
                "score": 5,
                "major_issues": True,
                "feedback": f"Apply the following book-level improvements:\n{instructions}"
            }

            # Use chapter-level orchestrator (single iteration pass)
            result = await self.chapter_orchestrator.produce_high_quality_chapter(
                project,
                chapter,
                max_iterations=1
            )

            results.append({
                "chapter": chapter_index,
                "final_score": result.get("final_score"),
                "iterations": result.get("iterations")
            })

        return {
            "chapters_updated": len(results),
            "details": results
        }
