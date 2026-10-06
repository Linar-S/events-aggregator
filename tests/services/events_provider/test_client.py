import pytest
from aiointercept import aiointercept

from src.services.events_provider import (
    EventsProviderAuthError,
    EventsProviderClient,
    EventsProviderNotFoundError,
)

BASE = "https://events-provider.test"


def _event_payload(event_id: str = "evt-1") -> dict:
    return {
        "id": event_id,
        "name": "Конференция по Python",
        "place": {
            "id": "place-1",
            "name": "Технопарк",
            "city": "Москва",
            "address": "ул. Ленина, 1",
            "seats_pattern": "A1-10",
        },
        "event_time": "2026-01-11T17:00:00+03:00",
        "registration_deadline": "2026-01-10T17:00:00+03:00",
        "status": "published",
        "number_of_visitors": 5,
    }


async def test_events_sends_api_key_and_trailing_slash(
    client: EventsProviderClient,
) -> None:
    async with aiointercept(mock_external_urls=True) as m:
        m.get(
            f"{BASE}/api/events/?changed_at=2000-01-01",
            json={"next": None, "previous": None, "results": [_event_payload()]},
        )
        page = await client.events(changed_at="2000-01-01")

    assert len(page.results) == 1
    assert page.results[0].id == "evt-1"
    assert page.results[0].is_published is True


async def test_401_raises_auth_error(client: EventsProviderClient) -> None:
    async with aiointercept(mock_external_urls=True) as m:
        m.get(
            f"{BASE}/api/events/?changed_at=2000-01-01",
            status=401,
            json={"detail": "Unauthorized"},
        )
        with pytest.raises(EventsProviderAuthError):
            await client.events(changed_at="2000-01-01")


async def test_404_raises_not_found(client: EventsProviderClient) -> None:
    async with aiointercept(mock_external_urls=True) as m:
        m.get(
            f"{BASE}/api/events/evt-1/seats/",
            status=404,
            json={"detail": "Event not found"},
        )
        with pytest.raises(EventsProviderNotFoundError):
            await client.seats("evt-1")
