import uuid
from datetime import UTC, datetime

from src.db.models import Ticket
from src.db.repositories import (
    EventRepositoryProtocol,
    TicketRepositoryProtocol,
)
from src.services.events_provider import EventsProviderClient
from src.services.events_provider.exceptions import EventsProviderError


class EventNotFoundError(Exception):
    """Событие не найдено в нашей БД."""


class EventNotPublishedError(Exception):
    """Событие не published — регистрация невозможна."""


class RegistrationClosedError(Exception):
    """Дедлайн регистрации прошёл."""


class SeatNotAvailableError(Exception):
    """Выбранное место недоступно."""


class CreateTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepositoryProtocol,
        tickets: TicketRepositoryProtocol,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets

    async def do(
        self,
        *,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> Ticket:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFoundError(event_id)

        if event.status != "published":
            raise EventNotPublishedError(event.status)

        now = datetime.now(UTC)
        if event.registration_deadline <= now:
            raise RegistrationClosedError(event.registration_deadline.isoformat())

        try:
            available = await self._client.seats(event_id)
        except EventsProviderError as exc:
            raise SeatNotAvailableError(str(exc)) from exc

        if seat not in available:
            raise SeatNotAvailableError(f"Seat {seat} is not available")

        try:
            external_ticket_id = await self._client.register(
                event_id=event_id,
                first_name=first_name,
                last_name=last_name,
                seat=seat,
                email=email,
            )
        except EventsProviderError as exc:
            details = getattr(exc, "details", None)
            raise SeatNotAvailableError(f"{exc} | details={details}") from exc

        ticket = Ticket(
            id=str(uuid.uuid4()),
            event_id=event_id,
            external_ticket_id=external_ticket_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
            status="active",
        )
        return await self._tickets.create(ticket)
