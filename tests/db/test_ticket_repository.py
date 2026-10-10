import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Event, Place, Ticket
from src.db.repositories import (
    SQLAlchemyEventRepository,
    SQLAlchemyPlaceRepository,
    SQLAlchemyTicketRepository,
)


def _place() -> Place:
    return Place(
        id="place-1",
        name="Place",
        city="City",
        address="Addr",
        seats_pattern="A1-10",
    )


def _event() -> Event:
    return Event(
        id="evt-1",
        name="Event 1",
        place_id="place-1",
        event_time=datetime(2026, 1, 11, 17, 0, tzinfo=UTC),
        registration_deadline=datetime(2026, 1, 10, 17, 0, tzinfo=UTC),
        status="published",
        number_of_visitors=0,
    )


async def _setup(db_session: AsyncSession) -> None:
    await SQLAlchemyPlaceRepository(db_session).upsert(_place())
    await SQLAlchemyEventRepository(db_session).upsert(_event())


async def test_ticket_create_and_get(db_session: AsyncSession) -> None:
    await _setup(db_session)
    repo = SQLAlchemyTicketRepository(db_session)

    ticket = Ticket(
        id=str(uuid.uuid4()),
        event_id="evt-1",
        external_ticket_id="external-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A5",
    )

    saved = await repo.create(ticket)

    assert saved.id == ticket.id
    fetched = await repo.get_by_external_id("external-1")
    assert fetched is not None
    assert fetched.seat == "A5"


async def test_ticket_update_status(db_session: AsyncSession) -> None:
    await _setup(db_session)
    repo = SQLAlchemyTicketRepository(db_session)

    ticket = Ticket(
        id=str(uuid.uuid4()),
        event_id="evt-1",
        external_ticket_id="external-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A5",
        status="active",
    )
    await repo.create(ticket)

    await repo.update_status(ticket.id, "cancelled")

    fetched = await repo.get_by_external_id("external-1")
    assert fetched is not None
    assert fetched.status == "cancelled"


async def test_ticket_get_missing_returns_none(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTicketRepository(db_session)

    result = await repo.get_by_external_id("nonexistent")

    assert result is None
