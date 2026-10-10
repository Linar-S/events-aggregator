from types import TracebackType
from typing import Any
from urllib.parse import urljoin

import aiohttp

from src.services.events_provider.exceptions import (
    EventsProviderAuthError,
    EventsProviderBadRequestError,
    EventsProviderError,
    EventsProviderNotFoundError,
    EventsProviderServerError,
)
from src.services.events_provider.schemas import (
    EventsPage,
    RegisterResponse,
    SeatsResponse,
    UnregisterResponse,
)

DEFAULT_TIMEOUT = 10.0


class EventsProviderClient:
    """HTTP-клиент для Events Provider API (на aiohttp).

    Все запросы к внешнему сервису идут только через этот класс.
    URL'ы всегда заканчиваются на trailing slash — иначе API отдаёт 301/308.
    """

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

    async def __aenter__(self) -> EventsProviderClient:
        if self._own_session:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={"x-api-key": self._api_key},
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

    # ---------- публичные методы ----------

    async def events(self, changed_at: str, cursor: str | None = None) -> EventsPage:
        """Получить страницу событий, изменённых после `changed_at`."""
        params: dict[str, str] = {"changed_at": changed_at}
        if cursor:
            params["cursor"] = cursor

        data = await self._request("GET", "/api/events/", params=params)
        return EventsPage.model_validate(data)

    async def seats(self, event_id: str) -> list[str]:
        """Список свободных мест для события."""
        data = await self._request("GET", f"/api/events/{event_id}/seats/")
        return SeatsResponse.model_validate(data).seats

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        seat: str,
        email: str,
    ) -> str:
        """Зарегистрировать участника. Возвращает ticket_id."""
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "seat": seat,
            "email": email,
        }
        data = await self._request(
            "POST",
            f"/api/events/{event_id}/register/",
            json=payload,
        )
        return RegisterResponse.model_validate(data).ticket_id

    async def unregister(self, event_id: str, ticket_id: str) -> bool:
        """Отменить регистрацию. Возвращает True при успехе."""
        data = await self._request(
            "DELETE",
            f"/api/events/{event_id}/unregister/",
            json={"ticket_id": ticket_id},
        )
        return UnregisterResponse.model_validate(data).success

    # ---------- внутреннее ----------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        if self._session is None:
            raise EventsProviderError("ClientSession is not initialized. Use async with.")

        url = urljoin(self._base_url + "/", path.lstrip("/"))

        try:
            async with self._session.request(
                method=method,
                url=url,
                params=params,
                json=json,
            ) as response:
                return await self._handle_response(response)
        except aiohttp.ClientError as exc:
            raise EventsProviderError(f"HTTP error: {exc}") from exc

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Any:
        status = response.status
        if 200 <= status < 300:
            return await response.json()

        body = await self._safe_body(response)

        if status == 400:
            raise EventsProviderBadRequestError("Bad request", details=body)
        if status == 401:
            raise EventsProviderAuthError("Unauthorized: check x-api-key")
        if status == 404:
            raise EventsProviderNotFoundError(f"Not found: {body}")
        if 500 <= status < 600:
            raise EventsProviderServerError(f"Server error {status}: {body}")
        raise EventsProviderError(f"Unexpected status {status}: {body}")

    async def _safe_body(self, response: aiohttp.ClientResponse) -> object:
        try:
            return await response.json()
        except aiohttp.ContentTypeError, ValueError:
            return await response.text()
