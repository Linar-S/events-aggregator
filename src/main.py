import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

import uvicorn
from fastapi import FastAPI

from src.api.app import create_app
from src.services.background.sync_worker import sync_worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    stop_event = asyncio.Event()
    worker_task = asyncio.create_task(sync_worker(stop_event))
    logger.info("Background sync worker scheduled")

    try:
        yield
    finally:
        stop_event.set()
        with contextlib.suppress(asyncio.CancelledError):
            await worker_task
        logger.info("Background sync worker stopped")


def create_lifespan_app() -> FastAPI:
    app = create_app()
    app.router.lifespan_context = lifespan
    return app


app = create_lifespan_app()


def run() -> None:
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
