from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, TimestampMixin
from src.db.models.enums import EventStatus
from src.db.models.place import Place


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    # ID из внешнего API
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)

    place_id: Mapped[str] = mapped_column(
        ForeignKey("places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    place: Mapped[Place] = relationship(back_populates="events", lazy="joined")

    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    registration_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    number_of_visitors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Метаданные из внешнего API
    changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    external_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Event id={self.id} name={self.name!r} status={self.status}>"

    @property
    def is_published(self) -> bool:
        return self.status == EventStatus.PUBLISHED
