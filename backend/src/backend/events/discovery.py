from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import ScalarSelect

from backend.database.models import (
    CatalogSnapshot,
    Event,
    EventStatus,
    Reservation,
    ReservationStatus,
)
from backend.events.schemas import PublishedEventResponse

DISCOVERY_RESULT_LIMIT = 50


class PublishedEventNotFoundError(Exception):
    """No published future event has the requested identifier."""


def list_published_events(
    database: Session,
    search_query: str | None,
) -> list[PublishedEventResponse]:
    committed_quantity = _committed_quantity_expression()
    statement = (
        select(Event, CatalogSnapshot, committed_quantity.label("committed_quantity"))
        .join(CatalogSnapshot, CatalogSnapshot.id == Event.catalog_snapshot_id)
        .where(Event.status == EventStatus.PUBLISHED, Event.start_at > func.now())
        .order_by(Event.start_at, Event.created_at)
        .limit(DISCOVERY_RESULT_LIMIT)
    )
    if search_query:
        statement = statement.where(
            or_(
                Event.name.icontains(search_query, autoescape=True),
                Event.venue_name.icontains(search_query, autoescape=True),
                Event.city.icontains(search_query, autoescape=True),
            )
        )

    rows = database.execute(statement).all()
    return [
        PublishedEventResponse.from_models(event, snapshot, int(committed or 0))
        for event, snapshot, committed in rows
    ]


def get_published_event(database: Session, event_id: UUID) -> PublishedEventResponse:
    committed_quantity = _committed_quantity_expression()
    row = database.execute(
        select(Event, CatalogSnapshot, committed_quantity.label("committed_quantity"))
        .join(CatalogSnapshot, CatalogSnapshot.id == Event.catalog_snapshot_id)
        .where(
            Event.id == event_id,
            Event.status == EventStatus.PUBLISHED,
            Event.start_at > func.now(),
        )
    ).one_or_none()
    if row is None:
        raise PublishedEventNotFoundError
    event, snapshot, committed = row
    return PublishedEventResponse.from_models(event, snapshot, int(committed or 0))


def _committed_quantity_expression() -> ScalarSelect[int]:
    return (
        select(func.coalesce(func.sum(Reservation.quantity), 0))
        .where(
            Reservation.event_id == Event.id,
            or_(
                Reservation.status == ReservationStatus.APPROVED,
                and_(
                    Reservation.status == ReservationStatus.PENDING,
                    Reservation.expires_at > func.now(),
                ),
            ),
        )
        .correlate(Event)
        .scalar_subquery()
    )
