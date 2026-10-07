from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class Place(Base):
    __tablename__ = "places"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    seats_pattern: Mapped[str] = mapped_column(String(512), nullable=False)

    # Поля из внешнего API — чтобы отслеживать изменения
    changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    events: Mapped[list[Event]] = relationship(  # noqa: F821
        back_populates="place",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Place id={self.id} name={self.name!r}>"
