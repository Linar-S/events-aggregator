import pytest
from aiointercept import aiointercept

from src.services.capashino import (
    CapashinoAuthError,
    CapashinoBadRequestError,
    CapashinoClient,
)

BASE = "https://capashino.test"


@pytest.fixture
async def client() -> CapashinoClient:
    async with CapashinoClient(base_url=BASE, api_key="test-key") as c:
        yield c


async def test_send_notification_success(client: CapashinoClient) -> None:
    async with aiointercept(mock_external_urls=True) as m:
        m.post(
            f"{BASE}/api/notifications",
            status=201,
            json={
                "id": "notif-123",
                "user_id": "user-1",
                "message": "Hello",
                "reference_id": "ticket-1",
                "created_at": "2026-10-24T12:00:00Z",
            },
        )

        result = await client.send_notification(
            message="Hello",
            reference_id="ticket-1",
            idempotency_key="outbox-1",
        )

        assert result["id"] == "notif-123"


async def test_send_notification_409_treated_as_success(
    client: CapashinoClient,
) -> None:
    async with aiointercept(mock_external_urls=True) as m:
        m.post(
            f"{BASE}/api/notifications",
            status=409,
            json={"id": "notif-123"},
        )

        result = await client.send_notification(
            message="Hello",
            reference_id="ticket-1",
            idempotency_key="outbox-1",
        )

        assert result["id"] == "notif-123"


async def test_send_notification_401_raises_auth_error(
    client: CapashinoClient,
) -> None:
    async with aiointercept(mock_external_urls=True) as m:
        m.post(
            f"{BASE}/api/notifications",
            status=401,
            json={"detail": "Unauthorized"},
        )

        with pytest.raises(CapashinoAuthError):
            await client.send_notification(
                message="Hello",
                reference_id="ticket-1",
                idempotency_key="outbox-1",
            )


async def test_send_notification_422_raises_bad_request(
    client: CapashinoClient,
) -> None:
    async with aiointercept(mock_external_urls=True) as m:
        m.post(
            f"{BASE}/api/notifications",
            status=422,
            json={"detail": "empty message"},
        )

        with pytest.raises(CapashinoBadRequestError):
            await client.send_notification(
                message="   ",
                reference_id="ticket-1",
                idempotency_key="outbox-1",
            )
