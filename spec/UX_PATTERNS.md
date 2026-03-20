# UX Patterns — Cross-Cutting спецификация

Дата: 2026-03-20
Статус: Draft

---

## 1. Toast Notifications

### Замена `alert()` и `window.location.reload()`

Текущее поведение: `alert('Saved')`, `window.location.reload()` после каждого действия.

Целевое: toast-уведомления в углу экрана.

### Типы

| Тип | Цвет | Иконка | Пример |
|-----|------|--------|--------|
| Success | Зелёный | ✓ | "Глава сохранена" |
| Error | Красный | ✕ | "Ошибка генерации" |
| Warning | Жёлтый | ⚠ | "LLM не настроен" |
| Info | Синий | ℹ | "Генерация запущена..." |
| Progress | Синий + спиннер | ⟳ | "Генерация... 2/3 итерации" |

### Поведение
- Появляется в правом верхнем углу
- Автозакрытие через 4 секунды (success/info), 8 секунд (error/warning)
- Progress — остаётся до завершения операции
- Стек: несколько toast друг над другом

### Реализация

Лёгкий компонент на vanilla JS, включаемый в `base.html`:

```javascript
function showToast(message, type = 'success', duration = 4000) {
    // create div, animate in, auto-remove
}
```

---

## 2. Loading States

### Skeleton Screens

Вместо пустого экрана при загрузке — серые анимированные блоки-заглушки.

Применяется:
- Список проектов (cards skeleton)
- Список сцен (list skeleton)
- Editor area (text block skeleton)

### Progress Indicators

| Операция | Индикатор |
|----------|-----------|
| Generate chapter/scene | Spinner + streaming текст |
| Review | Spinner → Score badge |
| Produce HQ | Progress bar: "Итерация 1/3, Score: 6.2" |
| Book Analysis | Spinner → отформатированный отчёт |
| Book Rewrite | Progress: "Глава 2/5 переписана" |
| Export | Spinner → скачивание |

### Кнопки во время загрузки
- Disabled + спиннер вместо текста
- Текст меняется: "Generate" → "Generating..."

---

## 3. SSE Streaming

### Для генерации текста

Вместо ожидания полного ответа — текст появляется по мере генерации (как в ChatGPT).

```javascript
const source = new EventSource(`/projects/${id}/generate-scene-stream/${idx}`);
source.onmessage = (e) => {
    editor.value += e.data;
};
source.addEventListener('done', () => {
    source.close();
    showToast('Сцена сгенерирована');
});
```

Backend: `StreamingResponse` с `text/event-stream`.

Применяется:
- Generate scene
- Generate chapter
- Generate variants (каждый вариант — поток)
- Illustration prompt generation

---

## 4. Keyboard Shortcuts

| Shortcut | Действие | Контекст |
|----------|----------|----------|
| `Ctrl+S` / `Cmd+S` | Save | Editor, Workspace |
| `Ctrl+G` | Generate | Editor, Workspace |
| `Ctrl+R` | Review | Editor, Workspace |
| `Ctrl+Shift+H` | Produce HQ | Editor |
| `Ctrl+I` | Illustrate | Workspace |
| `Ctrl+Z` | Undo | Editor |
| `Ctrl+Shift+Z` | Redo | Editor |
| `Escape` | Close modal/panel | Global |
| `Ctrl+/` | Show shortcuts help | Global |

### Реализация

Глобальный listener в `base.html`:
```javascript
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        document.querySelector('[data-action="save"]')?.click();
    }
});
```

---

## 5. Autosave

### Поведение
- Автосохранение через 3 секунды после последнего изменения (debounce)
- Индикатор: "Сохранено ✓" / "Сохранение..." / "Не сохранено ⚠"
- Работает в Editor и Workspace

### Индикатор

```
┌──────────────────────────────────────────┐
│  Scene Title          Saved ✓  12:34:56  │
└──────────────────────────────────────────┘
```

При изменении:
```
│  Scene Title     Saving...  ⟳            │
```

При ошибке:
```
│  Scene Title     Not saved ⚠  [Retry]    │
```

---

## 6. Тёмная тема

### CSS-переменные

```css
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f9fafb;
    --text-primary: #111827;
    --text-secondary: #6b7280;
    --border: #e5e7eb;
    --accent: #4f46e5;
}

[data-theme="dark"] {
    --bg-primary: #1f2937;
    --bg-secondary: #111827;
    --text-primary: #f9fafb;
    --text-secondary: #9ca3af;
    --border: #374151;
    --accent: #818cf8;
}
```

### Переключатель
- Иконка солнце/луна в top bar
- Сохранение предпочтения в localStorage
- Уважать `prefers-color-scheme` системы

---

## 7. Responsive Design

### Breakpoints

| Размер | Layout |
|--------|--------|
| Desktop (>1280px) | 3-колоночный workspace, sidebar |
| Tablet (768-1280px) | 2-колоночный workspace, sidebar сворачивается |
| Mobile (<768px) | 1-колоночный, bottom nav вместо sidebar |

### Workspace на мобильном
- Вкладки: Scenes | Editor | AI
- Swipe между панелями

---

## 8. Error Handling

### Вместо raw stack traces

```
┌─ Error ──────────────────────────────────┐
│  ✕ Ошибка генерации                      │
│                                          │
│  LLM вернул некорректный ответ.          │
│  Попробуйте ещё раз или измените         │
│  параметры генерации.                    │
│                                          │
│  [Попробовать снова]  [Подробнее ▾]      │
│                                          │
│  ──── Технические детали ────            │
│  Status: 429 Rate Limit Exceeded         │
│  Endpoint: /chat/completions             │
└──────────────────────────────────────────┘
```

### Категории ошибок

| Категория | Сообщение | Действие |
|-----------|-----------|----------|
| LLM не настроен | "Настройте LLM провайдер" | Ссылка на Settings |
| Rate limit | "Слишком много запросов" | Кнопка "Retry" с delay |
| Timeout | "Превышено время ожидания" | Кнопка "Retry" |
| Parse error | "AI вернул некорректный ответ" | Кнопка "Retry" |
| DB error | "Ошибка сохранения" | Кнопка "Retry" |

---

## 9. Локализация

### Подход

Простая key-value система на JSON:

```
app/static/i18n/
├── ru.json
└── en.json
```

```json
{
    "nav.home": "Главная",
    "nav.settings": "Настройки",
    "project.create": "Создать проект",
    "scene.generate": "Сгенерировать сцену",
    "scene.save": "Сохранить",
    "review.score": "Оценка",
    ...
}
```

### Реализация (frontend)

```javascript
const i18n = {};
async function loadLocale(lang) {
    const resp = await fetch(`/static/i18n/${lang}.json`);
    Object.assign(i18n, await resp.json());
}
function t(key) {
    return i18n[key] || key;
}
```

### В шаблонах

Jinja2 `_(key)` или `{{ t('key') }}` через JS.

Первый этап: русский язык как основной.

---

## 10. Confirmation Dialogs

### Замена `confirm()`

Модальный диалог для деструктивных действий:

```
┌─────────────────────────────────────┐
│  Удалить проект?                    │
│                                     │
│  Проект "Тёмный лес" и все главы    │
│  будут удалены безвозвратно.        │
│                                     │
│     [Отмена]  [Удалить]             │
└─────────────────────────────────────┘
```

Применяется:
- Удаление проекта
- Удаление главы
- Rollback версии
- Book Rewrite (необратимая операция)
