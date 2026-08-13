from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_roles
from backend.catalog.dependencies import get_ticketmaster_client
from backend.catalog.http_errors import catalog_http_exception
from backend.catalog.ticketmaster import CatalogProviderError, TicketmasterClient
from backend.database.dependencies import get_database_session
from backend.database.models import User, UserRole
from backend.events.discovery import (
    PublishedEventNotFoundError,
    get_published_event,
    list_published_events,
)
from backend.events.schemas import (
    EventCreate,
    EventUpdate,
    OrganizerEventCollectionResponse,
    OrganizerEventResponse,
    PublishedEventCollectionResponse,
    PublishedEventResponse,
)
from backend.events.service import (
    EventCannotBePublishedError,
    EventNotFoundError,
    UnsafeCapacityReductionError,
    create_event,
    list_organizer_events,
    publish_event,
    update_event,
)

router = APIRouter(prefix="/events", tags=["events"])

Organizer = Annotated[User, Depends(require_roles(UserRole.ORGANIZER))]
Database = Annotated[Session, Depends(get_database_session)]
CatalogClient = Annotated[TicketmasterClient, Depends(get_ticketmaster_client)]


@router.get(
    "",
    response_model=PublishedEventCollectionResponse,
    summary="List published events",
    description=(
        "Public upcoming-event discovery with optional local text search. Availability is a "
        "PostgreSQL-timed snapshot; reservation creation remains authoritative."
    ),
)
def get_published_events(
    database: Database,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> PublishedEventCollectionResponse:
    search_query = q.strip() if q and q.strip() else None
    return PublishedEventCollectionResponse(items=list_published_events(database, search_query))


@router.get(
    "/organizer",
    response_model=OrganizerEventCollectionResponse,
    summary="List owned events",
    description="Return only events owned by the authenticated Organizer.",
)
def get_organizer_events(
    organizer: Organizer,
    database: Database,
) -> OrganizerEventCollectionResponse:
    return OrganizerEventCollectionResponse(items=list_organizer_events(database, organizer.id))


@router.get(
    "/{event_id}",
    response_model=PublishedEventResponse,
    summary="Get published event",
    description="Return one upcoming published event and its current availability snapshot.",
)
def get_published_event_details(
    event_id: UUID,
    database: Database,
) -> PublishedEventResponse:
    try:
        return get_published_event(database, event_id)
    except PublishedEventNotFoundError as error:
        raise _not_found() from error


@router.post(
    "",
    response_model=OrganizerEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create event draft",
    description=(
        "Organizer-only creation from a Ticketmaster identifier. The backend refetches the "
        "provider item, verifies its identifier, and persists an immutable source snapshot."
    ),
)
def post_event(
    command: EventCreate,
    organizer: Organizer,
    database: Database,
    client: CatalogClient,
) -> OrganizerEventResponse:
    try:
        provider_snapshot = client.get_event_snapshot(command.provider_event_id)
    except CatalogProviderError as error:
        raise catalog_http_exception(error) from error
    return create_event(database, organizer.id, command, provider_snapshot)


@router.put(
    "/{event_id}",
    response_model=OrganizerEventResponse,
    summary="Replace owned event details",
    description=(
        "Replace editable fields on an Organizer-owned event. Capacity cannot fall below "
        "approved sales plus active temporary holds."
    ),
)
def put_event(
    event_id: UUID,
    command: EventUpdate,
    organizer: Organizer,
    database: Database,
) -> OrganizerEventResponse:
    try:
        return update_event(database, organizer.id, event_id, command)
    except EventNotFoundError as error:
        raise _not_found() from error
    except UnsafeCapacityReductionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Capacity cannot be lower than the quantity in active or approved reservations "
                f"({error.committed_quantity})."
            ),
        ) from error


@router.post(
    "/{event_id}/publish",
    response_model=OrganizerEventResponse,
    summary="Publish owned event",
    description=("Idempotently make an Organizer-owned future event visible in public discovery."),
)
def post_event_publication(
    event_id: UUID,
    organizer: Organizer,
    database: Database,
) -> OrganizerEventResponse:
    try:
        return publish_event(database, organizer.id, event_id)
    except EventNotFoundError as error:
        raise _not_found() from error
    except EventCannotBePublishedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only an event with a future start can be published.",
        ) from error


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Event was not found.",
    )
