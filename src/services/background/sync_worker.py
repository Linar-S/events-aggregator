import asyncio
import logging

from src.core.config import get_settings
from src.db.repositories import (
    SQLAlchemyEventRepository,
    SQLAlchemyPlaceRepository,
    SQLAlchemySyncMetaRepository,
)
from src.db.session import get_session
from src.services.events_provider import EventsProviderClient
from src.services.usecases.sync_events import SyncEventsUsecase

logger = logging.getLogger(__name__)


async def run_sync_once() -> None:
    """Один прогон синхронизации — открывает свою сессию."""
    settings = get_settings()

    async with EventsProviderClient(
        base_url=settings.events_provider_base_url,
        api_key=settings.events_provider_api_key,
    ) as client:
        async for session in get_session():
            usecase = SyncEventsUsecase(
                client=client,
                places=SQLAlchemyPlaceRepository(session),
                events=SQLAlchemyEventRepository(session),
                sync_meta=SQLAlchemySyncMetaRepository(session),
            )
            await usecase.do()
            await session.commit()
            break


async def sync_worker(stop_event: asyncio.Event) -> None:
    """Фоновый воркер: запускает синхронизацию раз в SYNC_INTERVAL_SECONDS."""
    settings = get_settings()
    interval = settings.sync_interval_seconds

    logger.info("Sync worker started, interval=%s seconds", interval)

    while not stop_event.is_set():
        try:
            await run_sync_once()
        except Exception:
            logger.exception("Sync run failed")

        # Ждём либо interval, либо stop_event
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except TimeoutError:
            continue
