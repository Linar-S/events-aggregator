from enum import StrEnum


class EventStatus(StrEnum):
    """Статусы события из Events Provider API.

    Значения — строки, потому что API может добавлять новые статусы,
    и мы не хотим падать на незнакомом. Enum используется только в коде
    для типобезопасных сравнений.
    """

    NEW = "new"
    PUBLISHED = "published"
    REGISTRATION_CLOSED = "registration_closed"
    FINISHED = "finished"


class TicketStatus(StrEnum):
    """Статусы тикета в нашей БД."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
