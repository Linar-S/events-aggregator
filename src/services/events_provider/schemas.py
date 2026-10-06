from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Place(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    city: str
    address: str
    seats_pattern: str
    changed_at: datetime | None = None
    created_at: datetime | None = None


class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    place: Place
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int = 0
    changed_at: datetime | None = None
    created_at: datetime | None = None
    status_changed_at: datetime | None = None

    @property
    def is_published(self) -> bool:
        return self.status == "published"


class EventsPage(BaseModel):
    """Одна страница ответа GET /api/events/."""

    model_config = ConfigDict(extra="ignore")

    next: str | None = None
    previous: str | None = None
    results: list[Event] = Field(default_factory=list)


class SeatsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    seats: list[str] = Field(default_factory=list)


class RegisterResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ticket_id: str


class UnregisterResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool
