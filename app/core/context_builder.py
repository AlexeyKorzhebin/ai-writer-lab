"""Context builder for AI Chat — manages token budget and @-references."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from app.domain.narrative import NarrativeSpec, SceneSpec


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for mixed content."""
    return len(text) // 4 if text else 0


@dataclass
class ContextBlock:
    name: str
    content: str
    tokens: int = 0
    priority: int = 0  # higher = more important

    def __post_init__(self):
        if not self.tokens:
            self.tokens = estimate_tokens(self.content)


REFERENCE_PATTERN = re.compile(r'@(scene|char|world|location|plot|structure|chapter|prev|selection|style|review|all-chars|timeline)(?::([^\s,]+))?')


def parse_references(text: str) -> list[tuple[str, str]]:
    """Extract @-references from user message. Returns list of (type, key) tuples."""
    return [(m.group(1), m.group(2) or '') for m in REFERENCE_PATTERN.finditer(text)]


class ContextBuilder:
    """Assembles context for the LLM chat within a token budget."""

    def __init__(self, max_tokens: int = 16000):
        self.max_tokens = max_tokens
        self.blocks: list[ContextBlock] = []

    @property
    def used_tokens(self) -> int:
        return sum(b.tokens for b in self.blocks)

    @property
    def remaining(self) -> int:
        return max(0, self.max_tokens - self.used_tokens)

    @property
    def usage_pct(self) -> float:
        return self.used_tokens / self.max_tokens if self.max_tokens else 0

    def add_system_prompt(self, author_style: str = "", language: str = "ru") -> None:
        prompt = f"""Ты — AI-соавтор, помогающий писателю создавать художественную прозу.
Отвечай на {'русском' if language == 'ru' else 'английском'} языке.
Пиши литературным языком, с вниманием к деталям и атмосфере.
{f'Стиль: {author_style}' if author_style else ''}
Когда предлагаешь текст, пиши только художественный текст без метакомментариев."""
        self.blocks.append(ContextBlock("system", prompt, priority=100))

    def add_auto_context(self, spec: Optional[NarrativeSpec], scene_idx: int = -1) -> None:
        if not spec:
            return

        core = f"Жанр: {spec.core_idea.genre.value}, Логлайн: {spec.core_idea.logline}"
        if spec.core_idea.central_conflict:
            core += f"\nКонфликт: {spec.core_idea.central_conflict}"
        self.blocks.append(ContextBlock("core_idea", core, priority=90))

        if 0 <= scene_idx < len(spec.scenes):
            scene = spec.scenes[scene_idx]
            scene_text = f"Сцена {scene_idx}: {scene.title}\n{scene.content or scene.summary or ''}"
            self.blocks.append(ContextBlock("current_scene", scene_text, priority=85))

            if scene_idx > 0:
                prev = spec.scenes[scene_idx - 1]
                prev_text = f"Предыдущая сцена: {prev.title}\n{prev.summary or (prev.content or '')[:500]}"
                self.blocks.append(ContextBlock("prev_scene", prev_text, priority=70))

    def add_reference(self, ref_type: str, key: str, content: str) -> None:
        self.blocks.append(ContextBlock(f"ref:{ref_type}:{key}", content, priority=60))

    def add_pinned(self, content: str) -> None:
        if content:
            self.blocks.append(ContextBlock("pinned", content, priority=75))

    def add_history(self, messages: list[dict]) -> None:
        history_text = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_text += f"\n[{role}]: {content}"
        if history_text:
            self.blocks.append(ContextBlock("history", history_text.strip(), priority=50))

    def add_user_message(self, message: str) -> None:
        self.blocks.append(ContextBlock("user_message", message, priority=95))

    def build_messages(self) -> list[dict]:
        """Build the final messages array for the LLM API, respecting token budget."""
        sorted_blocks = sorted(self.blocks, key=lambda b: b.priority, reverse=True)

        selected = []
        total = 0
        response_reserve = 2000

        for block in sorted_blocks:
            if total + block.tokens + response_reserve > self.max_tokens:
                if block.priority >= 90:
                    trimmed = block.content[:self.remaining * 4]
                    selected.append(ContextBlock(block.name, trimmed, priority=block.priority))
                    total += estimate_tokens(trimmed)
                continue
            selected.append(block)
            total += block.tokens

        messages = []
        system_parts = []
        for b in selected:
            if b.name == "system" or b.name.startswith("ref:") or b.name in ("core_idea", "current_scene", "prev_scene", "pinned"):
                system_parts.append(b.content)
            elif b.name == "user_message":
                pass  # added last
            elif b.name == "history":
                pass  # parsed below

        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})

        history_block = next((b for b in selected if b.name == "history"), None)
        if history_block:
            for line in history_block.content.split("\n["):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("["):
                    line = line[1:]
                if "]: " in line:
                    role, content = line.split("]: ", 1)
                    role = role.strip().lower()
                    if role in ("user", "assistant"):
                        messages.append({"role": role, "content": content})

        user_block = next((b for b in selected if b.name == "user_message"), None)
        if user_block:
            messages.append({"role": "user", "content": user_block.content})

        return messages

    def get_budget_info(self) -> dict:
        return {
            "max_tokens": self.max_tokens,
            "used_tokens": self.used_tokens,
            "remaining_tokens": self.remaining,
            "usage_pct": round(self.usage_pct * 100, 1),
            "blocks": [{"name": b.name, "tokens": b.tokens} for b in self.blocks],
        }


def resolve_reference(ref_type: str, key: str, spec: Optional[NarrativeSpec]) -> str:
    """Resolve an @-reference to its text content."""
    if not spec:
        return ""

    if ref_type == "scene" and key.isdigit():
        idx = int(key)
        if 0 <= idx < len(spec.scenes):
            s = spec.scenes[idx]
            return f"Сцена {idx}: {s.title}\n{s.content or s.summary or ''}"

    elif ref_type == "char":
        for c in spec.characters:
            if c.name.lower() == key.lower():
                parts = [f"Персонаж: {c.name} ({c.role.value})"]
                if c.motivation:
                    parts.append(f"Мотивация: {c.motivation}")
                if c.fear:
                    parts.append(f"Страх: {c.fear}")
                return "\n".join(parts)

    elif ref_type == "world":
        w = spec.world
        return f"Мир: {w.world_type}, Период: {w.time_period}\nАтмосфера: {w.atmosphere}\nПравила: {w.rules}"

    elif ref_type == "plot":
        ci = spec.core_idea
        return f"Логлайн: {ci.logline}\nЖанр: {ci.genre.value}\nКонфликт: {ci.central_conflict}"

    elif ref_type == "structure":
        s = spec.structure
        pts = ", ".join(tp.name for tp in s.turning_points) if s.turning_points else ""
        return f"Структура: {s.macro_structure.value}\nПоворотные точки: {pts}\nКульминация: {s.climax}"

    elif ref_type == "all-chars":
        return "\n".join(f"- {c.name} ({c.role.value}): {c.motivation}" for c in spec.characters)

    elif ref_type == "style":
        return spec.core_idea.tone or ""

    elif ref_type == "prev":
        scenes_with_content = [s for s in spec.scenes if s.content]
        if scenes_with_content:
            last = scenes_with_content[-1]
            return f"Предыдущая сцена: {last.title}\n{last.summary or (last.content or '')[:500]}"

    return f"[Не найдено: @{ref_type}:{key}]"
