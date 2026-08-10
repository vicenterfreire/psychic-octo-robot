from typing import Annotated

from fastapi import Depends

from backend.catalog.ticketmaster import TicketmasterClient
from backend.core.dependencies import get_application_settings
from backend.core.settings import Settings


def get_ticketmaster_client(
    settings: Annotated[Settings, Depends(get_application_settings)],
) -> TicketmasterClient:
    return TicketmasterClient(
        api_key=settings.ticketmaster_api_key,
        timeout_seconds=settings.ticketmaster_timeout_seconds,
    )
