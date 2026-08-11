from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel

from backend.database.models import CatalogSnapshot, Event, Ticket


class TicketEventResponse(BaseModel):
    id: UUID
    name: str
    venue_name: str
    address: str
    city: str
    country_code: str
    start_at: datetime
    image_url: str | None

    @classmethod
    def from_models(cls, event: Event, snapshot: CatalogSnapshot) -> Self:
        return cls(
            id=event.id,
            name=event.name,
            venue_name=event.venue_name,
            address=event.address,
            city=event.city,
            country_code=event.country_code,
            start_at=event.start_at,
            image_url=snapshot.image_url,
        )


class CustomerTicketResponse(BaseModel):
    id: UUID
    ticket_number: int
    issued_at: datetime
    is_used: bool
    is_revoked: bool
    token: str
    share_url: str
    event: TicketEventResponse

    @classmethod
    def from_models(
        cls,
        ticket: Ticket,
        event: Event,
        snapshot: CatalogSnapshot,
        token: str,
        share_url: str,
    ) -> Self:
        return cls(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            issued_at=ticket.issued_at,
            is_used=ticket.used_at is not None,
            is_revoked=ticket.revoked_at is not None,
            token=token,
            share_url=share_url,
            event=TicketEventResponse.from_models(event, snapshot),
        )


class CustomerTicketCollectionResponse(BaseModel):
    items: list[CustomerTicketResponse]


class SharedTicketResponse(BaseModel):
    ticket_number: int
    issued_at: datetime
    is_used: bool
    is_revoked: bool
    event: TicketEventResponse

    @classmethod
    def from_models(cls, ticket: Ticket, event: Event, snapshot: CatalogSnapshot) -> Self:
        return cls(
            ticket_number=ticket.ticket_number,
            issued_at=ticket.issued_at,
            is_used=ticket.used_at is not None,
            is_revoked=ticket.revoked_at is not None,
            event=TicketEventResponse.from_models(event, snapshot),
        )
