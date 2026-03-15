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

### Production (CAILA — текущая рабочая схема)

В окружении сервера уже присутствует `CAILA_API_KEY`.

Нужно пробросить его в OpenAI-совместимые переменные:

```bash
export OPENAI_API_KEY=$CAILA_API_KEY
export OPENAI_BASE_URL=https://caila.io/api/adapters/openai/v1
```

Проверка:

```bash
echo $OPENAI_API_KEY
```

---

## 4. Запуск сервера (локально)

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

---

# 9. Production запуск через nginx

## Текущая рабочая схема

- Uvicorn слушает: `127.0.0.1:8017`
- nginx проксирует: `/writer/`
- Домен: `https://elion.black-castle.ru/writer/`

### Конфигурация nginx

Файл:

```
/etc/nginx/sites-enabled/elion.black-castle.ru
```

Ключевой блок:

```nginx
location /writer/ {
    rewrite ^/writer/(.*)$ /$1 break;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    proxy_pass http://127.0.0.1:8017;
}
```

### Запуск production

1. Запустить uvicorn:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8017
```

2. Проверить nginx:

```bash
sudo systemctl status nginx
```

3. Открыть в браузере:

```
https://elion.black-castle.ru/writer/
```

---

## SSL

- Let's Encrypt
- Сертификаты находятся в:

```
/etc/letsencrypt/live/elion.black-castle.ru/
```

---

## Проверка работы прокси

Если приложение работает локально, но не работает через домен:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Важное замечание

Текущая схема использует rewrite `/writer/` → `/`.
В будущем рекомендуется добавить `root_path="/writer"` в FastAPI для полной production-совместимости.
