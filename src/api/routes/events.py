from datetime import date
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request

from src.api.dependencies import (
    EventRepositoryDep,
    EventsProviderClientDep,
)
from src.api.schemas import (
    EventDetailResponse,
    EventResponse,
    EventSeatsResponse,
    EventsPageResponse,
)
from src.services.usecases import (
    EventNotFoundError,
    EventNotPublishedError,
    EventsProviderUnavailableError,
    GetEventSeatsUsecase,
)

router = APIRouter(prefix="/api/events", tags=["events"])


def _build_page_url(
    base_url: str,
    *,
    page: int,
    page_size: int,
    date_from: date | None,
) -> str:
    params: dict[str, str] = {"page": str(page), "page_size": str(page_size)}
    if date_from is not None:
        params["date_from"] = date_from.isoformat()
    return f"{base_url}?{urlencode(params)}"


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
        next_url = _build_page_url(
            base_url, page=page + 1, page_size=page_size, date_from=date_from
        )
    if page > 1:
        previous_url = _build_page_url(
            base_url, page=page - 1, page_size=page_size, date_from=date_from
        )

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


@router.get("/{event_id}/seats", response_model=EventSeatsResponse)
async def get_event_seats(
    event_id: str,
    events: EventRepositoryDep,
    client: EventsProviderClientDep,
) -> EventSeatsResponse:
    usecase = GetEventSeatsUsecase(client=client, events=events)
    try:
        seats = await usecase.do(event_id)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EventNotPublishedError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Event is not published: {exc}",
        ) from exc
    except EventsProviderUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return EventSeatsResponse(event_id=event_id, available_seats=seats)
