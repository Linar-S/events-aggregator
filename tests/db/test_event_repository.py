from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Event, Place
from src.db.repositories import SQLAlchemyEventRepository, SQLAlchemyPlaceRepository


def _place() -> Place:
    return Place(
        id="place-1",
        name="Технопарк",
        city="Москва",
        address="ул. Ленина, 1",
        seats_pattern="A1-10",
    )


def _event(
    event_id: str,
    event_time: datetime,
    *,
    status: str = "published",
) -> Event:
    return Event(
        id=event_id,
        name=f"Event {event_id}",
        place_id="place-1",
        event_time=event_time,
        registration_deadline=event_time - timedelta(days=1),
        status=status,
        number_of_visitors=0,
        changed_at=datetime.now(UTC),
    )


async def test_event_upsert_inserts_new(db_session: AsyncSession) -> None:
    await SQLAlchemyPlaceRepository(db_session).upsert(_place())
    repo = SQLAlchemyEventRepository(db_session)

    when = datetime(2026, 1, 11, 17, 0, tzinfo=UTC)
    saved = await repo.upsert(_event("evt-1", when))

    assert saved.id == "evt-1"
    fetched = await repo.get("evt-1")
    assert fetched is not None
    assert fetched.name == "Event evt-1"


async def test_event_upsert_updates_existing(db_session: AsyncSession) -> None:
    await SQLAlchemyPlaceRepository(db_session).upsert(_place())
    repo = SQLAlchemyEventRepository(db_session)

    when = datetime(2026, 1, 11, 17, 0, tzinfo=UTC)
    await repo.upsert(_event("evt-1", when))

    updated = _event("evt-1", when, status="registration_closed")
    updated.name = "Обновлённое имя"
    await repo.upsert(updated)

    fetched = await repo.get("evt-1")
    assert fetched is not None
    assert fetched.name == "Обновлённое имя"
    assert fetched.status == "registration_closed"


async def test_event_list_returns_all(db_session: AsyncSession) -> None:
    await SQLAlchemyPlaceRepository(db_session).upsert(_place())
    repo = SQLAlchemyEventRepository(db_session)

    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    for i in range(5):
        await repo.upsert(_event(f"evt-{i}", base + timedelta(days=i)))

    rows, total = await repo.list(offset=0, limit=10)

    assert total == 5
    assert len(rows) == 5
    # порядок по event_time
    assert rows[0].id == "evt-0"
    assert rows[-1].id == "evt-4"


async def test_event_list_filters_by_date_from(db_session: AsyncSession) -> None:
    await SQLAlchemyPlaceRepository(db_session).upsert(_place())
    repo = SQLAlchemyEventRepository(db_session)

    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    for i in range(5):
        await repo.upsert(_event(f"evt-{i}", base + timedelta(days=i)))

    rows, total = await repo.list(date_from=date(2026, 1, 3), offset=0, limit=10)

    assert total == 3
    assert {r.id for r in rows} == {"evt-2", "evt-3", "evt-4"}


async def test_event_list_paginates(db_session: AsyncSession) -> None:
    await SQLAlchemyPlaceRepository(db_session).upsert(_place())
    repo = SQLAlchemyEventRepository(db_session)

    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    for i in range(5):
        await repo.upsert(_event(f"evt-{i}", base + timedelta(days=i)))

    page1, total = await repo.list(offset=0, limit=2)
    page2, _ = await repo.list(offset=2, limit=2)

    assert total == 5
    assert [r.id for r in page1] == ["evt-0", "evt-1"]
    assert [r.id for r in page2] == ["evt-2", "evt-3"]
