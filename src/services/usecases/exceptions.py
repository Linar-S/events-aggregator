class EventNotFoundError(Exception):
    """Событие не найдено в нашей БД."""


class EventNotPublishedError(Exception):
    """Событие не published — операция невозможна."""


class RegistrationClosedError(Exception):
    """Дедлайн регистрации прошёл."""


class SeatNotAvailableError(Exception):
    """Выбранное место недоступно."""


class EventAlreadyPastError(Exception):
    """Событие уже прошло — операция невозможна."""


class TicketNotFoundError(Exception):
    """Тикет не найден в нашей БД."""


class EventsProviderUnavailableError(Exception):
    """Внешний API Events Provider вернул ошибку."""
