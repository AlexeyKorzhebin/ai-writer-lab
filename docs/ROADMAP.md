# AI Writer Lab — Product & Architecture Roadmap

Дата фиксации: 2026-03-15
Статус: Production baseline стабилен

---

# 0. Текущая точка (Baseline)

✅ Production-ready инфраструктура:
- systemd сервис
- nginx reverse proxy (HTTPS)
- CAILA (OpenAI-compatible)
- Alembic (миграции)
- Async SQLAlchemy (без lazy loading)
- E2E протестированы: generate, review, edit, orchestration, export

Это версия 0.1 — стабильный исследовательский прототип.

---

# 1. Phase I — Архитектурное усиление (Core Stability)

## 1.1 Убрать create_all() из runtime
- Полный переход на Alembic
- Startup без create_all

## 1.2 Repository слой
- Изолировать ORM от бизнес-логики
- Убрать передачу ORM-объектов в pipeline
- Ввести DTO слой

## 1.3 LLM abstraction layer
- Поддержка нескольких провайдеров
- Retry logic
- Structured logging
- Timeout + circuit breaker

## 1.4 Конфигурационный слой
- Pydantic settings
- .env support
- Разделение dev/prod

Ожидаемый результат: версия 0.2 — архитектурно зрелый backend.

---

# 2. Phase II — Улучшение Writer Engine

## 2.1 Memory Layer
- Vector store (pgvector или SQLite FTS)
- Long-term book memory
- Chapter-to-chapter consistency

## 2.2 Iterative drafting loop
- Draft → Review → Edit → Refine x N
- Configurable depth

## 2.3 Style embedding
- Author profile embedding
- Tone reinforcement

## 2.4 Multi-model routing
- Cheap model for draft
- Strong model for refinement

Ожидаемый результат: версия 0.3 — интеллектуальный long-form writer.

---

# 3. Phase III — UX & Productization

## 3.1 Versioning
- Chapter versions
- Diff view
- Rollback

## 3.2 Outline Builder UI
- Visual chapter structure
- Drag & drop

## 3.3 Book Dashboard
- Consistency metrics
- Style drift detection
- Coverage view

## 3.4 Async background jobs
- Long operations через task queue
- Progress tracking

Ожидаемый результат: версия 0.4 — usable product.

---

# 4. Phase IV — Advanced AI Features

## 4.1 Book-level rewrite engine
- Full-book transformation
- Genre adaptation
- Audience targeting

## 4.2 Knowledge injection
- External sources
- Citation mode

## 4.3 Structured output mode
- Academic mode
- Technical documentation mode

## 4.4 Plugin architecture
- Custom agents
- Prompt modules

Ожидаемый результат: версия 0.5 — AI writing platform.

---

# 5. Infrastructure Evolution

## 5.1 Database upgrade path
- Переход SQLite → PostgreSQL
- pgvector

## 5.2 Horizontal scaling
- Gunicorn + Uvicorn workers
- Separate API and background workers

## 5.3 Observability
- Structured logs
- Metrics (Prometheus)
- Error tracking (Sentry)

---

# 6. Non-Goals (пока)

- Multi-user auth
- SaaS billing
- Public API

---

# 7. Приоритет на ближайшие 2 спринта

Sprint 1:
- Remove create_all
- Repository layer
- Structured config

Sprint 2:
- Vector memory
- Iterative drafting loop
- Versioning

---

# Стратегическое видение

AI Writer Lab → Agent-based long-form authoring engine.

Не просто генератор текста, а:
- интеллектуальный редактор
- архитектурно управляемый процесс написания книги
- модульная агентная система

---

Документ является живым. Обновлять после каждого архитектурного скачка.
