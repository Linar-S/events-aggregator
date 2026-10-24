import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class OutboxStatus:
    """Статусы записи outbox."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Outbox(Base):
    """Запись Transactional Outbox.

    Создаётся в той же транзакции, что и бизнес-действие (например, тикет).
    Воркер периодически читает `pending`-записи и отправляет их во внешний API.
    """

    __tablename__ = "outbox"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=OutboxStatus.PENDING,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return (
            f"<Outbox id={self.id} event={self.event_type!r} "
            f"status={self.status} attempts={self.attempts}>"
        )
