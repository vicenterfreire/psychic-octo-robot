from datetime import datetime, timedelta
from typing import cast
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session

from backend.database.models import Event, EventStatus, Reservation, ReservationStatus, Ticket
from backend.reservations.schemas import PaymentOutcome, ReservationResponse


class ReservableEventNotFoundError(Exception):
    """The requested event is not published and upcoming."""


class ReservationNotFoundError(Exception):
    """The customer does not own the requested reservation."""


class InsufficientAvailabilityError(Exception):
    def __init__(self, available_quantity: int) -> None:
        self.available_quantity = available_quantity
        super().__init__(f"Only {available_quantity} tickets are currently available.")


def create_reservation(
    database: Session,
    customer_id: UUID,
    event_id: UUID,
    quantity: int,
    lifetime_seconds: int,
) -> ReservationResponse:
    event = database.scalar(
        select(Event)
        .where(
            Event.id == event_id,
            Event.status == EventStatus.PUBLISHED,
            Event.start_at > func.now(),
        )
        .with_for_update()
    )
    if event is None:
        raise ReservableEventNotFoundError

    database_time = _database_time(database)
    _expire_stale_reservations(database, event.id, database_time)
    committed_quantity = _committed_quantity(database, event.id, database_time)
    available_quantity = max(event.capacity - committed_quantity, 0)
    if quantity > available_quantity:
        raise InsufficientAvailabilityError(available_quantity)

    reservation = Reservation(
        customer_id=customer_id,
        event_id=event.id,
        quantity=quantity,
        status=ReservationStatus.PENDING,
        created_at=database_time,
        expires_at=database_time + timedelta(seconds=lifetime_seconds),
    )
    database.add(reservation)
    database.commit()
    database.refresh(reservation)
    return ReservationResponse.from_model(reservation, database_time)


def get_customer_reservation(
    database: Session,
    customer_id: UUID,
    reservation_id: UUID,
) -> ReservationResponse:
    reservation = database.scalar(
        select(Reservation)
        .where(
            Reservation.id == reservation_id,
            Reservation.customer_id == customer_id,
        )
        .with_for_update()
    )
    if reservation is None:
        raise ReservationNotFoundError

    database_time = _database_time(database)
    if reservation.status == ReservationStatus.PENDING and reservation.expires_at <= database_time:
        reservation.status = ReservationStatus.EXPIRED
        database.commit()
        database.refresh(reservation)

    return ReservationResponse.from_model(
        reservation,
        database_time,
        _ticket_count(database, reservation.id),
    )


def process_payment(
    database: Session,
    customer_id: UUID,
    reservation_id: UUID,
    outcome: PaymentOutcome,
) -> ReservationResponse:
    event_id = database.scalar(
        select(Reservation.event_id).where(
            Reservation.id == reservation_id,
            Reservation.customer_id == customer_id,
        )
    )
    if event_id is None:
        raise ReservationNotFoundError

    locked_event_id = database.scalar(
        select(Event.id).where(Event.id == event_id).with_for_update()
    )
    if locked_event_id is None:  # Protected by the reservation foreign key.
        raise RuntimeError("Reservation event is missing.")

    reservation = database.scalar(
        select(Reservation)
        .where(
            Reservation.id == reservation_id,
            Reservation.customer_id == customer_id,
            Reservation.event_id == locked_event_id,
        )
        .with_for_update()
    )
    if reservation is None:
        raise ReservationNotFoundError

    database_time = _database_time(database)
    if reservation.status == ReservationStatus.PENDING:
        if reservation.expires_at <= database_time:
            reservation.status = ReservationStatus.EXPIRED
        elif outcome == PaymentOutcome.DECLINED:
            reservation.status = ReservationStatus.DECLINED
        else:
            reservation.status = ReservationStatus.APPROVED
            database.add_all(
                Ticket(reservation_id=reservation.id, ticket_number=ticket_number)
                for ticket_number in range(1, reservation.quantity + 1)
            )
        database.commit()
        database.refresh(reservation)

    return ReservationResponse.from_model(
        reservation,
        database_time,
        _ticket_count(database, reservation.id),
    )


def _database_time(database: Session) -> datetime:
    return cast(datetime, database.scalar(select(func.now())))


def _expire_stale_reservations(
    database: Session,
    event_id: UUID,
    database_time: datetime,
) -> None:
    database.execute(
        update(Reservation)
        .where(
            Reservation.event_id == event_id,
            Reservation.status == ReservationStatus.PENDING,
            Reservation.expires_at <= database_time,
        )
        .values(status=ReservationStatus.EXPIRED, updated_at=database_time)
    )


def _committed_quantity(
    database: Session,
    event_id: UUID,
    database_time: datetime,
) -> int:
    quantity = database.scalar(
        select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
            Reservation.event_id == event_id,
            or_(
                Reservation.status == ReservationStatus.APPROVED,
                and_(
                    Reservation.status == ReservationStatus.PENDING,
                    Reservation.expires_at > database_time,
                ),
            ),
        )
    )
    return int(quantity or 0)


def _ticket_count(database: Session, reservation_id: UUID) -> int:
    quantity = database.scalar(
        select(func.count(Ticket.id)).where(Ticket.reservation_id == reservation_id)
    )
    return int(quantity or 0)
