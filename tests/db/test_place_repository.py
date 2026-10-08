from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Place
from src.db.repositories import SQLAlchemyPlaceRepository


def _place(place_id: str = "place-1") -> Place:
    return Place(
        id=place_id,
        name="Технопарк",
        city="Москва",
        address="ул. Ленина, 1",
        seats_pattern="A1-10,B1-20",
        changed_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )


async def test_place_upsert_inserts_new(db_session: AsyncSession) -> None:
    repo = SQLAlchemyPlaceRepository(db_session)
    place = _place()

    saved = await repo.upsert(place)

    assert saved.id == "place-1"
    assert saved.name == "Технопарк"

    fetched = await repo.get("place-1")
    assert fetched is not None
    assert fetched.city == "Москва"


async def test_place_upsert_updates_existing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyPlaceRepository(db_session)

    await repo.upsert(_place())

    updated = _place()
    updated.name = "Новое имя"
    updated.city = "Казань"
    await repo.upsert(updated)

    fetched = await repo.get("place-1")
    assert fetched is not None
    assert fetched.name == "Новое имя"
    assert fetched.city == "Казань"


async def test_place_get_missing_returns_none(db_session: AsyncSession) -> None:
    repo = SQLAlchemyPlaceRepository(db_session)

    result = await repo.get("nonexistent")

    assert result is None
