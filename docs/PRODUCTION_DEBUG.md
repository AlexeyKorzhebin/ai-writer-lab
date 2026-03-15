# AI Writer Lab — Production Debug Log

## 2026-03-15 — Internal Server Error on /writer/

### Симптом
- HTTPS доступ работает
- nginx проксирует корректно
- Backend (systemd) запущен
- UI возвращает 500 Internal Server Error

### Диагностика

Через journalctl:

```
sqlalchemy.exc.OperationalError:
no such column: projects.temperature
```

SQL:

```
SELECT projects.id, projects.title, projects.description,
       projects.model_name, projects.temperature,
       projects.max_tokens, projects.author_name,
       projects.author_style
FROM projects
```

### Причина

Production база `writer.db` была создана до добавления новых колонок.

Тестовая база пересоздаётся автоматически через create_all().
Production база не мигрируется.

### Решение (временно)

1. Остановить сервис
2. Сделать backup writer.db
3. Удалить writer.db
4. Перезапустить сервис (create_all создаст актуальную схему)

### Долгосрочное решение

Добавить Alembic и полноценные миграции.

---

## Архитектурный вывод

- create_all() подходит только для прототипа
- Production требует миграционной стратегии
- systemd + nginx работает корректно
- Ошибка была на уровне схемы БД
