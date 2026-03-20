# Settings & Configuration — Спецификация

Дата: 2026-03-20
Статус: Draft

---

## 1. Текущее состояние

Конфигурация (`app/core/config.py`):
```python
class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./writer.db"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-3.5-turbo"
    llm_timeout: float = 120.0
    max_orchestrator_iterations: int = 3
    orchestrator_min_score: int = 8
    debug: bool = False
```

Проблемы:
- Все настройки только через `.env` или переменные окружения
- Нет UI для смены провайдера/модели
- Нет per-project настроек
- Нет model routing (разные модели для разных задач)

---

## 2. Целевая архитектура

### 2.1 Два уровня настроек

**Глобальные** (Settings экран):
- LLM Provider: provider type, API key, base URL
- Default model
- Default generation parameters

**Per-project** (Project Settings):
- Переопределение модели
- Переопределение temperature, max_tokens
- Author style
- Story format
- Max iterations, min score

### 2.2 Приоритет

```
Per-project setting > Global setting > .env default
```

---

## 3. LLM Provider Configuration

### 3.1 Поддерживаемые провайдеры

| Provider | Base URL | Особенности |
|----------|----------|-------------|
| OpenAI | `https://api.openai.com/v1` | Стандартный API |
| CAILA | `https://caila.io/api/adapters/openai/v1` | OpenAI-compatible |
| Local (Ollama) | `http://localhost:11434/v1` | Локальные модели |
| Custom | Любой URL | OpenAI-compatible endpoint |

> **Примечание:** поддерживаются только OpenAI-compatible API. Провайдеры с
> собственным форматом API (Anthropic) требуют отдельного адаптера — планируется
> в будущих версиях.

### 3.2 UI-предустановки провайдеров

При выборе провайдера из dropdown автоматически заполняется Base URL и предлагается список моделей:

```yaml
providers:
  openai:
    name: "OpenAI"
    base_url: "https://api.openai.com/v1"
    models: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"]
  caila:
    name: "CAILA"
    base_url: "https://caila.io/api/adapters/openai/v1"
    models: ["gpt-4", "gpt-3.5-turbo"]
  ollama:
    name: "Ollama (Local)"
    base_url: "http://localhost:11434/v1"
    models: ["llama3", "mistral", "mixtral"]
  custom:
    name: "Custom"
    base_url: ""
    models: []
```

### 3.3 Test Connection

Endpoint: `POST /settings/test-connection`

```json
{
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4"
}
```

Логика: отправить простой `chat/completions` запрос с минимальным промптом. Вернуть статус.

---

## 4. Model Routing

### 4.1 Концепция

Разные задачи требуют разных моделей:
- **Draft** — дешёвая быстрая модель для первого черновика
- **Refinement** — мощная модель для финальной обработки
- **Review** — модель для оценки и ревью (нужна аналитика)
- **Illustration** — модель для генерации промптов иллюстраций

### 4.2 Реализация

Расширить `Settings`:
```python
class Settings(BaseSettings):
    # ... existing ...
    draft_model: str = ""          # fallback to openai_model
    refinement_model: str = ""     # fallback to openai_model
    review_model: str = ""         # fallback to openai_model
    illustration_model: str = ""   # fallback to openai_model
```

В `OpenAIAdapter` — метод `call()` принимает параметр `purpose`:
```python
async def call(self, messages, purpose="default"):
    model = self._get_model_for_purpose(purpose)
    ...
```

### 4.3 UI

В Settings:

```
Model Routing:
  Draft:       [gpt-3.5-turbo ▾]  (быстрый, дешёвый)
  Refinement:  [gpt-4         ▾]  (качественный)
  Review:      [gpt-4         ▾]  (аналитический)
  Illustration:[gpt-4         ▾]  (визуальное мышление)
```

---

## 5. Per-Project Settings

### 5.1 Расширение модели Project

Уже есть в БД:
- `model_name`
- `temperature`
- `max_tokens`

Добавить:
- `max_iterations` (уже есть в NarrativeSpec migration, но на уровне project)
- `min_score`

### 5.2 UI

В Project Dashboard — секция "Project Settings":

```
┌─ Project Settings ──────────────────┐
│                                      │
│  Model: [Use global default     ▾]   │
│  Temperature: [0.7]                  │
│  Max tokens: [4096]                  │
│  Max iterations: [3]                 │
│  Min quality score: [8]              │
│                                      │
│  Author style:                       │
│  [А. С. Пушкин ▾] [Edit]           │
│                                      │
│  [Save Project Settings]             │
└──────────────────────────────────────┘
```

---

## 6. Хранение настроек

### 6.1 Глобальные настройки

Вариант A: YAML-файл `app/data/settings.yaml`
Вариант B: Таблица `settings` в БД (key-value)

Рекомендация: **Вариант B** (таблица в БД), чтобы настройки сохранялись между перезапусками и были доступны через API.

```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP
);
```

### 6.2 Безопасность API-ключей

- API-ключи хранятся зашифрованными (Fernet или аналог)
- В UI показываются замаскированными: `sk-...abc123`
- Передаются только при создании/обновлении, не возвращаются в GET

---

## 7. Backend Endpoints

```
GET  /settings                    → текущие глобальные настройки
PUT  /settings                    → обновить глобальные настройки
POST /settings/test-connection    → проверить подключение к LLM

GET  /settings/providers          → список доступных провайдеров
GET  /settings/models/{provider}  → список моделей для провайдера

PUT  /projects/{id}/settings      → обновить настройки проекта
GET  /projects/{id}/settings      → получить настройки проекта
```
