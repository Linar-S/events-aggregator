from types import TracebackType
from typing import Any
from urllib.parse import urljoin

import aiohttp

from src.services.capashino.exceptions import (
    CapashinoAuthError,
    CapashinoBadRequestError,
    CapashinoError,
    CapashinoServerError,
)

DEFAULT_TIMEOUT = 10.0


class CapashinoClient:
    """HTTP-клиент для Notification-сервиса Capashino (на aiohttp)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session = session
        self._own_session = session is None

    async def __aenter__(self) -> "CapashinoClient":
        if self._own_session:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={"X-API-Key": self._api_key},
            )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if self._own_session and self._session is not None:
            await self._session.close()

    async def send_notification(
        self,
        *,
        message: str,
        reference_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Отправить уведомление в Capashino.

        Возвращает тело ответа при успехе (201 или 409).
        """
        if self._session is None:
            raise CapashinoError("ClientSession is not initialized. Use async with.")

        url = urljoin(self._base_url + "/", "api/notifications")
        payload = {
            "message": message,
            "reference_id": reference_id,
            "idempotency_key": idempotency_key,
        }

        try:
            async with self._session.request(
                method="POST",
                url=url,
                json=payload,
            ) as response:
                return await self._handle_response(response)
        except aiohttp.ClientError as exc:
            raise CapashinoError(f"HTTP error: {exc}") from exc

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        status = response.status

        # 201 Created — успех
        # 409 Conflict — уведомление с таким idempotency_key уже создано, считаем успехом
        if status in (201, 409):
            try:
                return await response.json()
            except ValueError:
                return {"status": status}

        body = await self._safe_body(response)

        if status in (400, 422):
            raise CapashinoBadRequestError(f"Bad request: {body}", details=body)
        if status == 401:
            raise CapashinoAuthError("Unauthorized: check X-API-Key")
        if 500 <= status < 600:
            raise CapashinoServerError(f"Server error {status}: {body}")

        raise CapashinoError(f"Unexpected status {status}: {body}")

    async def _safe_body(self, response: aiohttp.ClientResponse) -> object:
        try:
            return await response.json()
        except (aiohttp.ContentTypeError, ValueError):
            return await response.text()
