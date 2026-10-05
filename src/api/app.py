from fastapi import FastAPI

from src.api.routes import health


def create_app() -> FastAPI:
    app = FastAPI(title="Events Aggregator", version="0.1.0")
    app.include_router(health.router)
    return app