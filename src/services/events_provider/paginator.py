from datetime import date

from src.services.events_provider.client import EventsProviderClient
from src.services.events_provider.schemas import Event
from src.services.events_provider.url_utils import extract_cursor


class EventsPaginator:
    """Async-итератор по cursor-based пагинации Events Provider API.

    Пример:
        paginator = EventsPaginator(client, changed_at="2000-01-01")
        async for event in paginator:
            print(event.name)
    """

    def __init__(
        self,
        client: EventsProviderClient,
        changed_at: str | date,
    ) -> None:
        self._client = client
        self._changed_at = changed_at.isoformat() if isinstance(changed_at, date) else changed_at
        self._next_url: str | None = None
        self._buffer: list[Event] = []
        self._started = False
        self._done = False

    def __aiter__(self) -> "EventsPaginator":
        return self

    async def __anext__(self) -> Event:
        while not self._buffer:
            if self._done:
                raise StopAsyncIteration
            await self._load_next_page()

        return self._buffer.pop(0)

    async def _load_next_page(self) -> None:
        if not self._started:
            page = await self._client.events(changed_at=self._changed_at)
            self._started = True
        elif self._next_url:
            cursor = extract_cursor(self._next_url)
            page = await self._client.events(
                changed_at=self._changed_at,
                cursor=cursor,
            )
        else:
            self._done = True
            return

        self._buffer.extend(page.results)
        self._next_url = page.next
        if not page.next and not self._buffer:
            self._done = True
