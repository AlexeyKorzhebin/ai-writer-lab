# Покрытие тестами спецификаций (`spec/*.md`)

Автотесты в `tests/spec/` сопоставлены с документами. Полное поведенческое покрытие UI (Alpine, drag-and-drop) — вручную / e2e; здесь — **API, доменная логика, наличие экранов и статики**.

| Спека | Файл | Что проверяют тесты |
|-------|------|---------------------|
| **UI_UX_OVERVIEW** | `test_spec_screens_static_export.py` | Главная, базовый layout-набор статики (CSS/JS/i18n), экспорт |
| **SCREENS_SPEC** | `test_spec_screens_static_export.py` | HTTP 200 для Home, Settings, Wizard, Workspace, Analytics при наличии проекта/спеки |
| **SETTINGS_AND_CONFIG** | `test_spec_settings_author_world.py` | `/settings`, `/api/settings`, providers, models, test-connection (ошибка без URL) |
| **AUTHOR_STYLE_PRESETS** | `test_spec_settings_author_world.py` | `/author-presets`, структура пресетов; sample с mock LLM |
| **WORLD_AND_LOCATIONS** | `test_spec_settings_author_world.py` | `/world-presets`, CRUD локаций, `world/import` (preset), `generate-locations` с mock |
| **AI_CHAT_AND_CONTEXT** | `test_spec_chat_context_domain.py`, `test_spec_domain_context.py` | `parse_references`, `resolve_reference`, `ContextBuilder`, `/chat/estimate`, sessions, new-task |
| **ILLUSTRATION_PROMPT_GENERATOR** | `test_spec_chat_illustrations_analytics.py` | `/illustration-templates`, варианты/промпт сцены с mock LLM |
| **UX_PATTERNS** | `test_spec_screens_static_export.py` | Наличие `app.js` (toast/theme), статика i18n `/static/i18n/*.json` |

Файлы спецификаций в `spec/`: `UI_UX_OVERVIEW.md`, `SCREENS_SPEC.md`, `SETTINGS_AND_CONFIG.md`, `WORLD_AND_LOCATIONS.md`, `UX_PATTERNS.md`, `ILLUSTRATION_PROMPT_GENERATOR.md`, `AUTHOR_STYLE_PRESETS.md`, `AI_CHAT_AND_CONTEXT.md`.

Запуск только спек-тестов:

```bash
uv run pytest tests/spec/ -v
# или по маркеру
uv run pytest -m spec -v
```
