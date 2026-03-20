# Illustration Prompt Generator — Спецификация

Дата: 2026-03-20
Статус: Draft

---

## 1. Концепция

Illustration Prompt Generator — модуль для создания текстовых промптов, описывающих визуальное представление сцен книги. Промпты генерируются AI на основе текста сцены и шаблонов, и могут быть использованы в любом image-генераторе (Midjourney, DALL-E, Stable Diffusion, Kandinsky / z-image и др.).

Ключевая идея: автор выделяет фрагмент текста или выбирает целую сцену → AI предлагает 3 варианта визуального представления → автор редактирует или пишет свой → система генерирует финальный промпт по выбранному шаблону.

---

## 2. User Flow

```
1. Автор работает в Story Workspace (центральная панель — текст сцены)
2. Выделяет фрагмент текста ИЛИ нажимает кнопку "Illustrate Scene"
3. Открывается панель Illustration Prompt Generator
4. AI анализирует фрагмент/сцену и предлагает:
   - Вариант A — визуальная интерпретация (описание сцены)
   - Вариант B — альтернативная композиция
   - Вариант C — фокус на деталях/эмоциях
   - "Write My Own" — свой вариант
5. Автор выбирает вариант, может отредактировать описание
6. Выбирает шаблон промпта (dropdown)
7. Нажимает "Generate Prompt"
8. Система подставляет описание в шаблон промпта → финальный текст
9. Автор копирует промпт или сохраняет к сцене
```

---

## 3. Шаблоны промптов (Prompt Templates)

### 3.1 Формат хранения

Шаблоны хранятся в Markdown-файлах в директории `app/data/illustration_templates/`.

Каждый файл — один шаблон.

### 3.2 Структура файла шаблона

```markdown
---
name: "Реалистичная иллюстрация (z-image)"
target: "z-image"
tags: [realistic, detailed, book-illustration]
---

# Промпт-шаблон

{{scene_description}}

Style: realistic book illustration, detailed, cinematic lighting
Medium: digital painting
Aspect ratio: 16:9
Quality: high detail, professional illustration

{{#if characters}}
Characters present: {{characters}}
{{/if}}

{{#if mood}}
Mood: {{mood}}
{{/if}}

{{#if setting}}
Setting: {{setting}}
{{/if}}
```

### 3.3 Примеры шаблонов

**`realistic_book.md`** — Реалистичная книжная иллюстрация
```
{{scene_description}}
Style: realistic book illustration, detailed, oil painting style
Medium: traditional illustration
Colors: rich, warm palette
Mood: {{mood}}
Setting: {{setting}}
```

**`fantasy_epic.md`** — Эпическое фэнтези
```
{{scene_description}}
Style: epic fantasy illustration, dramatic lighting, grand scale
Medium: digital art, concept art
Colors: deep blues, golds, dramatic shadows
Atmosphere: {{mood}}
Environment: {{setting}}
Characters: {{characters}}
```

**`noir_mystery.md`** — Нуар / детектив
```
{{scene_description}}
Style: film noir, high contrast, shadows, moody
Medium: black and white illustration with accent colors
Lighting: chiaroscuro, street lights, rain reflections
Mood: {{mood}}
```

**`manga_anime.md`** — Манга / аниме стиль
```
{{scene_description}}
Style: manga illustration, expressive characters, dynamic composition
Medium: manga/anime digital art
Expression: {{mood}}
Background: {{setting}}
```

**`minimalist_modern.md`** — Минималистичная современная
```
{{scene_description}}
Style: minimalist, clean lines, limited color palette
Medium: vector illustration, flat design
Focus: emotional core of the scene
Mood: {{mood}}
```

**`custom.md`** — Пользовательский (пустой шаблон)
```
{{scene_description}}

{{custom_instructions}}
```

### 3.4 Переменные шаблонов

| Переменная | Источник | Описание |
|-----------|----------|----------|
| `{{scene_description}}` | AI-generated или ручной ввод | Визуальное описание сцены |
| `{{characters}}` | NarrativeSpec.characters | Участники сцены |
| `{{mood}}` | SceneSpec.emotional_state | Эмоциональное состояние |
| `{{setting}}` | WorldSpec + SceneSpec | Локация и обстановка |
| `{{time_of_day}}` | Извлекается AI из текста | Время суток |
| `{{custom_instructions}}` | Ввод пользователя | Дополнительные инструкции |

---

## 4. AI-генерация вариантов

### 4.1 Входные данные для AI

```json
{
  "scene_text": "выделенный фрагмент или полный текст сцены",
  "scene_spec": {
    "title": "Встреча у моста",
    "participants": ["Анна", "Дмитрий"],
    "emotional_state": "напряжение, надежда",
    "purpose": "Примирение после конфликта"
  },
  "world_spec": {
    "world_type": "realistic",
    "time_period": "1920-е",
    "atmosphere": "Серый промышленный город"
  },
  "characters": [
    {
      "name": "Анна",
      "appearance": "Высокая, тёмные волосы, серые глаза",
      "role": "protagonist"
    }
  ]
}
```

### 4.2 AI-промпт для генерации вариантов

```
На основе следующего фрагмента текста создай 3 различных варианта
визуального описания сцены для генерации иллюстрации.

Текст сцены:
{scene_text}

Контекст:
- Мир: {world_type}, {time_period}
- Атмосфера: {atmosphere}
- Участники: {participants}
- Эмоциональное состояние: {emotional_state}

Для каждого варианта укажи:
1. Композицию (что в центре, что на фоне)
2. Ракурс (крупный план, средний, общий)
3. Освещение
4. Ключевые визуальные детали
5. Эмоциональный акцент

Формат ответа — JSON:
{
  "variants": [
    {
      "label": "Вариант A — ...",
      "description": "...",
      "composition": "...",
      "angle": "...",
      "lighting": "...",
      "key_details": "...",
      "emotional_focus": "..."
    }
  ]
}
```

### 4.3 Выходные данные

AI возвращает 3 варианта. Каждый вариант включает:
- `label` — краткое название варианта
- `description` — полное визуальное описание (это станет `{{scene_description}}` в шаблоне)
- Метаданные композиции (для отображения в UI)

---

## 5. UI-компоненты

### 5.1 Расположение

Illustration Prompt Generator интегрируется в Story Workspace:
- **Кнопка** "Illustrate" в toolbar центральной панели (рядом с Save/Generate)
- **Контекстное меню** при выделении текста → "Illustrate this fragment"
- **Панель генератора** открывается как **modal** или **sliding panel** справа (поверх AI Co-Author)

### 5.2 Wireframe панели генератора

```
┌─────────────────────────────────────────────┐
│  Illustration Prompt Generator        [✕]   │
├─────────────────────────────────────────────┤
│                                             │
│  Source text:                               │
│  ┌─────────────────────────────────────┐    │
│  │ "Анна стояла на мосту, глядя на     │    │
│  │  тёмную воду. Ветер трепал..."      │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  [Generate Variants]                        │
│                                             │
│  ┌─ Variant A ─────────────────────────┐    │
│  │ Общий план. Женская фигура на       │    │
│  │ каменном мосту. Тёмная река внизу.  │    │
│  │ Вечернее освещение...               │    │
│  │                           [Select]  │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─ Variant B ─────────────────────────┐    │
│  │ Крупный план. Лицо Анны, отражение  │    │
│  │ воды в глазах. Ветер в волосах...   │    │
│  │                           [Select]  │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─ Variant C ─────────────────────────┐    │
│  │ Вид сверху. Мост и река,            │    │
│  │ маленькая фигура в центре...        │    │
│  │                           [Select]  │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  [Write My Own]                             │
│                                             │
│  ─────────────────────────────────────────  │
│                                             │
│  Selected description: (editable)           │
│  ┌─────────────────────────────────────┐    │
│  │ Общий план. Женская фигура на       │    │
│  │ каменном мосту...                   │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  Template: [Реалистичная иллюстрация ▾]     │
│                                             │
│  [Generate Prompt]                          │
│                                             │
│  ─────────────────────────────────────────  │
│                                             │
│  Generated Prompt:                          │
│  ┌─────────────────────────────────────┐    │
│  │ A woman standing on a stone bridge  │    │
│  │ overlooking a dark river. Evening   │    │
│  │ light. Wind in her dark hair...     │    │
│  │ Style: realistic book illustration  │    │
│  │ Medium: digital painting            │    │
│  │ ...                                 │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  [Copy to Clipboard]  [Save to Scene]       │
│                                             │
└─────────────────────────────────────────────┘
```

### 5.3 Состояния UI

1. **Initial** — показан исходный текст, кнопка "Generate Variants"
2. **Loading** — спиннер, "AI анализирует сцену..."
3. **Variants Ready** — 3 карточки + Write My Own
4. **Editing** — выбранный вариант в редактируемом поле
5. **Prompt Generated** — финальный промпт с кнопками Copy/Save

---

## 6. Backend API

### 6.1 Новые endpoints

```
POST /projects/{id}/narrative-spec/illustration-variants/{scene_idx}
Body: {
  "fragment": "optional selected text fragment"
}
Response: {
  "variants": [
    {
      "label": "Variant A — General view",
      "description": "...",
      "composition": "...",
      "angle": "...",
      "lighting": "...",
      "key_details": "...",
      "emotional_focus": "..."
    },
    ...
  ]
}

POST /projects/{id}/narrative-spec/illustration-prompt/{scene_idx}
Body: {
  "description": "selected/edited scene description",
  "template_key": "realistic_book",
  "custom_instructions": "optional"
}
Response: {
  "prompt": "final generated prompt text",
  "template_used": "realistic_book"
}

GET /illustration-templates
Response: {
  "templates": [
    {
      "key": "realistic_book",
      "name": "Реалистичная книжная иллюстрация",
      "target": "z-image",
      "tags": ["realistic", "detailed"]
    },
    ...
  ]
}
```

### 6.2 Хранение промптов

Сгенерированные промпты сохраняются к сцене:

```python
@dataclass
class IllustrationPrompt:
    id: Optional[int] = None
    scene_id: Optional[int] = None
    description: str = ""
    template_key: str = ""
    generated_prompt: str = ""
    fragment: Optional[str] = None  # исходный фрагмент текста
    created_at: Optional[str] = None
```

Новая таблица `illustration_prompts`:
- id (PK)
- scene_id (FK → scenes.id)
- description
- template_key
- generated_prompt
- fragment
- created_at

---

## 7. Шаблоны промптов — управление

### 7.1 Файловая структура

```
app/data/illustration_templates/
├── realistic_book.md
├── fantasy_epic.md
├── noir_mystery.md
├── manga_anime.md
├── minimalist_modern.md
├── watercolor.md
├── comic_book.md
└── custom.md
```

### 7.2 Загрузка шаблонов

При старте приложения шаблоны загружаются из файлов.
YAML frontmatter каждого файла определяет метаданные.
Тело файла — сам шаблон промпта.

### 7.3 Пользовательские шаблоны (будущее)

В будущем пользователь сможет:
- Создавать свои шаблоны через UI
- Хранить их в БД
- Делиться ими

---

## 8. Интеграция с NarrativeSpec

### 8.1 Контекст для генерации

AI использует для генерации вариантов:
- Текст сцены (или выделенный фрагмент)
- `SceneSpec` (participants, emotional_state, purpose)
- `WorldSpec` (world_type, time_period, atmosphere)
- `CharacterSpec` (внешность — новое поле `appearance`)
- `CoreIdea` (genre, tone)

### 8.2 Необходимые изменения в модели

Добавить в `CharacterSpec`:
```python
appearance: str = ""  # физическое описание для иллюстраций
speech_style: str = ""  # манера речи (для будущего)
```

Добавить в `SceneSpec`:
```python
illustration_prompts: list[IllustrationPrompt] = field(default_factory=list)
```

---

## 9. Примеры использования

### Пример 1: Фэнтези-сцена

**Текст:** "Эльдар поднял меч, и клинок засиял голубым светом. Тьма отступила."

**Variant A:** "Воин в серебряных доспехах поднимает светящийся голубым меч. Тёмный лес позади. Лучи света пробивают тьму. Героический ракурс снизу."

**Template:** Fantasy Epic

**Prompt:**
```
A warrior in silver armor raises a sword glowing with blue light.
Dark forest behind. Rays of blue light pierce the darkness.
Heroic low-angle shot.
Style: epic fantasy illustration, dramatic lighting, grand scale
Medium: digital art, concept art
Colors: deep blues, golds, dramatic shadows
Atmosphere: triumph over darkness
```

### Пример 2: Нуар-детектив

**Текст:** "Он закурил, стоя под фонарём. Дождь стучал по шляпе."

**Variant B:** "Крупный план мужчины в шляпе под уличным фонарём. Сигаретный дым. Дождь. Мокрый асфальт отражает свет."

**Template:** Noir Mystery

**Prompt:**
```
Close-up of a man in a fedora under a street lamp.
Cigarette smoke curling up. Rain falling. Wet asphalt reflecting light.
Style: film noir, high contrast, shadows, moody
Medium: black and white illustration with accent colors
Lighting: chiaroscuro, street lights, rain reflections
Mood: solitude, tension
```

---

## 10. Язык промптов

По умолчанию финальный промпт генерируется на **английском** (большинство image-генераторов лучше работают с английским).

Опция: переключатель языка промпта (RU/EN) в UI.

AI-описания вариантов показываются на **языке интерфейса** (русском), а финальный prompt — на английском.
