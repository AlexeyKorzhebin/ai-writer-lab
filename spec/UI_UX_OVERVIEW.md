# AI Writer Lab — UI/UX Specification Overview

Дата: 2026-03-20
Статус: Draft

---

## 1. Текущее состояние

### Существующие экраны

| Шаблон | Назначение | Состояние |
|--------|------------|-----------|
| `home.html` | Список проектов + создание | Прототип |
| `project.html` | Просмотр проекта с главами | Прототип |
| `chapter.html` | Редактор главы | Прототип |
| `story_wizard.html` | 5-шаговый визард создания истории | Рабочий |
| `story_workspace.html` | 3-колоночный workspace | Рабочий |

### Текущий стек
- Tailwind CSS (CDN)
- Vanilla JavaScript
- Jinja2 шаблоны
- FastAPI backend

### Ключевые проблемы
- Нет единого layout (каждая страница самостоятельна)
- Raw JSON-вывод анализов и ревью
- `alert()` и `window.location.reload()` вместо нормального UX
- Нет конфигурации провайдеров/моделей через UI
- Нет готовых стилевых пресетов авторов
- Нет прогресс-индикаторов для длительных AI-операций
- Save вызывает generate в workspace (баг)
- Нет иллюстрационного слоя

---

## 2. Целевая архитектура экранов

```
Home / Dashboard
├── Settings (провайдер, модель, глобальные параметры)
├── Author Presets (управление стилями)
└── Project
    ├── Story Wizard (создание/редактирование NarrativeSpec)
    ├── Story Workspace (сцены + AI Co-Author)
    │   └── Illustration Prompt Generator
    ├── Chapter Editor
    ├── Book Analytics Dashboard
    └── Export
```

---

## 3. Принципы дизайна

1. **Story-First** — интерфейс ведёт пользователя через нарратив, а не через технические сущности
2. **AI как соавтор** — AI всегда предлагает варианты, пользователь выбирает
3. **Прозрачность** — видно что делает AI, какой score, какие проблемы найдены
4. **Incremental disclosure** — не показывать всё сразу, раскрывать по мере необходимости
5. **No data loss** — автосохранение, версионирование, undo
6. **Русский язык** — основной язык интерфейса (с возможностью переключения)

---

## 4. Технический стек (целевой)

- **CSS:** Tailwind CSS (CDN → local build в будущем)
- **JS:** Vanilla JS → Alpine.js для реактивности (лёгкий, без сборки)
- **Icons:** Lucide или Heroicons
- **Charts:** Chart.js (для аналитики)
- **Diff:** jsdiff (для сравнения версий)
- **Drag & drop:** SortableJS
- **Markdown:** Marked.js (для превью)
- **Streaming:** EventSource (SSE)

---

## 5. Список спецификаций

| Файл | Описание |
|------|----------|
| [SCREENS_SPEC.md](SCREENS_SPEC.md) | Детальная спецификация каждого экрана |
| [ILLUSTRATION_PROMPT_GENERATOR.md](ILLUSTRATION_PROMPT_GENERATOR.md) | Генератор промптов для иллюстраций |
| [AUTHOR_STYLE_PRESETS.md](AUTHOR_STYLE_PRESETS.md) | Пресеты авторских стилей |
| [SETTINGS_AND_CONFIG.md](SETTINGS_AND_CONFIG.md) | Конфигурация провайдеров и моделей |
| [AI_CHAT_AND_CONTEXT.md](AI_CHAT_AND_CONTEXT.md) | AI Chat, @-ссылки, управление контекстом, token budget |
| [WORLD_AND_LOCATIONS.md](WORLD_AND_LOCATIONS.md) | Мир, локации, иерархия, пресеты миров, consistency |
| [UX_PATTERNS.md](UX_PATTERNS.md) | Cross-cutting UX-паттерны (toast, loading, keyboard) |

---

## 6. Приоритизация

### Sprint 1 — Core UX
1. Base layout (`base.html` с навигацией, breadcrumbs, темы)
2. Конфигурация провайдера/модели (Settings)
3. Author style presets
4. Починить Save vs Generate в workspace
5. Toast notifications + loading states

### Sprint 2 — Writing Experience
6. SSE streaming для генерации текста
7. Форматированный review output
8. AI-подсказки в Wizard
9. Chat-mode в Co-Author panel
10. Diff view для версий

### Sprint 3 — Illustration & Analytics
11. Illustration Prompt Generator
12. Book Analytics Dashboard
13. Drag & drop сцен
14. Keyboard shortcuts

### Sprint 4 — Polish
15. Локализация (RU)
16. Responsive design
17. WYSIWYG/Markdown editor
