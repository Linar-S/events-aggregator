import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from src.core.config import get_settings
from src.core.datetime_utils import ensure_aware_utc
from src.db.models import EventStatus, Ticket, TicketStatus
from src.db.repositories import (
    EventRepositoryProtocol,
    IdempotencyRepositoryProtocol,
    OutboxRepositoryProtocol,
    TicketRepositoryProtocol,
)
from src.services.events_provider import EventsProviderClient
from src.services.events_provider.exceptions import EventsProviderError
from src.services.usecases.exceptions import (
    EventNotFoundError,
    EventNotPublishedError,
    IdempotencyConflictError,
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
        idempotency: IdempotencyRepositoryProtocol,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets
        self._outbox = outbox
        self._idempotency = idempotency

    async def do(
        self,
        *,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
        idempotency_key: str | None = None,
    ) -> Ticket:
        # 1. Проверка идемпотентности
        request_hash = hashlib.sha256(
            f"{event_id}|{first_name}|{last_name}|{email}|{seat}".encode()
        ).hexdigest()

        if idempotency_key:
            existing = await self._idempotency.get(idempotency_key)
            if existing:
                if existing.request_hash != request_hash:
                    raise IdempotencyConflictError(
                        "Idempotency key reused with different request data"
                    )
                ticket = await self._tickets.get_by_id(existing.ticket_id)
                if ticket:
                    return ticket
                # Если тикета нет (редкий кейс) — удаляем ключ и идем как новый
                await self._idempotency.delete(idempotency_key)

        # 2. Обычная логика
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

        # Проверяем, не возвращает ли внешний API старый ticket_id для этого места
        existing_ticket = await self._tickets.get_by_event_and_external_id(
            event_id, external_ticket_id
        )

        if existing_ticket:
            # Обновляем данные существующего тикета и возвращаем его
            existing_ticket.first_name = first_name
            existing_ticket.last_name = last_name
            existing_ticket.email = email
            existing_ticket.status = TicketStatus.ACTIVE
            saved = existing_ticket
        else:
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

        # 3. Сохраняем ключ идемпотентности ТОЛЬКО после успешной регистрации
        if idempotency_key:
            settings = get_settings()
            expires_at = now + timedelta(seconds=settings.idempotency_key_ttl_seconds)
            await self._idempotency.create(
                key=idempotency_key,
                ticket_id=saved.id,
                request_hash=request_hash,
                expires_at=expires_at,
            )

        # 4. Outbox
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
