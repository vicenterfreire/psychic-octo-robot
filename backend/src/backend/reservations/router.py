from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_roles
from backend.core.dependencies import get_application_settings
from backend.core.settings import Settings
from backend.database.dependencies import get_database_session
from backend.database.models import User, UserRole
from backend.reservations.schemas import PaymentCommand, ReservationCreate, ReservationResponse
from backend.reservations.service import (
    InsufficientAvailabilityError,
    ReservableEventNotFoundError,
    ReservationNotFoundError,
    create_reservation,
    get_customer_reservation,
    process_payment,
)

router = APIRouter(prefix="/reservations", tags=["reservations"])

Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]
Database = Annotated[Session, Depends(get_database_session)]
ApplicationSettings = Annotated[Settings, Depends(get_application_settings)]


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def post_reservation(
    command: ReservationCreate,
    response: Response,
    customer: Customer,
    database: Database,
    settings: ApplicationSettings,
) -> ReservationResponse:
    response.headers["Cache-Control"] = "no-store"
    try:
        return create_reservation(
            database,
            customer.id,
            command.event_id,
            command.quantity,
            settings.reservation_lifetime_seconds,
        )
    except ReservableEventNotFoundError as error:
        raise _not_found("Event was not found.") from error
    except InsufficientAvailabilityError as error:
        noun = "ticket is" if error.available_quantity == 1 else "tickets are"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only {error.available_quantity} {noun} currently available.",
        ) from error


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(
    reservation_id: UUID,
    response: Response,
    customer: Customer,
    database: Database,
) -> ReservationResponse:
    response.headers["Cache-Control"] = "no-store"
    try:
        return get_customer_reservation(database, customer.id, reservation_id)
    except ReservationNotFoundError as error:
        raise _not_found("Reservation was not found.") from error


@router.post("/{reservation_id}/payment", response_model=ReservationResponse)
def post_payment(
    reservation_id: UUID,
    command: PaymentCommand,
    response: Response,
    customer: Customer,
    database: Database,
) -> ReservationResponse:
    response.headers["Cache-Control"] = "no-store"
    try:
        return process_payment(database, customer.id, reservation_id, command.outcome)
    except ReservationNotFoundError as error:
        raise _not_found("Reservation was not found.") from error


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
