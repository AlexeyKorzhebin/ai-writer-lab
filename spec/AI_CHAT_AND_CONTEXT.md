# AI Chat & Context Management — Спецификация

Дата: 2026-03-20
Статус: Draft

---

## 1. Общая концепция

AI Chat — основной инструмент взаимодействия автора с AI в рамках Story Workspace. Это не просто "генерация по кнопке", а полноценный диалог, где автор может:

- Давать инструкции ("сделай диалог длиннее")
- Ссылаться на элементы книги ("перепиши с учётом @character:Анна")
- Видеть и управлять контекстом, который получает AI
- Контролировать расход токенов
- Разделять работу на задачи/сессии

---

## 2. Reference System (система ссылок)

### 2.1 Синтаксис @ -ссылок

По аналогии с Cursor / Slack, автор вводит `@` в чат, после чего появляется
dropdown-автокомплит с доступными элементами.

| Ссылка | Что подтягивает в контекст | Пример |
|--------|---------------------------|--------|
| `@scene:N` или `@scene:Title` | Полный текст сцены + метаданные | `@scene:3` или `@scene:Встреча у моста` |
| `@char:Name` | Полное описание персонажа из NarrativeSpec | `@char:Анна` |
| `@world` | WorldSpec целиком | `@world` |
| `@plot` | CoreIdea (logline, conflict, themes) | `@plot` |
| `@structure` | StructuralSpec (turning points, climax) | `@structure` |
| `@chapter:N` | Summary главы (или полный текст, если указать `@chapter:3:full`) | `@chapter:2` |
| `@prev` | Полный текст предыдущей сцены | `@prev` |
| `@selection` | Текущий выделенный фрагмент в редакторе | `@selection` |
| `@style` | Author style profile | `@style` |
| `@review:N` | Последний review сцены N | `@review:3` |
| `@all-chars` | Краткий список всех персонажей | `@all-chars` |
| `@timeline` | Список всех сцен с кратким описанием | `@timeline` |

### 2.2 UI автокомплита

При вводе `@` в поле чата:

```
┌─────────────────────────────────┐
│  🔍 Search elements...          │
├─────────────────────────────────┤
│  📄 Scenes                      │
│    Scene 1: Прибытие            │
│    Scene 2: Первая встреча      │
│    Scene 3: Встреча у моста  ←  │
│    Scene 4: Разговор            │
│  👤 Characters                   │
│    Анна (protagonist)           │
│    Дмитрий (antagonist)         │
│    Иван (mentor)                │
│  🌍 World                        │
│  📖 Plot                         │
│  🏗️ Structure                    │
│  📝 Chapters                     │
│    Chapter 1: Начало            │
│    Chapter 2: Конфликт          │
│  ✏️ Current selection             │
│  🎭 Author style                 │
└─────────────────────────────────┘
```

Поведение:
- Ввод `@` → открывается dropdown
- Продолжаем набирать → фильтрует (fuzzy search)
- `@Ann` → предлагает "@char:Анна"
- `@sc` → предлагает все сцены
- Стрелки ↑↓ для навигации, Enter для выбора
- Выбранная ссылка вставляется как badge/chip: `[@char:Анна]`

### 2.3 Визуальное представление ссылок в чате

Ссылки отображаются как кликабельные badges:

```
Перепиши эту сцену, чтобы [🧑 Анна] была более решительной.
Учти, что в [📄 Scene 2] она ещё сомневалась.
```

При клике на badge → показывает превью содержимого (popup).

### 2.4 Drag & Drop ссылок

Помимо `@`-синтаксиса, можно перетаскивать элементы из левой панели
(сцены, персонажи) прямо в поле чата. Это автоматически создаёт ссылку.

---

## 3. Context Window Management

### 3.1 Архитектура контекста

Контекст AI-запроса состоит из нескольких слоёв:

```
┌─────────────────────────────────────────────┐
│ SYSTEM PROMPT (фиксированный)               │
│  - Роль: AI-соавтор                         │
│  - Author style                             │
│  - Правила генерации                        │
│  ~500 tokens                                │
├─────────────────────────────────────────────┤
│ AUTO-CONTEXT (автоматический)               │
│  - Текущая сцена (текст + метаданные)       │
│  - Предыдущая сцена (summary)               │
│  - CoreIdea (logline, genre, conflict)      │
│  ~1,000–3,000 tokens                        │
├─────────────────────────────────────────────┤
│ PINNED CONTEXT (закреплённый пользователем) │
│  - Элементы, которые пользователь            │
│    закрепил через pin                        │
│  ~0–4,000 tokens                            │
├─────────────────────────────────────────────┤
│ REFERENCED CONTEXT (@-ссылки)               │
│  - Элементы, упомянутые через @             │
│  ~0–4,000 tokens                            │
├─────────────────────────────────────────────┤
│ CHAT HISTORY                                │
│  - Предыдущие сообщения в текущей сессии    │
│  ~0–4,000 tokens                            │
├─────────────────────────────────────────────┤
│ USER MESSAGE                                │
│  - Текущее сообщение пользователя           │
│  ~50–500 tokens                             │
├─────────────────────────────────────────────┤
│ RESERVED FOR RESPONSE                       │
│  ~2,000–4,000 tokens                        │
└─────────────────────────────────────────────┘
```

### 3.2 Token Budget

```
Общий лимит модели (напр. 128k для GPT-4-turbo)
 └── System prompt:     ~500 tokens  (фикс.)
 └── Auto-context:      ~1,000–3,000 tokens  (авто)
 └── Pinned context:    ~0–4,000 tokens  (пользователь)
 └── @ References:      ~0–4,000 tokens  (пользователь)
 └── Chat history:      ~0–4,000 tokens  (авто, сжимается)
 └── User message:      ~50–500 tokens  (пользователь)
 └── Response reserve:  ~2,000–4,000 tokens  (фикс.)
                        ─────────────
 Доступно:             ~max_tokens модели
```

Для моделей с малым контекстом (8k) бюджет сжимается автоматически:
- Chat history суммаризируется
- @ References обрезаются до summaries вместо полного текста
- Предупреждение пользователю

---

## 4. Context Panel (UI)

### 4.1 Расположение

Context Panel — раскрываемая секция над чатом в правой панели.
По умолчанию — компактный вид (одна строка со статистикой).
При нажатии — разворачивается полный список элементов контекста.

### 4.2 Компактный вид

```
┌─────────────────────────────────────────┐
│  Context: 4,230 / 16,000 tokens  [▾]   │
│  ████████░░░░░░░░░░░░  26%              │
└─────────────────────────────────────────┘
```

Цвета прогресс-бара:
- 🟢 0–50% — зелёный (свободно)
- 🟡 50–80% — жёлтый (внимание)
- 🔴 80–100% — красный (мало места, рекомендуется очистить)

### 4.3 Развёрнутый вид

```
┌─────────────────────────────────────────┐
│  Context: 4,230 / 16,000 tokens  [▴]   │
│  ████████░░░░░░░░░░░░  26%              │
│                                         │
│  🔒 Auto-context                ~1,200t │
│    📄 Current scene: Встреча       800t │
│    📖 Plot summary                 400t │
│                                         │
│  📌 Pinned                      ~1,500t │
│    👤 Анна (full)           680t  [📌✕] │
│    👤 Дмитрий (full)        520t  [📌✕] │
│    🌍 World spec            300t  [📌✕] │
│                                         │
│  @ Referenced (this message)      ~800t │
│    📄 Scene 2 (summary)     250t  [✕]   │
│    📄 Scene 5 (summary)     250t  [✕]   │
│    📝 Review scene 3        300t  [✕]   │
│                                         │
│  💬 Chat history (5 msgs)        ~730t  │
│                            [Summarize]  │
│                                         │
│  ─────────────────────────────────────  │
│  [Clear References]  [New Task]         │
│  [Context Settings ⚙]                  │
└─────────────────────────────────────────┘
```

### 4.4 Элементы контекста

Каждый элемент показывает:
- Иконку типа (📄 сцена, 👤 персонаж, 🌍 мир и т.д.)
- Название
- Размер в токенах (приблизительный)
- Кнопки управления:
  - 📌 Pin/Unpin — закрепить (останется в контексте между сообщениями)
  - ✕ Remove — убрать из контекста
  - 👁️ Preview — показать содержимое (popup)
  - [full/summary] — переключить: полный текст или summary

### 4.5 Автоматическое управление

| Ситуация | Действие | Уведомление |
|----------|----------|-------------|
| Контекст < 50% | — | Зелёный индикатор |
| Контекст 50–80% | — | Жёлтый индикатор |
| Контекст > 80% | Auto-summarize chat history | "Chat history суммаризирована для экономии места" |
| Контекст > 90% | Предложить очистить | "Контекст почти заполнен. Удалить неактуальные ссылки?" |
| @ Reference не влезает | Подставить summary вместо full | "⚠ @scene:3 добавлена как summary (не хватает места для полного текста)" |
| Модель с малым контекстом | Агрессивная суммаризация | "Внимание: модель gpt-3.5-turbo имеет ограниченный контекст" |

---

## 5. Chat Sessions & Tasks

### 5.1 Концепция задач

Работа в чате организована в **задачи (tasks)**. Каждая задача — это отдельная
сессия с чистой историей, но с возможностью сохранить контекст.

Примеры задач:
- "Написать сцену встречи"
- "Переработать диалог Анны и Дмитрия"
- "Проверить консистентность персонажа"
- "Создать промпт для иллюстрации"

### 5.2 Lifecycle задачи

```
Создание → Работа → Завершение/Сброс
                ↑
                └── Продолжение (добавить сообщения)
```

### 5.3 UI управления задачами

```
┌─────────────────────────────────────────┐
│  Task: Переработка диалога        [▾]   │
│  ───────────────────────────────────── │
│  [+ New Task]  [History ▾]             │
└─────────────────────────────────────────┘
```

Dropdown "History" показывает предыдущие задачи:
```
┌──────────────────────────────────┐
│  📋 Task History                  │
│                                  │
│  ● Переработка диалога  (current)│
│  ○ Написание сцены 3     14:20  │
│  ○ Review сцены 2        13:45  │
│  ○ Генерация вариантов   12:30  │
│                                  │
│  [Clear All History]             │
└──────────────────────────────────┘
```

### 5.4 Когда делать New Task

Система подсказывает:

| Ситуация | Подсказка |
|----------|-----------|
| Chat > 10 сообщений | "Длинный диалог. Создать новую задачу?" |
| Смена сцены | "Вы перешли к другой сцене. Начать новую задачу?" |
| Контекст > 80% | "Контекст почти заполнен. Новая задача освободит место." |
| 30+ минут с последнего сообщения | "Продолжить текущую задачу или создать новую?" |
| Явная смена темы | AI определяет смену темы → подсказка |

### 5.5 Что происходит при New Task

1. Chat history очищается (но сохраняется в историю задач)
2. Pinned context **сохраняется** (если не снять вручную)
3. @ References очищаются
4. Auto-context пересчитывается (текущая сцена)
5. Token counter сбрасывается
6. Предыдущая задача доступна в History для просмотра

### 5.6 Что происходит при Reset (полный сброс)

1. Всё как при New Task
2. Плюс: pinned context тоже очищается
3. Контекст = только auto-context + system prompt

---

## 6. Chat UI — полный wireframe

```
┌─ AI Co-Author ──────────────────────────────┐
│                                             │
│  Task: Переработка диалога  [▾] [+ New]    │
│                                             │
│  ┌─ Context ────────────────────────────┐   │
│  │  3,450 / 16,000 tokens  26%         │   │
│  │  ████████░░░░░░░░░░░░         [▾]   │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  🤖 AI:                              │   │
│  │  Вот переработанный диалог с учётом  │   │
│  │  характера Анны:                     │   │
│  │                                      │   │
│  │  — Я не вернусь, — сказала она.     │   │
│  │  — Ты говоришь это каждый раз...    │   │
│  │                                      │   │
│  │  [Apply to Editor] [Copy]            │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  👤 You:                              │   │
│  │  Сделай Анну более решительной.      │   │
│  │  Учти [🧑 Анна] и [📄 Scene 2]       │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  🤖 AI:                              │   │
│  │  (streaming response...)             │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  Type message... @ for references    │   │
│  │                                      │   │
│  │                           [Send ↵]   │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Quick actions:                             │
│  [Continue scene] [Add dialogue]            │
│  [Describe setting] [Review]                │
│                                             │
└─────────────────────────────────────────────┘
```

### 6.1 Элементы UI

**Заголовок задачи:** название текущей задачи + dropdown истории + кнопка New

**Context bar:** компактный/раскрываемый, всегда видно кол-во токенов

**Chat area:** скроллируемая область с сообщениями. Каждое сообщение:
- Аватар (🤖 AI / 👤 You)
- Текст с ссылками-badges
- Для AI-ответов: кнопки [Apply to Editor] [Copy] [Regenerate]
- Streaming: текст появляется по мере генерации

**Input area:**
- Textarea с поддержкой @ автокомплита
- Shift+Enter = новая строка
- Enter или кнопка Send = отправить
- Подсказка: "@ для ссылок"

**Quick actions:** предустановленные действия (кнопки), зависящие от контекста:
- Если сцена пустая: [Generate scene] [Suggest variants]
- Если сцена написана: [Continue] [Add dialogue] [Describe setting] [Review]
- Если есть review: [Apply fixes] [Improve style]

---

## 7. "Apply to Editor" — применение результатов

### 7.1 Режимы применения

Когда AI генерирует текст, пользователь может:

| Действие | Что происходит |
|----------|---------------|
| **Apply to Editor** | Заменяет текст в редакторе целиком |
| **Insert at Cursor** | Вставляет в позицию курсора в редакторе |
| **Replace Selection** | Заменяет выделенный фрагмент |
| **Copy** | Копирует в буфер обмена |
| **Save as Variant** | Сохраняет как вариант сцены |

### 7.2 Preview перед применением

Для "Apply" и "Replace" — показать diff:

```
┌─ Preview Changes ─────────────────────┐
│                                       │
│  - Она молча отвернулась.            │
│  + — Я не вернусь, — сказала она     │
│  + твёрдо, глядя ему в глаза.        │
│                                       │
│  [Apply] [Cancel]                     │
└───────────────────────────────────────┘
```

---

## 8. Token Counting — техническая реализация

### 8.1 Подсчёт токенов

Frontend показывает **приблизительный** подсчёт.
Точный подсчёт делает backend перед отправкой.

**Приблизительный (frontend):**
- Для русского текста: ~1 token ≈ 2.5 символа (для GPT-моделей)
- Для английского: ~1 token ≈ 4 символа
- Обновляется в реальном времени при наборе текста

**Точный (backend):**
- tiktoken (для OpenAI-совместимых моделей)
- Считается перед отправкой запроса
- Возвращается в ответе:
  ```json
  {
    "response": "...",
    "usage": {
      "prompt_tokens": 3450,
      "completion_tokens": 520,
      "total_tokens": 3970
    }
  }
  ```

### 8.2 API для token estimation

```
POST /estimate-tokens
Body: {
  "elements": [
    {"type": "scene", "id": 3, "mode": "full"},
    {"type": "character", "name": "Анна", "mode": "full"},
    {"type": "world", "mode": "full"}
  ]
}
Response: {
  "estimates": [
    {"type": "scene", "id": 3, "tokens": 850},
    {"type": "character", "name": "Анна", "tokens": 320},
    {"type": "world", "tokens": 280}
  ],
  "total": 1450
}
```

### 8.3 Статистика сессии

В Context Panel показывается:
- Текущее заполнение контекста (tokens used / model limit)
- Потреблено за сессию (cumulative tokens sent + received)
- Стоимость (приблизительная, если известна цена модели)

```
┌─ Session Stats ─────────────────────┐
│  Context:     3,450 / 16,000 tokens │
│  Session:     12,340 tokens used    │
│  Messages:    8                     │
│  Est. cost:   ~$0.02                │
└─────────────────────────────────────┘
```

---

## 9. Context Settings

Пользователь может настроить поведение контекста:

```
┌─ Context Settings ⚙ ────────────────┐
│                                      │
│  Auto-context:                       │
│  ☑ Include current scene             │
│  ☑ Include previous scene (summary)  │
│  ☑ Include plot summary              │
│  ☐ Include all characters            │
│  ☐ Include world spec                │
│                                      │
│  History management:                 │
│  Auto-summarize after: [8] messages  │
│  Max history tokens:   [4000]        │
│                                      │
│  Token display:                      │
│  ○ Approximate (fast)                │
│  ○ Exact (slower, uses tiktoken)     │
│                                      │
│  Model context limit:                │
│  Auto-detect from model: [✓]        │
│  Override: [        ] tokens         │
│                                      │
│  [Save]                              │
└──────────────────────────────────────┘
```

---

## 10. Примеры сценариев использования

### Сценарий 1: Переработка диалога

```
User: Перепиши диалог в @scene:3 между @char:Анна и @char:Дмитрий.
      Анна должна быть более уверенной. Учти её арку из @structure.

→ AI получает в контексте:
  - System prompt + author style
  - Current scene (auto)
  - Scene 3 full text (@ ref)
  - Анна full spec (@ ref)
  - Дмитрий full spec (@ ref)
  - StructuralSpec (@ ref)
  - Chat history

→ AI генерирует переработанный диалог
→ User нажимает [Apply to Editor]
→ Diff preview → Apply
```

### Сценарий 2: Проверка консистентности

```
User: Проверь, не противоречит ли поведение @char:Анна в текущей
      сцене тому, что было в @scene:1 и @scene:2.

→ AI получает Scene 1, Scene 2, текущую сцену, Анна spec
→ AI анализирует и отвечает с пометками
→ User решает, что исправить
```

### Сценарий 3: Генерация с контролем контекста

```
[Context: 12,500 / 16,000 tokens — 78%]

User: Ещё добавь @chapter:1 для контекста

System: "⚠ @chapter:1 содержит ~4,200 tokens. Превышает лимит.
         Добавить как summary (~300 tokens)?"

User: Да, добавь summary

[Context: 12,800 / 16,000 tokens — 80%]
```

### Сценарий 4: Новая задача

```
[After 15 messages, context at 85%]

System: "Диалог довольно длинный. Создать новую задачу?
         Pinned context сохранится, история будет доступна."

User: [New Task]

→ Новая задача создаётся
→ Context сбрасывается до auto + pinned
→ Token counter: 2,100 / 16,000 (13%)
```

---

## 11. Backend Architecture

### 11.1 ChatSession model

```python
@dataclass
class ChatMessage:
    role: str           # "user" | "assistant" | "system"
    content: str
    references: list[str] = field(default_factory=list)  # ["scene:3", "char:Анна"]
    tokens: int = 0
    timestamp: str = ""

@dataclass
class ChatSession:
    id: Optional[int] = None
    project_id: int = 0
    task_name: str = ""
    messages: list[ChatMessage] = field(default_factory=list)
    pinned_context: list[str] = field(default_factory=list)  # ["char:Анна", "world"]
    created_at: str = ""
    updated_at: str = ""
    is_active: bool = True
```

### 11.2 Context Builder

```python
class ContextBuilder:
    def __init__(self, project_id, narrative_spec, model_limit):
        self.budget = TokenBudget(model_limit)
    
    def add_system_prompt(self, author_style: str) -> int:
        """Returns tokens used."""
    
    def add_auto_context(self, current_scene, prev_scene_summary, plot) -> int:
        """Auto-included context. Returns tokens used."""
    
    def add_pinned(self, elements: list[str]) -> int:
        """Pinned elements. Returns tokens used."""
    
    def add_references(self, refs: list[str]) -> int:
        """@ references from message. Returns tokens used.
        If full text doesn't fit, downgrades to summary."""
    
    def add_history(self, messages: list[ChatMessage]) -> int:
        """Chat history. Summarizes if exceeds budget."""
    
    def build(self) -> list[dict]:
        """Returns final messages array for LLM API."""
    
    def get_usage(self) -> dict:
        """Returns current token usage breakdown."""
```

### 11.3 API Endpoints

```
POST /projects/{id}/chat/send
Body: {
  "session_id": 42,         # null for new session
  "task_name": "Rewrite",   # only for new session
  "message": "Перепиши диалог...",
  "references": ["scene:3", "char:Анна"],
  "pinned": ["char:Анна", "world"]
}
Response (SSE stream): {
  "type": "token",   "data": "Вот"
  "type": "token",   "data": " переработанный"
  "type": "token",   "data": " диалог"
  ...
  "type": "done",    "data": {
    "session_id": 42,
    "usage": {
      "prompt_tokens": 3450,
      "completion_tokens": 520,
      "context_breakdown": {
        "system": 480,
        "auto": 1200,
        "pinned": 800,
        "references": 650,
        "history": 270,
        "message": 50
      }
    }
  }
}

GET /projects/{id}/chat/sessions
Response: [
  {"id": 42, "task_name": "Rewrite", "messages": 8, "updated_at": "..."},
  {"id": 41, "task_name": "Review", "messages": 3, "updated_at": "..."}
]

GET /projects/{id}/chat/sessions/{session_id}
Response: { full session with messages }

POST /projects/{id}/chat/estimate
Body: {
  "references": ["scene:3", "char:Анна"],
  "pinned": ["world"],
  "message": "Перепиши..."
}
Response: {
  "breakdown": {
    "system": 480,
    "auto": 1200,
    "pinned": 280,
    "references": 1170,
    "history": 730,
    "message": 45,
    "total": 3905,
    "model_limit": 16000,
    "available_for_response": 12095
  }
}

DELETE /projects/{id}/chat/sessions/{session_id}
```

---

## 12. Ограничения и trade-offs

| Решение | Причина | Альтернатива |
|---------|---------|-------------|
| Приблизительный подсчёт на frontend | Быстрый UX без запроса к серверу | Точный через API (медленнее) |
| Summary вместо full при нехватке места | Лучше summary чем ничего | Предупреждение + отказ |
| Авто-суммаризация истории | Экономия токенов | Потеря деталей ранних сообщений |
| Сессии хранятся в БД | Персистентность | Больше storage, нужна очистка |
| Pinned context между задачами | Удобство при работе с одним персонажем | Может занимать много места |
