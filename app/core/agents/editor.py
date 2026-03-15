class EditorAgent:
    def __init__(self, llm):
        self.llm = llm

    async def apply_improvements(self, project, chapter, review_text):
        prompt = f"""
You are a professional book editor.

Book title: {project.title}
Author style: {project.author_style or 'Neutral professional tone'}

Original chapter:
{chapter.content}

Editor review feedback:
{review_text}

Rewrite the chapter applying the suggested improvements.
Keep the author's tone consistent.
Return only the improved chapter text.
"""
        return await self.llm.generate(prompt=prompt)
