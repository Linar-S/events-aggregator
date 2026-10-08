from collections.abc import Sequence
from datetime import date
from typing import Protocol

from src.db.models import Event, Place, SyncMeta, Ticket


class PlaceRepositoryProtocol(Protocol):
    async def upsert(self, place: Place) -> Place: ...
    async def get(self, place_id: str) -> Place | None: ...


class EventRepositoryProtocol(Protocol):
    async def get(self, event_id: str) -> Event | None: ...

    async def list(
        self,
        *,
        date_from: date | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Event], int]: ...

    async def upsert(self, event: Event) -> Event: ...


class TicketRepositoryProtocol(Protocol):
    async def create(self, ticket: Ticket) -> Ticket: ...
    async def get_by_external_id(self, external_id: str) -> Ticket | None: ...
    async def update_status(self, ticket_id: str, status: str) -> None: ...


class SyncMetaRepositoryProtocol(Protocol):
    async def get(self) -> SyncMeta | None: ...
    async def upsert(self, meta: SyncMeta) -> SyncMeta: ...
