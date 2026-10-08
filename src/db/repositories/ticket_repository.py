from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Ticket


class SQLAlchemyTicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, ticket: Ticket) -> Ticket:
        self._session.add(ticket)
        await self._session.flush()
        return ticket

    async def get_by_external_id(self, external_id: str) -> Ticket | None:
        result = await self._session.execute(
            select(Ticket).where(Ticket.external_ticket_id == external_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, ticket_id: str, status: str) -> None:
        await self._session.execute(
            update(Ticket).where(Ticket.id == ticket_id).values(status=status)
        )
        await self._session.flush()
