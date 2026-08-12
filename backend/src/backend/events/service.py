from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from backend.catalog.ticketmaster import CatalogEventSnapshot
from backend.database.models import (
    CatalogProvider,
    CatalogSnapshot,
    Event,
    EventStatus,
    Reservation,
    ReservationStatus,
)
from backend.events.schemas import EventCreate, EventUpdate, OrganizerEventResponse


class EventNotFoundError(Exception):
    """The organizer does not own an event with the requested identifier."""


class UnsafeCapacityReductionError(Exception):
    """The requested capacity is below approved sales and active holds."""

    def __init__(self, committed_quantity: int) -> None:
        self.committed_quantity = committed_quantity
        super().__init__(f"Capacity cannot be lower than {committed_quantity} committed tickets.")


class EventCannotBePublishedError(Exception):
    """The event no longer satisfies the publication rules."""


def create_event(
    database: Session,
    organizer_id: UUID,
    command: EventCreate,
    provider_snapshot: CatalogEventSnapshot,
) -> OrganizerEventResponse:
    """Persist the verified provider snapshot and an organizer-owned local draft together."""

    source = provider_snapshot.event
    snapshot = CatalogSnapshot(
        provider=CatalogProvider.TICKETMASTER,
        provider_event_id=source.provider_event_id,
        name=source.name,
        description=source.description,
        image_url=source.image_url,
        source_url=source.source_url,
        raw_data=provider_snapshot.raw_data,
    )
    database.add(snapshot)
    database.flush()
    event = Event(
        organizer_id=organizer_id,
        catalog_snapshot_id=snapshot.id,
        name=command.name,
        description=command.description,
        venue_name=command.venue_name,
        address=command.address,
        city=command.city,
        country_code=command.country_code,
        start_at=command.start_at,
        capacity=command.capacity,
        price_minor=command.price_minor,
        currency=command.currency,
        status=EventStatus.DRAFT,
    )
    database.add(event)
    database.commit()
    database.refresh(snapshot)
    database.refresh(event)
    return OrganizerEventResponse.from_models(event, snapshot)


def list_organizer_events(database: Session, organizer_id: UUID) -> list[OrganizerEventResponse]:
    """List only events owned by the authenticated organizer."""

    rows = database.execute(
        select(Event, CatalogSnapshot)
        .join(CatalogSnapshot, CatalogSnapshot.id == Event.catalog_snapshot_id)
        .where(Event.organizer_id == organizer_id)
        .order_by(Event.start_at, Event.created_at)
    ).all()
    return [OrganizerEventResponse.from_models(event, snapshot) for event, snapshot in rows]


def update_event(
    database: Session,
    organizer_id: UUID,
    event_id: UUID,
    command: EventUpdate,
) -> OrganizerEventResponse:
    """Replace local event details while holding its row and preserving committed inventory."""

    event = _lock_owned_event(database, organizer_id, event_id)
    committed_quantity = _committed_quantity(database, event.id)
    if command.capacity < committed_quantity:
        raise UnsafeCapacityReductionError(committed_quantity)

    for field, value in command.model_dump().items():
        setattr(event, field, value)
    database.commit()
    database.refresh(event)
    snapshot = database.get(CatalogSnapshot, event.catalog_snapshot_id)
    if snapshot is None:  # Protected by the foreign key; keeps typing and failure explicit.
        raise RuntimeError("Event catalog snapshot is missing.")
    return OrganizerEventResponse.from_models(event, snapshot)


def publish_event(
    database: Session,
    organizer_id: UUID,
    event_id: UUID,
) -> OrganizerEventResponse:
    """Publish an owned future event through an idempotent row-locked state transition."""

    event = _lock_owned_event(database, organizer_id, event_id)
    if event.start_at <= datetime.now(UTC):
        raise EventCannotBePublishedError
    event.status = EventStatus.PUBLISHED
    database.commit()
    database.refresh(event)
    snapshot = database.get(CatalogSnapshot, event.catalog_snapshot_id)
    if snapshot is None:
        raise RuntimeError("Event catalog snapshot is missing.")
    return OrganizerEventResponse.from_models(event, snapshot)


def _lock_owned_event(database: Session, organizer_id: UUID, event_id: UUID) -> Event:
    """Return the owned event as the shared inventory mutex without disclosing foreign rows."""

    event = database.scalar(
        select(Event)
        .where(Event.id == event_id, Event.organizer_id == organizer_id)
        .with_for_update()
    )
    if event is None:
        raise EventNotFoundError
    return event


def _committed_quantity(database: Session, event_id: UUID) -> int:
    """Count approved units and pending holds still active according to PostgreSQL time."""

    quantity = database.scalar(
        select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
            Reservation.event_id == event_id,
            or_(
                Reservation.status == ReservationStatus.APPROVED,
                and_(
                    Reservation.status == ReservationStatus.PENDING,
                    Reservation.expires_at > func.now(),
                ),
            ),
        )
    )
    return int(quantity or 0)
