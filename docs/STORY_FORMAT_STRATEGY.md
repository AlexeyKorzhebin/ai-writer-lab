# Story Format Strategy — Narrative Architecture Layer

Дата фиксации: 2026-03-15
Версия проекта: v0.2 Clean Architecture Baseline

---

# 1. Зачем нужен Story Format Layer

Story Format — это не UI‑параметр, а стратегический слой генерации.

Он определяет:
- Макро‑структуру истории
- Логику конфликта
- Эмоциональную динамику
- Правила consistency
- Структуру outline
- Правила review

Story Format реализуется как Domain Strategy.

---

# 2. Общая модель нарратива (Invariant Layer)

Любая художественная история содержит:

| Слой | Описание |
|------|----------|
| World | Мир и сеттинг |
| Characters | Главные и второстепенные персонажи |
| Structure | Макро‑структура произведения |
| Scenes | Последовательность сцен |
| Conflict | Центральный конфликт |
| Emotional Arc | Эмоциональная кривая |
| Resolution | Развязка |

Это Domain‑инвариант.

---

# 3. Сравнение жанров / форматов

| Формат | Структура | Конфликт | Арка героя | Особые требования |
|--------|-----------|----------|------------|-------------------|
| Three Act Novel | Setup → Confrontation → Resolution | Внешний + внутренний | Да | Чёткая кульминация |
| Hero’s Journey | 12 стадий | Трансформация | Обязательна | Ментор, возвращение |
| Mystery | Clue → Suspicion → Reveal | Скрытая правда | Необязательно | Логика улик |
| Epic Fantasy | Saga arc | Мир vs зло | Часто коллективная | Lore consistency |
| Short Story | Сжатая | Один фокус | Мини | Один поворот |
| Psychological Drama | Внутренний конфликт | Личность | Глубокая | Медленный темп |

---

# 4. Общие и переменные компоненты

## Общие (Core Domain)
- ProjectEntity
- ChapterEntity
- AuthorProfile
- WriterPipeline
- ReviewAgent
- EditorAgent
- OrchestratorAgent

## Переменные (Strategy Layer)
- Outline generator logic
- Scene prompt templates
- Conflict escalation model
- Emotional arc model
- Consistency rules
- Review criteria

---

# 5. Архитектурная модель

StoryFormat реализуется как стратегия:

```
Domain
 ├── Entities
 ├── StoryFormat (Strategy)
 └── NarrativeRules

Application
 ├── GenerateChapterUseCase
 ├── ReviewChapterUseCase
 └── ProduceHighQualityUseCase

Infrastructure
 ├── Repository
 ├── LLM
 └── Persistence
```

---

# 6. Интерфейс StoryFormat

```python
class StoryFormat(ABC):
    def build_outline_prompt(...)
    def build_scene_prompt(...)
    def review_rules(...)
    def consistency_rules(...)
    def emotional_model(...)
```

---

# 7. UX Следствие

UI должен предлагать выбор:

✨ Нарративная стратегия:
- Трёхактный роман
- Путь героя
- Детектив
- Эпическая сага
- Короткий рассказ

Но это не просто label — это подключение стратегии.

---

# 8. Стратегическое значение

Story Format Strategy превращает AI Writer Lab из генератора текста в:

→ Конструктор нарративных стратегий
→ Архитектурный инструмент создания художественных миров
→ Платформу для модульного сторителлинга

---

Следующий шаг: реализация StoryFormatRegistry и базовой стратегии ThreeAct.
