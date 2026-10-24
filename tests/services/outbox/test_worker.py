from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Outbox, OutboxStatus
from src.db.repositories import SQLAlchemyOutboxRepository
from src.services.outbox.worker import process_batch


async def test_process_batch_marks_sent_on_success(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyOutboxRepository(db_session)
    entry = await repo.create(
        event_type="ticket_purchased",
        payload={"ticket_id": "abc", "message": "Hello"},
    )

    sent: list[str] = []

    async def fake_handler(e: Outbox) -> None:
        sent.append(e.id)

    processed = await process_batch(
        db_session,
        batch_size=10,
        max_attempts=3,
        handler=fake_handler,
    )

    assert processed == 1
    assert sent == [entry.id]

    refreshed = await db_session.get(Outbox, entry.id)
    assert refreshed is not None
    assert refreshed.status == OutboxStatus.SENT
    assert refreshed.sent_at is not None


async def test_process_batch_marks_failed_on_error(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyOutboxRepository(db_session)
    entry = await repo.create(
        event_type="ticket_purchased",
        payload={"ticket_id": "abc"},
    )

    async def failing_handler(_: Outbox) -> None:
        raise RuntimeError("capashino is down")

    processed = await process_batch(
        db_session,
        batch_size=10,
        max_attempts=3,
        handler=failing_handler,
    )

    assert processed == 1

    refreshed = await db_session.get(Outbox, entry.id)
    assert refreshed is not None
    assert refreshed.attempts == 1
    assert refreshed.last_error == "capashino is down"
    assert refreshed.status == OutboxStatus.PENDING  # не достигли лимита


async def test_process_batch_empty_returns_zero(
    db_session: AsyncSession,
) -> None:
    processed = await process_batch(
        db_session,
        batch_size=10,
        max_attempts=3,
    )
    assert processed == 0
