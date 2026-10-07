from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class SyncMeta(Base, TimestampMixin):
    """Singleton-таблица: одна строка с метаданными синхронизации."""

    __tablename__ = "sync_meta"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)

    last_sync_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_changed_at: Mapped[str | None] = mapped_column(String(64))

    # idle / running / success / failed
    sync_status: Mapped[str] = mapped_column(String(32), default="idle", nullable=False)

    last_error: Mapped[str | None] = mapped_column(String(2048))

    def __repr__(self) -> str:
        return f"<SyncMeta status={self.sync_status} last_changed_at={self.last_changed_at}>"
