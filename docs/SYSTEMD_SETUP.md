# AI Writer Lab — Production systemd Setup

## Цель
Запуск AI Writer Lab как полноценного systemd-сервиса.

---

# 1. Unit файл

Создаётся файл:

```
/etc/systemd/system/ai-writer.service
```

Содержимое:

```ini
[Unit]
Description=AI Writer Lab (Uvicorn)
After=network.target

[Service]
User=openclaw
WorkingDirectory=/home/openclaw/projects/ai-writer-lab

Environment="OPENAI_API_KEY=${CAILA_API_KEY}"
Environment="OPENAI_BASE_URL=https://caila.io/api/adapters/openai/v1"

ExecStart=/home/openclaw/projects/ai-writer-lab/.venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8017

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

# 2. Активация

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-writer
sudo systemctl start ai-writer
```

---

# 3. Проверка статуса

```bash
sudo systemctl status ai-writer
```

Просмотр логов:

```bash
journalctl -u ai-writer -f
```

---

# 4. Перезапуск

```bash
sudo systemctl restart ai-writer
```

---

# 5. Архитектурная схема

Browser → HTTPS → nginx → 127.0.0.1:8017 → Uvicorn (systemd)

---

# 6. Важно

- Uvicorn НЕ запускать вручную
- Управление только через systemctl
- Логи только через journalctl
