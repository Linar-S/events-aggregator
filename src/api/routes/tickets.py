from fastapi import APIRouter, HTTPException

from src.api.dependencies import (
    EventRepositoryDep,
    EventsProviderClientDep,
    TicketRepositoryDep,
)
from src.api.schemas import (
    TicketCancelResponse,
    TicketCreateRequest,
    TicketCreateResponse,
)
from src.services.usecases import (
    CancelTicketUsecase,
    CreateTicketUsecase,
    EventAlreadyPastError,
    EventNotFoundError,
    EventNotPublishedError,
    RegistrationClosedError,
    SeatNotAvailableError,
    TicketNotFoundError,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("", status_code=201, response_model=TicketCreateResponse)
async def create_ticket(
    payload: TicketCreateRequest,
    events: EventRepositoryDep,
    tickets: TicketRepositoryDep,
    client: EventsProviderClientDep,
) -> TicketCreateResponse:
    usecase = CreateTicketUsecase(client=client, events=events, tickets=tickets)
    try:
        ticket = await usecase.do(
            event_id=payload.event_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email),
            seat=payload.seat,
        )
    except EventNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Event not found: {exc}") from exc
    except EventNotPublishedError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Event is not published: {exc}",
        ) from exc
    except RegistrationClosedError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Registration deadline passed: {exc}",
        ) from exc
    except SeatNotAvailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TicketCreateResponse(ticket_id=ticket.id)


@router.delete("/{ticket_id}", response_model=TicketCancelResponse)
async def cancel_ticket(
    ticket_id: str,
    events: EventRepositoryDep,
    tickets: TicketRepositoryDep,
    client: EventsProviderClientDep,
) -> TicketCancelResponse:
    usecase = CancelTicketUsecase(client=client, events=events, tickets=tickets)
    try:
        await usecase.do(ticket_id=ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EventAlreadyPastError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Event already past: {exc}",
        ) from exc

    return TicketCancelResponse(success=True)
