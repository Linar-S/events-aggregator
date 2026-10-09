import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks

from src.services.background.sync_worker import run_sync_once

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["sync"])

# Защита от параллельных запусков
_sync_lock = asyncio.Lock()


async def _run_sync_safe() -> None:
    if _sync_lock.locked():
        logger.warning("Sync already running, skipping")
        return
    async with _sync_lock:
        await run_sync_once()


@router.post("/trigger")
async def trigger_sync(background: BackgroundTasks) -> dict[str, str]:
    """Запустить синхронизацию в фоне. Возвращает 200 сразу."""
    if _sync_lock.locked():
        return {"status": "already_running"}

    background.add_task(_run_sync_safe)
    return {"status": "scheduled"}
