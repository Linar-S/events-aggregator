import asyncio
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.db.models import Outbox
from src.db.repositories import SQLAlchemyOutboxRepository
from src.db.session import get_session
from src.services.capashino import CapashinoClient
from src.services.outbox.handlers import handle_outbox_event

logger = logging.getLogger(__name__)

OutboxHandler = Callable[[Outbox, CapashinoClient], Awaitable[None]]


async def process_batch(
    session: AsyncSession,
    *,
    capashino_client: CapashinoClient,
    batch_size: int,
    max_attempts: int,
    handler: OutboxHandler | None = None,
) -> int:
    """Обработать одну пачку pending-записей."""
    handler = handler or handle_outbox_event
    repo = SQLAlchemyOutboxRepository(session)

    pending = await repo.fetch_pending(limit=batch_size)
    if not pending:
        return 0

    for entry in pending:
        try:
            await handler(entry, capashino_client)
            await repo.mark_sent(entry.id)
        except Exception as exc:
            logger.exception("Outbox entry %s failed", entry.id)
            await repo.mark_failed(entry.id, str(exc), max_attempts)

    return len(pending)


async def outbox_worker(stop_event: asyncio.Event) -> None:
    """Фоновый воркер: читает pending и обрабатывает."""
    settings = get_settings()
    interval = settings.outbox_poll_interval_seconds
    batch_size = settings.outbox_batch_size
    max_attempts = settings.outbox_max_attempts

    if not settings.capashino_base_url or not settings.capashino_api_key:
        logger.error(
            "Capashino is not configured (CAPASHINO_BASE_URL / CAPASHINO_API_KEY). "
            "Outbox worker will not start."
        )
        return

    logger.info(
        "Outbox worker started, interval=%ss, batch_size=%s, max_attempts=%s",
        interval,
        batch_size,
        max_attempts,
    )

    async with CapashinoClient(
        base_url=settings.capashino_base_url,
        api_key=settings.capashino_api_key,
        timeout=settings.capashino_timeout_seconds,
    ) as capashino_client:
        while not stop_event.is_set():
            try:
                async for session in get_session():
                    processed = await process_batch(
                        session,
                        capashino_client=capashino_client,
                        batch_size=batch_size,
                        max_attempts=max_attempts,
                    )
                    # Явный commit — иначе при break из async for
                    # GeneratorExit прервёт commit в get_session.
                    await session.commit()
                    if processed > 0:
                        logger.info("Processed %s outbox entries", processed)
                    break
            except Exception:
                logger.exception("Outbox worker iteration failed")

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except TimeoutError:
                continue
