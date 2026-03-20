"""Chat domain models for AI Co-Author functionality."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Reference:
    ref_type: str  # scene, char, world, location, plot, structure, chapter, prev, selection, style, review, all-chars, timeline
    ref_key: str  # e.g. scene number, character name, etc.
    content: str = ""
    tokens: int = 0


@dataclass
class ChatMessage:
    role: str  # user, assistant, system
    content: str
    references: list[Reference] = field(default_factory=list)
    tokens: int = 0
    created_at: Optional[datetime] = None


@dataclass
class ChatSession:
    id: Optional[int] = None
    project_id: int = 0
    task_name: str = "Общий чат"
    messages: list[ChatMessage] = field(default_factory=list)
    pinned_context: list[Reference] = field(default_factory=list)
    created_at: Optional[datetime] = None
