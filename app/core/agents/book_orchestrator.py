class BookOrchestrator:
    """
    Coordinates book-level improvement based on ConsistencyAgent analysis.
    V1: Generates improvement plan only (no automatic rewriting).
    """

    def __init__(self, consistency_agent):
        self.consistency_agent = consistency_agent

    async def produce_book_improvement_plan(self, project, chapters):
        analysis = await self.consistency_agent.analyze_book(project, chapters)

        plan = {
            "global_score": analysis.get("global_score"),
            "actions": []
        }

        for issue in analysis.get("inconsistencies", []):
            plan["actions"].append({
                "type": "fix_inconsistency",
                "chapter": issue.get("chapter"),
                "description": issue.get("description")
            })

        for issue in analysis.get("redundancies", []):
            plan["actions"].append({
                "type": "reduce_redundancy",
                "chapter": issue.get("chapter"),
                "description": issue.get("description")
            })

        for issue in analysis.get("missing_links", []):
            plan["actions"].append({
                "type": "add_link",
                "chapter": issue.get("chapter"),
                "description": issue.get("description")
            })

        plan["recommendations"] = analysis.get("recommendations")

        return plan
