from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Event


class SQLAlchemyEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, event_id: str) -> Event | None:
        result = await self._session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        date_from: date | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Event], int]:
        stmt = select(Event)

        if date_from is not None:
            boundary = datetime.combine(date_from, datetime.min.time())
            stmt = stmt.where(Event.event_time >= boundary)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Event.event_time.asc()).offset(offset).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()

        return rows, total

    async def upsert(self, event: Event) -> Event:
        existing = await self._session.get(Event, event.id)
        if existing is None:
            self._session.add(event)
            await self._session.flush()
            return event

        existing.name = event.name
        existing.place_id = event.place_id
        existing.event_time = event.event_time
        existing.registration_deadline = event.registration_deadline
        existing.status = event.status
        existing.number_of_visitors = event.number_of_visitors
        existing.changed_at = event.changed_at
        existing.external_created_at = event.external_created_at
        existing.status_changed_at = event.status_changed_at
        await self._session.flush()
        return existing
