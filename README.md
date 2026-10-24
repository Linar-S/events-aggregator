# Events Aggregator

Backend-сервис агрегатор событий из Events Provider API.
Периодически синхронизирует события в локальную PostgreSQL, предоставляет REST API для работы с событиями и регистрациями.

**Часть 2 (Доработка):** реализован паттерн **Transactional Outbox** для гарантированной доставки уведомлений, интеграция с Notification-сервисом **Capashino**, поддержка **идемпотентности** при регистрации на мероприятие и мониторинг ошибок через **GlitchTip**.

## Стек
- Python 3.14, FastAPI, aiohttp
- PostgreSQL, SQLAlchemy 2.0 (async), Alembic
- sentry-sdk (интеграция с GlitchTip)
- uv, Ruff, pytest
- Docker, Kubernetes, GitHub Actions

## Запуск локально

1. Установить зависимости: `uv sync`
2. Скопировать `.env.example` → `.env` и заполнить переменные:
   ```env
   # Events Provider
   EVENTS_PROVIDER_BASE_URL=http://...
   EVENTS_PROVIDER_API_KEY=your_api_key

   # База данных
   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/events_aggregator

   # Capashino (уведомления)
   CAPASHINO_BASE_URL=http://student-system-capashino-web.student-system-capashino.svc:8000
   CAPASHINO_API_KEY=your_capashino_key

   # Настройки Outbox-воркера
   OUTBOX_POLL_INTERVAL_SECONDS=5
   OUTBOX_MAX_ATTEMPTS=10
   OUTBOX_BATCH_SIZE=50

   # Идемпотентность
   IDEMPOTENCY_KEY_TTL_SECONDS=86400

   # GlitchTip (Sentry)
   SENTRY_DSN=http://...