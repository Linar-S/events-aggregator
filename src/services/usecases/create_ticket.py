import uuid
from datetime import UTC, datetime

from src.core.datetime_utils import ensure_aware_utc
from src.db.models import EventStatus, Ticket, TicketStatus
from src.db.repositories import (
    EventRepositoryProtocol,
    OutboxRepositoryProtocol,
    TicketRepositoryProtocol,
)
from src.services.events_provider import EventsProviderClient
from src.services.events_provider.exceptions import EventsProviderError
from src.services.usecases.exceptions import (
    EventNotFoundError,
    EventNotPublishedError,
    RegistrationClosedError,
    SeatNotAvailableError,
)


class CreateTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepositoryProtocol,
        tickets: TicketRepositoryProtocol,
        outbox: OutboxRepositoryProtocol,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets
        self._outbox = outbox

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

        if event.status != EventStatus.PUBLISHED:
            raise EventNotPublishedError(event.status)

        now = datetime.now(UTC)
        deadline = ensure_aware_utc(event.registration_deadline)
        if deadline <= now:
            raise RegistrationClosedError(deadline.isoformat())

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
            raise SeatNotAvailableError(str(exc)) from exc

        ticket = Ticket(
            id=str(uuid.uuid4()),
            event_id=event_id,
            external_ticket_id=external_ticket_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
            status=TicketStatus.ACTIVE,
        )
        saved = await self._tickets.create(ticket)

        # Создаём запись в outbox в той же транзакции.
        # Payload содержит всё необходимое для отправки уведомления.
        message = f"Вы успешно зарегистрированы на мероприятие - {event.name}, место {seat}"
        await self._outbox.create(
            event_type="ticket_purchased",
            payload={
                "ticket_id": saved.id,
                "event_id": event_id,
                "event_name": event.name,
                "seat": seat,
                "email": email,
                "message": message,
            },
        )

        return saved
