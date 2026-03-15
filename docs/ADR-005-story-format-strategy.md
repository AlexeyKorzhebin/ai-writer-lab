# ADR-005 — Introduce Story Format Strategy Layer

Дата: 2026-03-15
Статус: Accepted

## Context

AI Writer Lab изначально работал как генератор текста с фиксированной логикой pipeline.

Для художественной литературы этого недостаточно:
- Разные жанры требуют разной макро‑структуры
- Разные жанры требуют разных правил consistency
- Разные жанры требуют разных review‑критериев

Хардкод логики жанров в pipeline нарушает Open/Closed Principle.

## Decision

Ввести Story Format Strategy как Domain‑слой.

StoryFormat определяет:
- Outline generation rules
- Scene prompt templates
- Conflict model
- Emotional arc model
- Review rules
- Consistency rules

UseCases будут работать через выбранную стратегию.

## Consequences

✅ Гибкость
✅ Поддержка множества жанров
✅ Расширяемость без переписывания ядра
✅ Чистая архитектура (Strategy Pattern)

Следующий этап: реализация StoryFormatRegistry.
