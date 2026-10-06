class EventsProviderError(Exception):
    """Базовое исключение для ошибок Events Provider API."""


class EventsProviderAuthError(EventsProviderError):
    """401 — ключ неверный или отсутствует."""


class EventsProviderNotFoundError(EventsProviderError):
    """404 — ресурс не найден."""


class EventsProviderBadRequestError(EventsProviderError):
    """400 — некорректные данные."""

    def __init__(self, message: str, details: object | None = None) -> None:
        super().__init__(message)
        self.details = details


class EventsProviderServerError(EventsProviderError):
    """5xx — ошибка на стороне Events Provider."""
