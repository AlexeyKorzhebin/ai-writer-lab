# AI Writer Lab — Инструкция по запуску

## 1. Клонирование репозитория

```bash
git clone https://github.com/AlexeyKorzhebin/ai-writer-lab.git
cd ai-writer-lab
```

---

## 2. Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

Если editable-режим не срабатывает:

```bash
pip install fastapi uvicorn sqlalchemy aiosqlite httpx jinja2 python-multipart openai
```

---

## 3. Настройка переменных окружения (LLM)

### Вариант A — OpenAI

```bash
export OPENAI_API_KEY=sk-...
```

### Вариант B — CAILA OpenAI-compatible

```bash
export OPENAI_API_KEY=<CAILA_API_KEY>
export OPENAI_BASE_URL=https://caila.io/api/adapters/openai/v1
```

---

## 4. Запуск сервера

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8017
```

Открыть в браузере:

```
http://127.0.0.1:8017
```

---

## 5. Проверка работоспособности

После запуска должно быть доступно:

- Создание проекта
- Создание главы
- Генерация главы
- Review
- Edit
- Produce High Quality
- Book-level consistency
- Экспорт PDF / DOCX / EPUB

---

## 6. Запуск тестов

```bash
source .venv/bin/activate
pytest -vv
```

Ожидаемый результат:

```
6 passed
```

---

## 7. Архитектурные особенности

- Async SQLAlchemy (без lazy loading)
- Eager loading Chapter → Project → Project.chapters
- Файловая test.db для тестов
- WriterPipeline + multi-agent orchestration

---

## 8. Режим разработки

```bash
uvicorn app.main:app --reload
```

Автоперезагрузка включена.
