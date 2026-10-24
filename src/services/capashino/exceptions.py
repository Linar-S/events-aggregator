class CapashinoError(Exception):
    """Базовое исключение для ошибок Capashino API."""


class CapashinoAuthError(CapashinoError):
    """401 — неверный API-ключ."""


class CapashinoBadRequestError(CapashinoError):
    """400 / 422 — некорректные данные."""

    def __init__(self, message: str, details: object | None = None) -> None:
        super().__init__(message)
        self.details = details


class CapashinoConflictError(CapashinoError):
    """409 — уведомление с таким idempotency_key уже существует.

    Для нас это не ошибка — значит, уведомление уже доставлено ранее.
    """


class CapashinoServerError(CapashinoError):
    """5xx — ошибка на стороне Capashino."""
