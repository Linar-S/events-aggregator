from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import SyncMeta

SYNC_META_ID = 1


class SQLAlchemySyncMetaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> SyncMeta | None:
        return await self._session.get(SyncMeta, SYNC_META_ID)

    async def upsert(self, meta: SyncMeta) -> SyncMeta:
        meta.id = SYNC_META_ID
        existing = await self._session.get(SyncMeta, SYNC_META_ID)
        if existing is None:
            self._session.add(meta)
            await self._session.flush()
            return meta

        existing.last_sync_time = meta.last_sync_time
        existing.last_changed_at = meta.last_changed_at
        existing.sync_status = meta.sync_status
        existing.last_error = meta.last_error
        await self._session.flush()
        return existing
