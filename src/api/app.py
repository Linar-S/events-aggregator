from fastapi import FastAPI

from src.api.routes import events, health, sync


def create_app() -> FastAPI:
    app = FastAPI(title="Events Aggregator", version="0.1.0")
    app.include_router(health.router)
    app.include_router(sync.router)
    app.include_router(events.router)
    return app
