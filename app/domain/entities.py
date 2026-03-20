from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AuthorProfile:
    name: Optional[str] = None
    style: Optional[str] = None


@dataclass
class ChapterEntity:
    id: Optional[int] = None
    project_id: Optional[int] = None
    title: str = ""
    content: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class ProjectEntity:
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[str] = None
    author: AuthorProfile = field(default_factory=AuthorProfile)
    chapters: list[ChapterEntity] = field(default_factory=list)

    @property
    def author_name(self) -> Optional[str]:
        return self.author.name

    @property
    def author_style(self) -> Optional[str]:
        return self.author.style
