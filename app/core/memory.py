"""
Long-term book memory using SQLite FTS5 for relevant context retrieval.

Uses a virtual FTS5 table that mirrors chapter content/summaries.
Provides ranked search so the WriterPipeline can pull in the most
relevant fragments from the entire book, not just the previous chapter.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


FTS_TABLE = "chapters_fts"

CREATE_FTS = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE}
USING fts5(chapter_id, title, content, summary, tokenize='unicode61');
"""

UPSERT_FTS = f"""
INSERT OR REPLACE INTO {FTS_TABLE}(rowid, chapter_id, title, content, summary)
VALUES (:rowid, :chapter_id, :title, :content, :summary);
"""

SEARCH_FTS = f"""
SELECT chapter_id, title, snippet({FTS_TABLE}, 2, '<b>', '</b>', '...', 60) AS snippet,
       rank
FROM {FTS_TABLE}
WHERE {FTS_TABLE} MATCH :query
ORDER BY rank
LIMIT :limit;
"""

DELETE_FTS = f"""
DELETE FROM {FTS_TABLE} WHERE chapter_id = :chapter_id;
"""


class MemoryService:
    """Provides retrieval-augmented context from the full book."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_fts_table(self) -> None:
        await self.db.execute(text(CREATE_FTS))
        await self.db.commit()

    async def index_chapter(self, chapter) -> None:
        """Index or update a chapter in FTS."""
        await self.ensure_fts_table()
        await self.db.execute(text(DELETE_FTS), {"chapter_id": chapter.id})
        await self.db.execute(text(UPSERT_FTS), {
            "rowid": chapter.id,
            "chapter_id": chapter.id,
            "title": chapter.title or "",
            "content": chapter.content or "",
            "summary": chapter.summary or "",
        })
        await self.db.commit()

    async def index_all_chapters(self, chapters) -> None:
        await self.ensure_fts_table()
        for ch in chapters:
            await self.db.execute(text(DELETE_FTS), {"chapter_id": ch.id})
            await self.db.execute(text(UPSERT_FTS), {
                "rowid": ch.id,
                "chapter_id": ch.id,
                "title": ch.title or "",
                "content": ch.content or "",
                "summary": ch.summary or "",
            })
        await self.db.commit()

    async def search(self, query: str, *, limit: int = 5, exclude_chapter_id: int | None = None) -> list[dict]:
        """Search for relevant context across the entire book."""
        await self.ensure_fts_table()

        safe_query = " ".join(
            token for token in query.split()
            if token and not token.startswith(("-", "NOT"))
        )
        if not safe_query:
            return []

        try:
            result = await self.db.execute(
                text(SEARCH_FTS),
                {"query": safe_query, "limit": limit + 2},
            )
            rows = result.fetchall()
        except Exception:
            return []

        results = []
        for row in rows:
            if exclude_chapter_id and row.chapter_id == exclude_chapter_id:
                continue
            results.append({
                "chapter_id": row.chapter_id,
                "title": row.title,
                "snippet": row.snippet,
            })
            if len(results) >= limit:
                break
        return results

    async def build_context(
        self,
        query: str,
        *,
        exclude_chapter_id: int | None = None,
        max_chars: int = 2000,
    ) -> str:
        """Build a context string from relevant fragments."""
        results = await self.search(query, limit=5, exclude_chapter_id=exclude_chapter_id)
        if not results:
            return ""

        parts = []
        total = 0
        for r in results:
            snippet_text = f"[{r['title']}]: {r['snippet']}"
            if total + len(snippet_text) > max_chars:
                break
            parts.append(snippet_text)
            total += len(snippet_text)

        if not parts:
            return ""
        return "Relevant context from the book:\n" + "\n".join(parts)
