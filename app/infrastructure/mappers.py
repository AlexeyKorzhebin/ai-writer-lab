from __future__ import annotations

from app.core.models import Project, Chapter
from app.domain.entities import ProjectEntity, ChapterEntity, AuthorProfile


def chapter_to_entity(orm: Chapter) -> ChapterEntity:
    return ChapterEntity(
        id=orm.id,
        project_id=orm.project_id,
        title=orm.title,
        content=orm.content,
        summary=orm.summary,
    )


def project_to_entity(orm: Project, *, with_chapters: bool = True) -> ProjectEntity:
    chapters = []
    if with_chapters and orm.chapters:
        chapters = [chapter_to_entity(c) for c in orm.chapters]

    return ProjectEntity(
        id=orm.id,
        title=orm.title,
        description=orm.description,
        model_name=orm.model_name,
        temperature=orm.temperature,
        max_tokens=orm.max_tokens,
        author=AuthorProfile(name=orm.author_name, style=orm.author_style),
        chapters=chapters,
    )


