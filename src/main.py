import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

import uvicorn
from fastapi import FastAPI

from src.api.app import create_app
from src.services.background.sync_worker import sync_worker
from src.services.outbox import outbox_worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    stop_event = asyncio.Event()

    sync_task = asyncio.create_task(sync_worker(stop_event))
    outbox_task = asyncio.create_task(outbox_worker(stop_event))
    logger.info("Background workers scheduled: sync, outbox")

    try:
        yield
    finally:
        stop_event.set()
        for task in (sync_task, outbox_task):
            with contextlib.suppress(asyncio.CancelledError):
                await task
        logger.info("Background workers stopped")


def create_lifespan_app() -> FastAPI:
    app = create_app()
    app.router.lifespan_context = lifespan
    return app


app = create_lifespan_app()


def run() -> None:
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
