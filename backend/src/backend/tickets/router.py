from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_roles
from backend.core.dependencies import get_application_settings
from backend.core.settings import Settings
from backend.database.dependencies import get_database_session
from backend.database.models import User, UserRole
from backend.tickets.dependencies import get_ticket_signer
from backend.tickets.schemas import CustomerTicketCollectionResponse, SharedTicketResponse
from backend.tickets.service import (
    SharedTicketNotFoundError,
    get_shared_ticket,
    list_customer_tickets,
)
from backend.tickets.signing import TicketSigner

router = APIRouter(prefix="/tickets", tags=["tickets"])

Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]
Database = Annotated[Session, Depends(get_database_session)]
ApplicationSettings = Annotated[Settings, Depends(get_application_settings)]
Signer = Annotated[TicketSigner, Depends(get_ticket_signer)]


@router.get("", response_model=CustomerTicketCollectionResponse)
def get_customer_tickets(
    response: Response,
    customer: Customer,
    database: Database,
    signer: Signer,
    settings: ApplicationSettings,
) -> CustomerTicketCollectionResponse:
    response.headers["Cache-Control"] = "no-store"
    return CustomerTicketCollectionResponse(
        items=list_customer_tickets(database, customer.id, signer, settings.frontend_origin)
    )


@router.get("/shared/{token}", response_model=SharedTicketResponse)
def get_ticket_by_share_token(
    token: Annotated[str, Path(min_length=1, max_length=128)],
    response: Response,
    database: Database,
    signer: Signer,
) -> SharedTicketResponse:
    response.headers["Cache-Control"] = "no-store"
    try:
        return get_shared_ticket(database, token, signer)
    except SharedTicketNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket was not found.",
        ) from error
