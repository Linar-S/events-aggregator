from collections.abc import AsyncIterator

import pytest

from src.services.events_provider import EventsProviderClient


@pytest.fixture
def api_key() -> str:
    return "test-key"


@pytest.fixture
def base_url() -> str:
    return "https://events-provider.test"


@pytest.fixture
async def client(base_url: str, api_key: str) -> AsyncIterator[EventsProviderClient]:
    async with EventsProviderClient(base_url=base_url, api_key=api_key) as c:
        yield c
