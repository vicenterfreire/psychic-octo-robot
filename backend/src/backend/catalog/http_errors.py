from fastapi import HTTPException, status

from backend.catalog.ticketmaster import (
    CatalogConfigurationError,
    CatalogCredentialsError,
    CatalogInvalidResponseError,
    CatalogItemNotFoundError,
    CatalogProviderError,
    CatalogQuotaError,
    CatalogTimeoutError,
)


def catalog_http_exception(error: CatalogProviderError) -> HTTPException:
    if isinstance(error, CatalogItemNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalog event was not found.",
        )
    if isinstance(error, CatalogConfigurationError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog search is not configured.",
        )
    if isinstance(error, CatalogCredentialsError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog provider credentials were rejected.",
        )
    if isinstance(error, CatalogQuotaError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog provider quota is temporarily unavailable.",
        )
    if isinstance(error, CatalogTimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Catalog provider timed out.",
        )
    if isinstance(error, CatalogInvalidResponseError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Catalog provider is unavailable.",
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Catalog provider is unavailable.",
    )
