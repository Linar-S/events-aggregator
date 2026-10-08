from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.app import create_app
from src.db.models import Base

# ---------- FastAPI-фикстуры (были) ----------


class FakeSession:
    async def execute(self, *_args, **_kwargs) -> None:
        return None


async def fake_get_session() -> AsyncIterator[FakeSession]:
    yield FakeSession()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()

    from src.api.routes import health as health_module

    app.dependency_overrides[health_module.get_session] = fake_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------- БД-фикстуры (новые) ----------


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """In-memory SQLite с накатанной схемой — для тестов репозиториев."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()
