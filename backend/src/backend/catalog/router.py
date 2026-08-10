from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.auth.dependencies import require_roles
from backend.catalog.dependencies import get_ticketmaster_client
from backend.catalog.http_errors import catalog_http_exception
from backend.catalog.schemas import CatalogSearchResponse
from backend.catalog.ticketmaster import (
    CatalogProviderError,
    TicketmasterClient,
)
from backend.database.models import User, UserRole

router = APIRouter(prefix="/catalog", tags=["catalog"])

Organizer = Annotated[User, Depends(require_roles(UserRole.ORGANIZER))]
CatalogClient = Annotated[TicketmasterClient, Depends(get_ticketmaster_client)]


@router.get("/events", response_model=CatalogSearchResponse)
def search_catalog_events(
    q: Annotated[str, Query(min_length=2, max_length=100)],
    _organizer: Organizer,
    client: CatalogClient,
) -> CatalogSearchResponse:
    keyword = q.strip()
    if len(keyword) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Search query must contain at least two non-whitespace characters.",
        )

    try:
        items = client.search_events(keyword)
    except CatalogProviderError as error:
        raise catalog_http_exception(error) from error

    return CatalogSearchResponse(items=items)
