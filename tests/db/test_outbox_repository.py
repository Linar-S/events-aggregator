from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import OutboxStatus
from src.db.repositories import SQLAlchemyOutboxRepository


async def test_outbox_create_sets_pending(db_session: AsyncSession) -> None:
    repo = SQLAlchemyOutboxRepository(db_session)

    entry = await repo.create(
        event_type="ticket_purchased",
        payload={"ticket_id": "abc", "message": "Hello"},
    )

    assert entry.id is not None
    assert entry.status == OutboxStatus.PENDING
    assert entry.attempts == 0
    assert entry.payload == {"ticket_id": "abc", "message": "Hello"}


async def test_outbox_fetch_pending_returns_only_pending(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyOutboxRepository(db_session)

    e1 = await repo.create(event_type="ticket_purchased", payload={"n": 1})
    e2 = await repo.create(event_type="ticket_purchased", payload={"n": 2})
    e3 = await repo.create(event_type="ticket_purchased", payload={"n": 3})

    await repo.mark_sent(e2.id)

    pending = await repo.fetch_pending(limit=10)

    ids = [e.id for e in pending]
    assert e1.id in ids
    assert e3.id in ids
    assert e2.id not in ids


async def test_outbox_mark_sent_sets_status_and_timestamp(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyOutboxRepository(db_session)
    entry = await repo.create(event_type="ticket_purchased", payload={})

    await repo.mark_sent(entry.id)

    refreshed = await db_session.get(type(entry), entry.id)
    assert refreshed is not None
    assert refreshed.status == OutboxStatus.SENT
    assert refreshed.sent_at is not None


async def test_outbox_mark_failed_increments_attempts(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyOutboxRepository(db_session)
    entry = await repo.create(event_type="ticket_purchased", payload={})

    await repo.mark_failed(entry.id, "connection timeout", max_attempts=3)

    refreshed = await db_session.get(type(entry), entry.id)
    assert refreshed is not None
    assert refreshed.attempts == 1
    assert refreshed.last_error == "connection timeout"
    assert refreshed.status == OutboxStatus.PENDING  # ещё не лимит


async def test_outbox_mark_failed_after_max_attempts_sets_failed(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyOutboxRepository(db_session)
    entry = await repo.create(event_type="ticket_purchased", payload={})

    for _ in range(3):
        await repo.mark_failed(entry.id, "err", max_attempts=3)

    refreshed = await db_session.get(type(entry), entry.id)
    assert refreshed is not None
    assert refreshed.attempts == 3
    assert refreshed.status == OutboxStatus.FAILED
