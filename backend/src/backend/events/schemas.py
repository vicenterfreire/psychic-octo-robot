from datetime import UTC, datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.database.models import CatalogProvider, CatalogSnapshot, Event, EventStatus


class EventDetails(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    venue_name: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=500)
    city: str = Field(min_length=1, max_length=120)
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    start_at: datetime
    capacity: int = Field(gt=0, le=1_000_000)
    price_minor: int = Field(ge=0, le=100_000_000)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")

    @field_validator("start_at")
    @classmethod
    def start_must_be_future_and_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Event start must include a timezone.")
        if value <= datetime.now(UTC):
            raise ValueError("Event start must be in the future.")
        return value


class EventCreate(EventDetails):
    provider_event_id: str = Field(min_length=1, max_length=128)


class EventUpdate(EventDetails):
    pass


class CatalogSourceResponse(BaseModel):
    provider: CatalogProvider
    provider_event_id: str
    name: str
    description: str | None
    image_url: str | None
    source_url: str | None

    @classmethod
    def from_snapshot(cls, snapshot: CatalogSnapshot) -> Self:
        return cls(
            provider=snapshot.provider,
            provider_event_id=snapshot.provider_event_id,
            name=snapshot.name,
            description=snapshot.description,
            image_url=snapshot.image_url,
            source_url=snapshot.source_url,
        )


class OrganizerEventResponse(BaseModel):
    id: UUID
    organizer_id: UUID
    name: str
    description: str | None
    venue_name: str
    address: str
    city: str
    country_code: str
    start_at: datetime
    capacity: int
    price_minor: int
    currency: str
    status: EventStatus
    source: CatalogSourceResponse
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_models(cls, event: Event, snapshot: CatalogSnapshot) -> Self:
        return cls(
            id=event.id,
            organizer_id=event.organizer_id,
            name=event.name,
            description=event.description,
            venue_name=event.venue_name,
            address=event.address,
            city=event.city,
            country_code=event.country_code,
            start_at=event.start_at,
            capacity=event.capacity,
            price_minor=event.price_minor,
            currency=event.currency,
            status=event.status,
            source=CatalogSourceResponse.from_snapshot(snapshot),
            created_at=event.created_at,
            updated_at=event.updated_at,
        )


class OrganizerEventCollectionResponse(BaseModel):
    items: list[OrganizerEventResponse]
