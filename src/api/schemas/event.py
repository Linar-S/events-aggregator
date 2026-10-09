from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    city: str
    address: str


class PlaceDetailResponse(PlaceResponse):
    seats_pattern: str


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    place: PlaceResponse
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class EventDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    place: PlaceDetailResponse
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class EventsPageResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventResponse]


class EventSeatsResponse(BaseModel):
    event_id: str
    available_seats: list[str]
