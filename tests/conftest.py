from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.app import create_app


class FakeSession:
    # для теста без запроса Postgres
    async def execute(self, *_args, **_kwargs) -> None:
        return None


async def fake_get_session() -> AsyncIterator[FakeSession]:
    yield FakeSession()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()

    # Подменяем зависимость БД на фейковую сессию
    from src.api.routes import health as health_module

    app.dependency_overrides[health_module.get_session] = fake_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
