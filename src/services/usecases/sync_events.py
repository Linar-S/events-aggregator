import logging
from datetime import UTC, datetime

from src.db.models import Event, Place, SyncMeta
from src.db.repositories import (
    EventRepositoryProtocol,
    PlaceRepositoryProtocol,
    SyncMetaRepositoryProtocol,
)
from src.services.events_provider import EventsPaginator, EventsProviderClient

logger = logging.getLogger(__name__)

FIRST_SYNC_DATE = "2000-01-01"


class SyncEventsUsecase:
    """Синхронизация событий из Events Provider API в локальную БД.

    Логика:
    1. Читаем SyncMeta.last_changed_at (или "2000-01-01" для первой синхронизации).
    2. Проходим пагинатором все страницы.
    3. Upsert каждого события и связанного place.
    4. Обновляем SyncMeta: last_sync_time, last_changed_at (максимальный из ответов), sync_status.
    """

    def __init__(
        self,
        client: EventsProviderClient,
        places: PlaceRepositoryProtocol,
        events: EventRepositoryProtocol,
        sync_meta: SyncMetaRepositoryProtocol,
    ) -> None:
        self._client = client
        self._places = places
        self._events = events
        self._sync_meta = sync_meta

    async def do(self) -> SyncMeta:
        meta = await self._sync_meta.get()
        if meta is None:
            meta = SyncMeta(last_changed_at=None, sync_status="idle")

        changed_at = meta.last_changed_at or FIRST_SYNC_DATE
        meta.sync_status = "running"
        meta.last_error = None
        await self._sync_meta.upsert(meta)

        max_changed_at = meta.last_changed_at
        events_count = 0

        try:
            paginator = EventsPaginator(self._client, changed_at=changed_at)
            async for event in paginator:
                place = Place(
                    id=event.place.id,
                    name=event.place.name,
                    city=event.place.city,
                    address=event.place.address,
                    seats_pattern=event.place.seats_pattern,
                    changed_at=event.place.changed_at,
                    created_at=event.place.created_at,
                )
                await self._places.upsert(place)

                db_event = Event(
                    id=event.id,
                    name=event.name,
                    place_id=event.place.id,
                    event_time=event.event_time,
                    registration_deadline=event.registration_deadline,
                    status=event.status,
                    number_of_visitors=event.number_of_visitors,
                    changed_at=event.changed_at,
                    external_created_at=event.created_at,
                    status_changed_at=event.status_changed_at,
                )
                await self._events.upsert(db_event)
                events_count += 1

                if event.changed_at is not None:
                    iso = event.changed_at.isoformat()
                    if max_changed_at is None or iso > max_changed_at:
                        max_changed_at = iso

            meta.last_sync_time = datetime.now(UTC)
            meta.last_changed_at = max_changed_at
            meta.sync_status = "success"
            meta.last_error = None
            await self._sync_meta.upsert(meta)
            logger.info("Sync completed: %d events", events_count)
        except Exception as exc:
            meta.sync_status = "failed"
            meta.last_error = str(exc)[:2000]
            await self._sync_meta.upsert(meta)
            logger.exception("Sync failed")
            raise

        return meta
