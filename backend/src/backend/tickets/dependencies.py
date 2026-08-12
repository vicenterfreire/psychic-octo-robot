from typing import Annotated

from fastapi import Depends, HTTPException, status

from backend.core.dependencies import get_application_settings
from backend.core.settings import Settings
from backend.tickets.signing import InvalidTicketSigningSecretError, TicketSigner

ApplicationSettings = Annotated[Settings, Depends(get_application_settings)]


def get_ticket_signer(settings: ApplicationSettings) -> TicketSigner:
    """Provide a signer or fail ticket endpoints closed when configuration is unsafe."""

    try:
        return TicketSigner(settings.ticket_hmac_secret or "")
    except InvalidTicketSigningSecretError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ticket signing is not configured.",
        ) from error
