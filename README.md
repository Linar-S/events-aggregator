# Events Aggregator

Backend-сервис агрегатор событий из Events Provider API.
Периодически синхронизирует события в локальную PostgreSQL, 
предоставляет REST API для работы с событиями и регистрациями.

## Стек
- Python 3.14, FastAPI, aiohttp
- PostgreSQL, SQLAlchemy 2.0 (async), Alembic
- uv, Ruff, pytest
- Docker, Kubernetes, GitHub Actions

## Запуск локально

1. Установить зависимости: `uv sync`
2. Скопировать `.env.example` → `.env`, заполнить:
   - `EVENTS_PROVIDER_BASE_URL` — URL Events Provider API
   - `EVENTS_PROVIDER_API_KEY` — API-ключ
   - `DATABASE_URL` — PostgreSQL URL
3. Применить миграции: `uv run alembic upgrade head`
4. Запустить: `uv run python -m src.main`

Приложение доступно на `http://localhost:8000`.

## API

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/health` | Health check |
| POST | `/api/sync/trigger` | Ручной запуск синхронизации |
| GET | `/api/events` | Список событий (page, page_size, date_from) |
| GET | `/api/events/{event_id}` | Детали события |
| GET | `/api/events/{event_id}/seats` | Свободные места (кэш 30 сек) |
| POST | `/api/tickets` | Регистрация на событие (201) |
| DELETE | `/api/tickets/{ticket_id}` | Отмена регистрации (200) |

## Разработка

```bash
# Тесты
uv run pytest -v

# Линтер
uv run ruff check . --fix
uv run ruff format .

# Миграции
uv run alembic revision --autogenerate -m "описание"
uv run alembic upgrade head