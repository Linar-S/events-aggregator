from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Outbox, OutboxStatus


class SQLAlchemyOutboxRepository:
    """Репозиторий для работы с Transactional Outbox."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, event_type: str, payload: dict) -> Outbox:
        """Создать запись в outbox со статусом pending.

        Важно: не делает commit — коммит выполняется на уровне сессии
        (в get_session), чтобы запись сохранялась в одной транзакции
        с бизнес-действием (например, созданием тикета).
        """
        entry = Outbox(
            event_type=event_type,
            payload=payload,
            status=OutboxStatus.PENDING,
            attempts=0,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def fetch_pending(self, limit: int = 50) -> Sequence[Outbox]:
        """Получить pending-записи для отправки.

        Сортировка по created_at (FIFO), чтобы не терять события
        и не «голодить» старые.
        """
        stmt = (
            select(Outbox)
            .where(Outbox.status == OutboxStatus.PENDING)
            .order_by(Outbox.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_sent(self, outbox_id: str) -> None:
        """Пометить как отправленную."""
        entry = await self._session.get(Outbox, outbox_id)
        if entry is None:
            return
        entry.status = OutboxStatus.SENT
        entry.sent_at = datetime.now(UTC)
        await self._session.flush()

    async def mark_failed(
        self,
        outbox_id: str,
        error: str,
        max_attempts: int,
    ) -> None:
        """Увеличить attempts и записать ошибку.

        Если attempts >= max_attempts — перевести в статус failed.
        Иначе — оставить pending для повторной попытки.
        """
        entry = await self._session.get(Outbox, outbox_id)
        if entry is None:
            return

        entry.attempts += 1
        entry.last_error = error[:2000]

        if entry.attempts >= max_attempts:
            entry.status = OutboxStatus.FAILED

        await self._session.flush()
