import time

from src.db.models import EventStatus
from src.db.repositories import EventRepositoryProtocol
from src.services.events_provider import EventsProviderClient
from src.services.events_provider.exceptions import EventsProviderError

_SEATS_TTL = 30.0
_seats_cache: dict[str, tuple[float, list[str]]] = {}


def _get_cached(event_id: str) -> list[str] | None:
    entry = _seats_cache.get(event_id)
    if entry is None:
        return None
    ts, seats = entry
    if time.monotonic() - ts > _SEATS_TTL:
        _seats_cache.pop(event_id, None)
        return None
    return seats


def _set_cached(event_id: str, seats: list[str]) -> None:
    _seats_cache[event_id] = (time.monotonic(), seats)


class EventNotFoundError(Exception):
    """Событие не найдено в нашей БД."""


class EventNotPublishedError(Exception):
    """Событие не published — места недоступны."""


class EventsProviderUnavailableError(Exception):
    """Внешний API вернул ошибку."""


class GetEventSeatsUsecase:
    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepositoryProtocol,
    ) -> None:
        self._client = client
        self._events = events

    async def do(self, event_id: str) -> list[str]:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFoundError(event_id)

        if event.status != EventStatus.PUBLISHED:
            raise EventNotPublishedError(event.status)

        cached = _get_cached(event_id)
        if cached is not None:
            return cached

        try:
            seats = await self._client.seats(event_id)
        except EventsProviderError as exc:
            raise EventsProviderUnavailableError(str(exc)) from exc

        _set_cached(event_id, seats)
        return seats
