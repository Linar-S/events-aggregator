from aiointercept import aiointercept

from src.services.events_provider import EventsPaginator, EventsProviderClient

BASE = "https://events-provider.test"


def _event(event_id: str) -> dict:
    return {
        "id": event_id,
        "name": f"Event {event_id}",
        "place": {
            "id": "place-1",
            "name": "Place",
            "city": "City",
            "address": "Addr",
            "seats_pattern": "A1-10",
        },
        "event_time": "2026-01-11T17:00:00+03:00",
        "registration_deadline": "2026-01-10T17:00:00+03:00",
        "status": "published",
        "number_of_visitors": 0,
    }


async def test_paginator_walks_all_pages(client: EventsProviderClient) -> None:
    page2_url = f"{BASE}/api/events/?changed_at=2000-01-01&cursor=abc"

    async with aiointercept(mock_external_urls=True) as m:
        m.get(
            f"{BASE}/api/events/?changed_at=2000-01-01",
            json={
                "next": page2_url,
                "previous": None,
                "results": [_event("1"), _event("2")],
            },
        )
        m.get(
            page2_url,
            json={"next": None, "previous": None, "results": [_event("3")]},
        )
        paginator = EventsPaginator(client, changed_at="2000-01-01")
        ids = [event.id async for event in paginator]

    assert ids == ["1", "2", "3"]
