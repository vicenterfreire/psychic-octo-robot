from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from backend.database.models import (
    CatalogSnapshot,
    Event,
    Reservation,
    ReservationStatus,
    Ticket,
)
from backend.tickets.schemas import CustomerTicketResponse, SharedTicketResponse
from backend.tickets.signing import TicketSigner


class SharedTicketNotFoundError(Exception):
    """The bearer token is invalid or does not resolve to an issued ticket."""


def list_customer_tickets(
    database: Session,
    customer_id: UUID,
    signer: TicketSigner,
    frontend_origin: str,
) -> list[CustomerTicketResponse]:
    rows = database.execute(
        _issued_ticket_statement().where(Reservation.customer_id == customer_id)
    ).all()
    items: list[CustomerTicketResponse] = []
    for ticket, event, snapshot in rows:
        token = signer.sign(ticket.id)
        items.append(
            CustomerTicketResponse.from_models(
                ticket,
                event,
                snapshot,
                token,
                f"{frontend_origin.rstrip('/')}/tickets/share/{token}",
            )
        )
    return items


def get_shared_ticket(
    database: Session,
    token: str,
    signer: TicketSigner,
) -> SharedTicketResponse:
    ticket_id = signer.verify(token)
    if ticket_id is None:
        raise SharedTicketNotFoundError
    row = database.execute(_issued_ticket_statement().where(Ticket.id == ticket_id)).one_or_none()
    if row is None:
        raise SharedTicketNotFoundError
    ticket, event, snapshot = row
    return SharedTicketResponse.from_models(ticket, event, snapshot)


def _issued_ticket_statement() -> Select[tuple[Ticket, Event, CatalogSnapshot]]:
    return (
        select(Ticket, Event, CatalogSnapshot)
        .join(Reservation, Reservation.id == Ticket.reservation_id)
        .join(Event, Event.id == Reservation.event_id)
        .join(CatalogSnapshot, CatalogSnapshot.id == Event.catalog_snapshot_id)
        .where(Reservation.status == ReservationStatus.APPROVED)
        .order_by(Event.start_at, Ticket.issued_at, Ticket.ticket_number)
    )
