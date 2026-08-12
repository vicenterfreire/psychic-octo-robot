from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models import Event, EventStatus, Reservation, ReservationStatus, Ticket
from backend.gate.schemas import (
    GateEventResponse,
    GateValidationOutcome,
    GateValidationResponse,
)
from backend.tickets.signing import TicketSigner

GATE_EVENT_LIMIT = 100


class GateEventNotFoundError(Exception):
    """The selected event is not published."""


def list_gate_events(database: Session) -> list[GateEventResponse]:
    """List published Gate contexts, including events whose scheduled start has passed."""

    events = database.scalars(
        select(Event)
        .where(Event.status == EventStatus.PUBLISHED)
        .order_by(Event.start_at.desc(), Event.created_at.desc())
        .limit(GATE_EVENT_LIMIT)
    ).all()
    return [GateEventResponse.from_model(event) for event in events]


def validate_ticket(
    database: Session,
    gate_user_id: UUID,
    event_id: UUID,
    token: str,
    signer: TicketSigner,
) -> GateValidationResponse:
    """Validate and consume an authentic ticket at most once for the selected event.

    Signature verification precedes state lookup. The ticket row lock serializes concurrent scans;
    revoked, wrong-event, and already-used checks have deliberate disclosure order, and only a
    valid transition commits PostgreSQL usage time with the Gate user.
    """

    selected_event_exists = database.scalar(
        select(Event.id).where(Event.id == event_id, Event.status == EventStatus.PUBLISHED)
    )
    if selected_event_exists is None:
        raise GateEventNotFoundError

    ticket_id = signer.verify(token)
    if ticket_id is None:
        return GateValidationResponse(outcome=GateValidationOutcome.INVALID)

    row = database.execute(
        select(Ticket, Reservation)
        .join(Reservation, Reservation.id == Ticket.reservation_id)
        .where(
            Ticket.id == ticket_id,
            Reservation.status == ReservationStatus.APPROVED,
        )
        .with_for_update(of=Ticket)
    ).one_or_none()
    if row is None:
        return GateValidationResponse(outcome=GateValidationOutcome.INVALID)

    ticket, reservation = row
    if ticket.revoked_at is not None:
        return GateValidationResponse(outcome=GateValidationOutcome.INVALID)
    if reservation.event_id != event_id:
        return GateValidationResponse(outcome=GateValidationOutcome.WRONG_EVENT)
    if ticket.used_at is not None:
        return GateValidationResponse(
            outcome=GateValidationOutcome.ALREADY_USED,
            ticket_number=ticket.ticket_number,
            used_at=ticket.used_at,
        )

    database_time = cast(datetime, database.scalar(select(func.now())))
    ticket_number = ticket.ticket_number
    ticket.used_at = database_time
    ticket.used_by_user_id = gate_user_id
    database.commit()
    return GateValidationResponse(
        outcome=GateValidationOutcome.VALID,
        ticket_number=ticket_number,
        used_at=database_time,
    )
