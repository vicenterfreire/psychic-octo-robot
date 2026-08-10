from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, Field, ValidationError

from backend.catalog.schemas import CatalogEvent

TICKETMASTER_BASE_URL = "https://app.ticketmaster.com/discovery/v2/"
SEARCH_RESULT_LIMIT = 12


class CatalogProviderError(Exception):
    """Base error for safe provider failure mapping."""


class CatalogConfigurationError(CatalogProviderError):
    """The provider credential is not configured."""


class CatalogCredentialsError(CatalogProviderError):
    """The provider rejected its configured credential."""


class CatalogTimeoutError(CatalogProviderError):
    """The provider did not answer within the configured deadline."""


class CatalogQuotaError(CatalogProviderError):
    """The provider quota has been exhausted."""


class CatalogUnavailableError(CatalogProviderError):
    """The provider could not serve the request."""


class CatalogInvalidResponseError(CatalogProviderError):
    """The provider returned data outside the expected contract."""


class _TicketmasterImage(BaseModel):
    url: str = Field(max_length=2048)
    ratio: str | None = None
    width: int = 0
    fallback: bool = False


class _TicketmasterEvent(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    info: str | None = None
    please_note: str | None = Field(default=None, alias="pleaseNote")
    url: str | None = Field(default=None, max_length=2048)
    images: list[_TicketmasterImage] = Field(default_factory=list)


class _TicketmasterEmbedded(BaseModel):
    events: list[_TicketmasterEvent] = Field(default_factory=list)


class _TicketmasterResponse(BaseModel):
    embedded: _TicketmasterEmbedded | None = Field(default=None, alias="_embedded")


def _safe_public_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value


def _select_image(images: list[_TicketmasterImage]) -> str | None:
    public_images = [image for image in images if _safe_public_url(image.url)]
    if not public_images:
        return None

    selected = max(
        public_images,
        key=lambda image: (not image.fallback, image.ratio == "16_9", image.width),
    )
    return selected.url


class TicketmasterClient:
    def __init__(
        self,
        api_key: str | None,
        timeout_seconds: float,
        *,
        base_url: str = TICKETMASTER_BASE_URL,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._base_url = base_url
        self._transport = transport

    def search_events(self, keyword: str) -> list[CatalogEvent]:
        if not self._api_key:
            raise CatalogConfigurationError

        try:
            with httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
                transport=self._transport,
                headers={"Accept": "application/json", "User-Agent": "Gather/0.1"},
            ) as client:
                response = client.get(
                    "events.json",
                    params={
                        "apikey": self._api_key,
                        "keyword": keyword,
                        "locale": "*",
                        "size": SEARCH_RESULT_LIMIT,
                        "sort": "relevance,desc",
                        "source": "ticketmaster",
                    },
                )
        except httpx.TimeoutException as error:
            raise CatalogTimeoutError from error
        except httpx.RequestError as error:
            raise CatalogUnavailableError from error

        if response.status_code in {401, 403}:
            raise CatalogCredentialsError
        if response.status_code == 429:
            raise CatalogQuotaError
        if response.status_code >= 400:
            raise CatalogUnavailableError

        try:
            provider_response = _TicketmasterResponse.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            raise CatalogInvalidResponseError from error

        if provider_response.embedded is None:
            return []

        return [
            CatalogEvent(
                provider_event_id=event.id,
                name=event.name,
                description=event.info or event.please_note,
                image_url=_select_image(event.images),
                source_url=_safe_public_url(event.url),
            )
            for event in provider_response.embedded.events
        ]
