from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.db.repositories import (
    SQLAlchemyEventRepository,
    SQLAlchemyPlaceRepository,
    SQLAlchemyTicketRepository,
)
from src.db.session import get_session
from src.services.events_provider import EventsProviderClient


async def get_event_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SQLAlchemyEventRepository:
    return SQLAlchemyEventRepository(session)


async def get_place_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SQLAlchemyPlaceRepository:
    return SQLAlchemyPlaceRepository(session)


async def get_ticket_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SQLAlchemyTicketRepository:
    return SQLAlchemyTicketRepository(session)


async def get_events_provider_client() -> AsyncIterator[EventsProviderClient]:
    settings = get_settings()
    async with EventsProviderClient(
        base_url=settings.events_provider_base_url,
        api_key=settings.events_provider_api_key,
    ) as client:
        yield client


EventRepositoryDep = Annotated[SQLAlchemyEventRepository, Depends(get_event_repository)]
PlaceRepositoryDep = Annotated[SQLAlchemyPlaceRepository, Depends(get_place_repository)]
TicketRepositoryDep = Annotated[SQLAlchemyTicketRepository, Depends(get_ticket_repository)]
EventsProviderClientDep = Annotated[EventsProviderClient, Depends(get_events_provider_client)]
