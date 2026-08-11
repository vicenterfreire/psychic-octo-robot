from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.database.models import Event


class GateValidationOutcome(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    ALREADY_USED = "already_used"
    WRONG_EVENT = "wrong_event"


class GateEventResponse(BaseModel):
    id: UUID
    name: str
    venue_name: str
    city: str
    country_code: str
    start_at: datetime

    @classmethod
    def from_model(cls, event: Event) -> Self:
        return cls(
            id=event.id,
            name=event.name,
            venue_name=event.venue_name,
            city=event.city,
            country_code=event.country_code,
            start_at=event.start_at,
        )


class GateEventCollectionResponse(BaseModel):
    items: list[GateEventResponse]


class GateValidationCommand(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: UUID
    token: str = Field(min_length=1, max_length=128)


class GateValidationResponse(BaseModel):
    outcome: GateValidationOutcome
    ticket_number: int | None = None
    used_at: datetime | None = None
