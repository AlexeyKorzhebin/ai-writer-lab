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
Home / Dashboard  [+ Создать] [📥 Импорт архива]
├── Settings (провайдер, модель, model routing, параметры)
├── Author Presets (управление стилями)
└── Project
    ├── Story Wizard (Step 0: Quick Start + стиль → Steps 1-5)
    ├── Story Workspace
    │   ├── Left Panel: дерево Главы > Сцены (drag & drop)
    │   ├── Center: редактор сцены + inline-иллюстрации
    │   ├── Right Panel: AI Chat (единый, без вкладок)
    │   └── Sliding Panel: Illustration Prompt Generator
    ├── Chapter Editor (все сцены главы + ревью)
    ├── Book Analytics Dashboard
    │   ├── Export Book (MD / PDF / EPUB, метаданные, обложка)
    │   └── Project Archive (экспорт/импорт .zip)
    └── [Export ▾] в Top Bar (быстрый экспорт)
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
| [SCREENS_SPEC.md](SCREENS_SPEC.md) | Детальная спецификация экранов, навигация, экспорт, project archive |
| [ILLUSTRATION_PROMPT_GENERATOR.md](ILLUSTRATION_PROMPT_GENERATOR.md) | Генератор промптов, upload иллюстраций, inline-маркеры |
| [AUTHOR_STYLE_PRESETS.md](AUTHOR_STYLE_PRESETS.md) | Пресеты авторских стилей |
| [SETTINGS_AND_CONFIG.md](SETTINGS_AND_CONFIG.md) | Конфигурация провайдеров (OpenAI-compatible) и model routing |
| [AI_CHAT_AND_CONTEXT.md](AI_CHAT_AND_CONTEXT.md) | AI Chat, @-ссылки (вкл. @location:), контекст, token budget |
| [WORLD_AND_LOCATIONS.md](WORLD_AND_LOCATIONS.md) | Мир, локации, расы, иерархия, пресеты миров, import world |
| [UX_PATTERNS.md](UX_PATTERNS.md) | Cross-cutting UX-паттерны (toast, loading, keyboard) |

---

## 6. Приоритизация

### Sprint 1 — Core UX
1. Base layout (`base.html` с sidebar-навигацией, breadcrumbs, темы, [Export] в Top Bar)
2. Конфигурация провайдера/модели (Settings, Model Routing вкл. illustration_model)
3. Author style presets (Step 0 Wizard + Project Settings)
4. Починить Save vs Generate в workspace
5. Toast notifications + loading states

### Sprint 2 — Writing Experience
6. **AI Chat с @-ссылками и Context Panel** (правая панель = Chat целиком)
7. **Иерархия Главы > Сцены** в Left Panel Workspace (дерево, drag & drop)
8. SSE streaming для генерации текста
9. Форматированный review output (в чате, Score badge, Apply Fix)
10. AI-подсказки в Wizard
11. Diff view для версий

### Sprint 3 — World, Locations & Illustration
12. **World & Locations management** (LocationSpec, иерархия, пресеты)
13. **Import World** (по имени, тексту, файлу)
14. Illustration Prompt Generator (sliding panel)
15. **Upload + inline-маркеры иллюстраций** в редакторе

### Sprint 4 — Analytics, Export & Polish
16. Book Analytics Dashboard
17. **Экспорт книги** (подробный: MD/PDF/EPUB, выбор глав, метаданные, обложка)
18. **Project Archive** (экспорт/импорт .zip с БД и иллюстрациями)
19. Локализация (RU)
20. Responsive design, keyboard shortcuts
