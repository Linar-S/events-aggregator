from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Event, OutboxStatus, Place
from src.db.repositories import (
    SQLAlchemyEventRepository,
    SQLAlchemyOutboxRepository,
    SQLAlchemyPlaceRepository,
    SQLAlchemyTicketRepository,
)
from src.services.usecases.create_ticket import CreateTicketUsecase


class FakeEventsProviderClient:
    async def seats(self, event_id: str) -> list[str]:
        return ["A1", "A2", "B5"]

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        seat: str,
        email: str,
    ) -> str:
        return "external-ticket-123"


async def _setup_event(db_session: AsyncSession, status: str = "published") -> Event:
    place = Place(
        id="place-1",
        name="Тестовый зал",
        city="Москва",
        address="ул. Тестовая, 1",
        seats_pattern="A1-10",
    )
    await SQLAlchemyPlaceRepository(db_session).upsert(place)

    event = Event(
        id="event-1",
        name="Тестовое событие",
        place_id="place-1",
        event_time=datetime.now(UTC) + timedelta(days=1),
        registration_deadline=datetime.now(UTC) + timedelta(hours=12),
        status=status,
        number_of_visitors=0,
    )
    await SQLAlchemyEventRepository(db_session).upsert(event)
    return event


async def test_create_ticket_creates_outbox_entry(db_session: AsyncSession) -> None:
    await _setup_event(db_session)

    usecase = CreateTicketUsecase(
        client=FakeEventsProviderClient(),
        events=SQLAlchemyEventRepository(db_session),
        tickets=SQLAlchemyTicketRepository(db_session),
        outbox=SQLAlchemyOutboxRepository(db_session),
    )

    ticket = await usecase.do(
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A1",
    )

    assert ticket.id is not None
    assert ticket.status == "active"

    outbox_repo = SQLAlchemyOutboxRepository(db_session)
    pending = await outbox_repo.fetch_pending()
    assert len(pending) == 1
    entry = pending[0]
    assert entry.event_type == "ticket_purchased"
    assert entry.status == OutboxStatus.PENDING
    assert entry.payload["ticket_id"] == ticket.id
    assert entry.payload["event_id"] == "event-1"
    assert entry.payload["seat"] == "A1"
    assert "Тестовое событие" in entry.payload["message"]
