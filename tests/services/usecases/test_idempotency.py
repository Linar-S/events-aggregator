from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Event, Place
from src.db.repositories import (
    SQLAlchemyEventRepository,
    SQLAlchemyIdempotencyRepository,
    SQLAlchemyOutboxRepository,
    SQLAlchemyPlaceRepository,
    SQLAlchemyTicketRepository,
)
from src.services.usecases.create_ticket import CreateTicketUsecase
from src.services.usecases.exceptions import IdempotencyConflictError


class FakeEventsProviderClient:
    def __init__(self) -> None:
        self.call_count = 0

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
        self.call_count += 1
        return f"external-{self.call_count}"


async def _setup_event(db_session: AsyncSession) -> None:
    place = Place(
        id="place-1",
        name="Зал",
        city="Москва",
        address="ул. 1",
        seats_pattern="A1-10",
    )
    await SQLAlchemyPlaceRepository(db_session).upsert(place)

    event = Event(
        id="event-1",
        name="Событие",
        place_id="place-1",
        event_time=datetime.now(UTC) + timedelta(days=1),
        registration_deadline=datetime.now(UTC) + timedelta(hours=12),
        status="published",
        number_of_visitors=0,
    )
    await SQLAlchemyEventRepository(db_session).upsert(event)


async def _make_usecase(db_session: AsyncSession, client: FakeEventsProviderClient):
    return CreateTicketUsecase(
        client=client,
        events=SQLAlchemyEventRepository(db_session),
        tickets=SQLAlchemyTicketRepository(db_session),
        outbox=SQLAlchemyOutboxRepository(db_session),
        idempotency=SQLAlchemyIdempotencyRepository(db_session),
    )


async def test_idempotency_returns_same_ticket(db_session: AsyncSession) -> None:
    await _setup_event(db_session)
    client = FakeEventsProviderClient()
    usecase = await _make_usecase(db_session, client)

    t1 = await usecase.do(
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A1",
        idempotency_key="key-1",
    )

    t2 = await usecase.do(
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A1",
        idempotency_key="key-1",
    )

    assert t1.id == t2.id
    # Внешний API должен быть вызван только ОДИН раз
    assert client.call_count == 1


async def test_idempotency_conflict_on_different_data(
    db_session: AsyncSession,
) -> None:
    await _setup_event(db_session)
    client = FakeEventsProviderClient()
    usecase = await _make_usecase(db_session, client)

    await usecase.do(
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A1",
        idempotency_key="key-1",
    )

    with pytest.raises(IdempotencyConflictError):
        await usecase.do(
            event_id="event-1",
            first_name="Иван",
            last_name="Иванов",
            email="ivan@example.com",
            seat="A2",  # другое место
            idempotency_key="key-1",
        )


async def test_without_key_creates_new_tickets(db_session: AsyncSession) -> None:
    await _setup_event(db_session)
    client = FakeEventsProviderClient()
    usecase = await _make_usecase(db_session, client)

    t1 = await usecase.do(
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A1",
    )
    t2 = await usecase.do(
        event_id="event-1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A1",
    )

    # Без ключа каждый запрос — новый тикет
    assert t1.id != t2.id
    assert client.call_count == 2
