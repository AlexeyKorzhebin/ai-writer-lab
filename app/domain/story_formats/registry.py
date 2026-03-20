"""Registry of available story format strategies."""

from __future__ import annotations

from app.domain.story_formats.base import StoryFormat
from app.domain.story_formats.three_act import ThreeActNovel
from app.domain.story_formats.short_story import ShortStory
from app.domain.story_formats.hero_journey import HeroJourney


class StoryFormatRegistry:
    _formats: dict[str, StoryFormat] = {}

    @classmethod
    def register(cls, key: str, fmt: StoryFormat) -> None:
        cls._formats[key] = fmt

    @classmethod
    def get(cls, key: str) -> StoryFormat | None:
        return cls._formats.get(key)

    @classmethod
    def get_or_default(cls, key: str | None) -> StoryFormat:
        if key and key in cls._formats:
            return cls._formats[key]
        return cls._formats.get("three_act", ThreeActNovel())

    @classmethod
    def list_formats(cls) -> list[dict]:
        return [
            {"key": k, "name": f.name, "description": f.description}
            for k, f in cls._formats.items()
        ]

    @classmethod
    def setup_defaults(cls) -> None:
        cls.register("three_act", ThreeActNovel())
        cls.register("short_story", ShortStory())
        cls.register("hero_journey", HeroJourney())


StoryFormatRegistry.setup_defaults()
