from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.auth.dependencies import require_roles
from backend.catalog.dependencies import get_ticketmaster_client
from backend.catalog.schemas import CatalogSearchResponse
from backend.catalog.ticketmaster import (
    CatalogConfigurationError,
    CatalogCredentialsError,
    CatalogInvalidResponseError,
    CatalogQuotaError,
    CatalogTimeoutError,
    CatalogUnavailableError,
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
    except CatalogConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog search is not configured.",
        ) from error
    except CatalogCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog provider credentials were rejected.",
        ) from error
    except CatalogQuotaError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog provider quota is temporarily unavailable.",
        ) from error
    except CatalogTimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Catalog provider timed out.",
        ) from error
    except (CatalogUnavailableError, CatalogInvalidResponseError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Catalog provider is unavailable.",
        ) from error

    return CatalogSearchResponse(items=items)
