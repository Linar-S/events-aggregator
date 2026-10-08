from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Place


class SQLAlchemyPlaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, place: Place) -> Place:
        existing = await self._session.get(Place, place.id)
        if existing is None:
            self._session.add(place)
            await self._session.flush()
            return place

        existing.name = place.name
        existing.city = place.city
        existing.address = place.address
        existing.seats_pattern = place.seats_pattern
        existing.changed_at = place.changed_at
        existing.created_at = place.created_at
        await self._session.flush()
        return existing

    async def get(self, place_id: str) -> Place | None:
        result = await self._session.execute(select(Place).where(Place.id == place_id))
        return result.scalar_one_or_none()
