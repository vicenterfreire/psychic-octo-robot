from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_roles
from backend.database.dependencies import get_database_session
from backend.database.models import User, UserRole
from backend.gate.schemas import (
    GateEventCollectionResponse,
    GateValidationCommand,
    GateValidationResponse,
)
from backend.gate.service import GateEventNotFoundError, list_gate_events, validate_ticket
from backend.tickets.dependencies import get_ticket_signer
from backend.tickets.signing import TicketSigner

router = APIRouter(prefix="/gate", tags=["gate"])

GateUser = Annotated[User, Depends(require_roles(UserRole.GATE))]
Database = Annotated[Session, Depends(get_database_session)]
Signer = Annotated[TicketSigner, Depends(get_ticket_signer)]


@router.get(
    "/events",
    response_model=GateEventCollectionResponse,
    summary="List gate events",
    description=(
        "Gate-only list of published events, including events whose scheduled start has passed."
    ),
)
def get_gate_events(
    response: Response,
    gate_user: GateUser,
    database: Database,
) -> GateEventCollectionResponse:
    response.headers["Cache-Control"] = "no-store"
    return GateEventCollectionResponse(items=list_gate_events(database))


@router.post(
    "/validations",
    response_model=GateValidationResponse,
    summary="Validate ticket for event",
    description=(
        "Verify the HMAC credential and atomically consume an unused ticket in the selected event "
        "context. Business outcomes are valid, invalid, already_used, or wrong_event."
    ),
)
def post_gate_validation(
    command: GateValidationCommand,
    response: Response,
    gate_user: GateUser,
    database: Database,
    signer: Signer,
) -> GateValidationResponse:
    response.headers["Cache-Control"] = "no-store"
    try:
        return validate_ticket(database, gate_user.id, command.event_id, command.token, signer)
    except GateEventNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event was not found.",
        ) from error
