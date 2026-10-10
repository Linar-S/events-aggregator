from datetime import UTC, datetime

from src.db.models import TicketStatus
from src.db.repositories import (
    EventRepositoryProtocol,
    TicketRepositoryProtocol,
)
from src.services.events_provider import EventsProviderClient
from src.services.events_provider.exceptions import EventsProviderError
from src.services.usecases.exceptions import (
    EventAlreadyPastError,
    TicketNotFoundError,
)


class CancelTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepositoryProtocol,
        tickets: TicketRepositoryProtocol,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets

    async def do(self, *, ticket_id: str) -> None:
        ticket = await self._tickets.get_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ticket_id)

        event = await self._events.get(ticket.event_id)
        if event is None:
            raise TicketNotFoundError(ticket_id)

        if event.event_time <= datetime.now(UTC):
            raise EventAlreadyPastError(event.event_time.isoformat())

        try:
            await self._client.unregister(event.id, ticket.external_ticket_id)
        except EventsProviderError as exc:
            raise TicketNotFoundError(str(exc)) from exc

        await self._tickets.update_status(ticket.id, TicketStatus.CANCELLED)
