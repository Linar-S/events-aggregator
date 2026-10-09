from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.routes import events, health, sync, tickets


def create_app() -> FastAPI:
    app = FastAPI(title="Events Aggregator", version="0.1.0")

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        # ТЗ требует 400 на некорректные данные
        return JSONResponse(status_code=400, content={"detail": exc.errors()})

    app.include_router(health.router)
    app.include_router(sync.router)
    app.include_router(events.router)
    app.include_router(tickets.router)
    return app
