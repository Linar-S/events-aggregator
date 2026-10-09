from pydantic import BaseModel, EmailStr, Field


class TicketCreateRequest(BaseModel):
    event_id: str
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    email: EmailStr
    seat: str = Field(min_length=1, max_length=32)


class TicketCreateResponse(BaseModel):
    ticket_id: str


class TicketCancelResponse(BaseModel):
    success: bool
