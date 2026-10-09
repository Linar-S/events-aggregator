from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from src.api.dependencies import (
    EventRepositoryDep,
    EventsProviderClientDep,
    PlaceRepositoryDep,
)
from src.api.schemas import (
    EventDetailResponse,
    EventResponse,
    EventSeatsResponse,
    EventsPageResponse,
)
from src.services.events_provider import EventsProviderError

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventsPageResponse)
async def list_events(
    request: Request,
    events: EventRepositoryDep,
    date_from: date | None = Query(default=None, description="YYYY-MM-DD"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> EventsPageResponse:
    offset = (page - 1) * page_size
    rows, total = await events.list(date_from=date_from, offset=offset, limit=page_size)

    base_url = str(request.base_url).rstrip("/") + "/api/events/"
    next_url = None
    previous_url = None
    if offset + page_size < total:
        next_url = f"{base_url}?page={page + 1}&page_size={page_size}"
    if page > 1:
        previous_url = f"{base_url}?page={page - 1}&page_size={page_size}"

    results = [EventResponse.model_validate(r) for r in rows]
    return EventsPageResponse(
        count=total,
        next=next_url,
        previous=previous_url,
        results=results,
    )


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(
    event_id: str,
    events: EventRepositoryDep,
) -> EventDetailResponse:
    event = await events.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventDetailResponse.model_validate(event)


# Простой in-memory кэш на 30 секунд: {event_id: list[str]}
_seats_cache: dict[str, tuple[float, list[str]]] = {}
_SEATS_TTL = 30.0


def _get_cached_seats(event_id: str) -> list[str] | None:
    import time

    entry = _seats_cache.get(event_id)
    if entry is None:
        return None
    ts, seats = entry
    if time.monotonic() - ts > _SEATS_TTL:
        _seats_cache.pop(event_id, None)
        return None
    return seats


def _set_cached_seats(event_id: str, seats: list[str]) -> None:
    import time

    _seats_cache[event_id] = (time.monotonic(), seats)


@router.get("/{event_id}/seats", response_model=EventSeatsResponse)
async def get_event_seats(
    event_id: str,
    events: EventRepositoryDep,
    places: PlaceRepositoryDep,
    client: EventsProviderClientDep,
) -> EventSeatsResponse | JSONResponse:
    event = await events.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    # Не ходим во внешний API для неопубликованных — он вернёт 500 с HTML
    if event.status != "published":
        raise HTTPException(
            status_code=400,
            detail=f"Event is not published (status={event.status})",
        )

    cached = _get_cached_seats(event_id)
    if cached is not None:
        return EventSeatsResponse(event_id=event_id, available_seats=cached)

    try:
        seats = await client.seats(event_id)
    except EventsProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    _set_cached_seats(event_id, seats)
    return EventSeatsResponse(event_id=event_id, available_seats=seats)
