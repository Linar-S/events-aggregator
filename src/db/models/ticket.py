import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("event_id", "external_ticket_id", name="uq_ticket_event_external"),
    )

    # Наш внутренний ID
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    event_id: Mapped[str] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ID, который вернул внешний API
    external_ticket_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    seat: Mapped[str] = mapped_column(String(32), nullable=False)

    # Статус: active / cancelled
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} event_id={self.event_id} seat={self.seat}>"
