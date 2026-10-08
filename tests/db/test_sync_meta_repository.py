from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import SyncMeta
from src.db.repositories import SQLAlchemySyncMetaRepository


async def test_sync_meta_get_returns_none_when_empty(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemySyncMetaRepository(db_session)

    assert await repo.get() is None


async def test_sync_meta_upsert_inserts_new(db_session: AsyncSession) -> None:
    repo = SQLAlchemySyncMetaRepository(db_session)

    meta = SyncMeta(
        last_sync_time=datetime.now(UTC),
        last_changed_at="2026-01-05T15:30:00+03:00",
        sync_status="success",
    )
    saved = await repo.upsert(meta)

    assert saved.id == 1
    fetched = await repo.get()
    assert fetched is not None
    assert fetched.sync_status == "success"
    assert fetched.last_changed_at == "2026-01-05T15:30:00+03:00"


async def test_sync_meta_upsert_updates_existing(db_session: AsyncSession) -> None:
    repo = SQLAlchemySyncMetaRepository(db_session)

    await repo.upsert(
        SyncMeta(
            last_changed_at="2026-01-05T15:30:00+03:00",
            sync_status="success",
        )
    )
    await repo.upsert(
        SyncMeta(
            last_changed_at="2026-01-06T10:00:00+03:00",
            sync_status="running",
            last_error=None,
        )
    )

    fetched = await repo.get()
    assert fetched is not None
    assert fetched.sync_status == "running"
    assert fetched.last_changed_at == "2026-01-06T10:00:00+03:00"
