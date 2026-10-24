from datetime import UTC, datetime


def ensure_aware_utc(value: datetime) -> datetime:
    """Привести datetime к UTC-aware.

    В production PostgreSQL возвращает aware datetime (TIMESTAMPTZ).
    В тестах SQLite не поддерживает таймзоны и возвращает naive.
    Этот хелпер нормализует оба случая — сравнения работают везде.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
