from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import IdempotencyKey


class SQLAlchemyIdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: str) -> IdempotencyKey | None:
        return await self._session.get(IdempotencyKey, key)

    async def create(
        self,
        key: str,
        ticket_id: str,
        request_hash: str,
        expires_at: datetime,
    ) -> IdempotencyKey:
        entry = IdempotencyKey(
            key=key,
            ticket_id=ticket_id,
            request_hash=request_hash,
            expires_at=expires_at,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def delete(self, key: str) -> None:
        entry = await self.get(key)
        if entry:
            await self._session.delete(entry)
            await self._session.flush()
