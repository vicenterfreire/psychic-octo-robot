from collections.abc import Callable

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth.dependencies import get_current_user
from backend.catalog.dependencies import get_ticketmaster_client
from backend.catalog.schemas import CatalogEvent
from backend.catalog.ticketmaster import (
    CatalogConfigurationError,
    CatalogCredentialsError,
    CatalogInvalidResponseError,
    CatalogProviderError,
    CatalogQuotaError,
    CatalogTimeoutError,
    CatalogUnavailableError,
    TicketmasterClient,
)
from backend.core.settings import Settings
from backend.database.models import User, UserRole
from backend.database.seed import GATE_ID, ORGANIZER_ID
from backend.main import create_app

API_KEY = "private-ticketmaster-test-key"
TEST_BASE_URL = "https://ticketmaster.test/discovery/v2/"


def make_provider_client(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    api_key: str | None = API_KEY,
) -> TicketmasterClient:
    return TicketmasterClient(
        api_key=api_key,
        timeout_seconds=0.1,
        base_url=TEST_BASE_URL,
        transport=httpx.MockTransport(handler),
    )


def test_ticketmaster_client_normalizes_only_the_internal_contract() -> None:
    def provider_response(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/discovery/v2/events.json"
        assert request.url.params["apikey"] == API_KEY
        assert request.url.params["keyword"] == "Aurora"
        assert request.url.params["source"] == "ticketmaster"
        assert request.url.params["size"] == "12"
        return httpx.Response(
            200,
            json={
                "_embedded": {
                    "events": [
                        {
                            "id": "event-123",
                            "name": "Aurora World Tour",
                            "info": "A live music event.",
                            "url": "https://www.ticketmaster.com/event-123",
                            "images": [
                                {
                                    "url": "https://images.test/fallback.jpg",
                                    "ratio": "16_9",
                                    "width": 2048,
                                    "fallback": True,
                                },
                                {
                                    "url": "https://images.test/event.jpg",
                                    "ratio": "16_9",
                                    "width": 1024,
                                    "fallback": False,
                                },
                            ],
                            "dates": {"start": {"dateTime": "2030-08-10T22:00:00Z"}},
                            "_embedded": {"venues": [{"name": "Provider Venue"}]},
                        }
                    ]
                }
            },
        )

    result = make_provider_client(provider_response).search_events("Aurora")

    assert result == [
        CatalogEvent(
            provider_event_id="event-123",
            name="Aurora World Tour",
            description="A live music event.",
            image_url="https://images.test/event.jpg",
            source_url="https://www.ticketmaster.com/event-123",
        )
    ]
    serialized = result[0].model_dump_json()
    assert API_KEY not in serialized
    assert "dates" not in serialized
    assert "venues" not in serialized


def test_ticketmaster_client_returns_an_empty_list_without_embedded_events() -> None:
    client = make_provider_client(lambda _request: httpx.Response(200, json={"page": {}}))

    assert client.search_events("nothing") == []


def test_ticketmaster_client_filters_unsafe_urls_and_uses_the_provider_note() -> None:
    client = make_provider_client(
        lambda _request: httpx.Response(
            200,
            json={
                "_embedded": {
                    "events": [
                        {
                            "id": "event-unsafe-urls",
                            "name": "Provider Event",
                            "pleaseNote": "Provider guidance.",
                            "url": "javascript:alert('unsafe')",
                            "images": [{"url": "data:image/png;base64,unsafe"}],
                        }
                    ]
                }
            },
        )
    )

    assert client.search_events("Provider") == [
        CatalogEvent(
            provider_event_id="event-unsafe-urls",
            name="Provider Event",
            description="Provider guidance.",
            image_url=None,
            source_url=None,
        )
    ]


def test_ticketmaster_client_rejects_missing_configuration_before_a_request() -> None:
    def unexpected_request(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("The provider must not be called without a key.")

    client = make_provider_client(unexpected_request, api_key=None)

    with pytest.raises(CatalogConfigurationError):
        client.search_events("Aurora")


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [
        (401, CatalogCredentialsError),
        (429, CatalogQuotaError),
        (503, CatalogUnavailableError),
    ],
)
def test_ticketmaster_client_maps_provider_failures(
    status_code: int,
    error_type: type[CatalogProviderError],
) -> None:
    client = make_provider_client(
        lambda _request: httpx.Response(status_code, json={"fault": {"detail": "secret"}})
    )

    with pytest.raises(error_type):
        client.search_events("Aurora")


def test_ticketmaster_client_maps_timeouts_without_leaking_the_request() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("provider timeout", request=request)

    client = make_provider_client(timeout)

    with pytest.raises(CatalogTimeoutError) as raised:
        client.search_events("Aurora")

    assert API_KEY not in str(raised.value)


def test_ticketmaster_client_rejects_invalid_provider_json() -> None:
    client = make_provider_client(lambda _request: httpx.Response(200, content=b"not-json"))

    with pytest.raises(CatalogInvalidResponseError):
        client.search_events("Aurora")


class StubCatalogClient:
    def __init__(
        self,
        items: list[CatalogEvent] | None = None,
        error: CatalogProviderError | None = None,
    ) -> None:
        self.items = items or []
        self.error = error
        self.queries: list[str] = []

    def search_events(self, keyword: str) -> list[CatalogEvent]:
        self.queries.append(keyword)
        if self.error:
            raise self.error
        return self.items


def make_user(role: UserRole) -> User:
    return User(
        id=ORGANIZER_ID if role is UserRole.ORGANIZER else GATE_ID,
        email=f"{role.value}@example.com",
        password_hash="not-used-in-catalog-tests",
        role=role,
    )


def make_catalog_app(role: UserRole, stub: StubCatalogClient) -> FastAPI:
    application = create_app(Settings(ticketmaster_api_key=API_KEY))
    application.dependency_overrides[get_current_user] = lambda: make_user(role)
    application.dependency_overrides[get_ticketmaster_client] = lambda: stub
    return application


def test_catalog_endpoint_is_organizer_only_and_normalizes_the_query() -> None:
    item = CatalogEvent(
        provider_event_id="event-123",
        name="Aurora World Tour",
        description=None,
        image_url=None,
        source_url="https://www.ticketmaster.com/event-123",
    )
    stub = StubCatalogClient([item])
    organizer_client = TestClient(make_catalog_app(UserRole.ORGANIZER, stub))

    response = organizer_client.get("/api/catalog/events", params={"q": "  Aurora  "})

    assert response.status_code == 200
    assert response.json() == {"items": [item.model_dump()]}
    assert stub.queries == ["Aurora"]
    assert API_KEY not in response.text

    gate_stub = StubCatalogClient([item])
    gate_client = TestClient(make_catalog_app(UserRole.GATE, gate_stub))
    denied_response = gate_client.get("/api/catalog/events", params={"q": "Aurora"})

    assert denied_response.status_code == 403
    assert gate_stub.queries == []


def test_catalog_endpoint_rejects_a_whitespace_only_query() -> None:
    stub = StubCatalogClient()
    client = TestClient(make_catalog_app(UserRole.ORGANIZER, stub))

    response = client.get("/api/catalog/events", params={"q": "   "})

    assert response.status_code == 422
    assert stub.queries == []


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail"),
    [
        (CatalogConfigurationError(), 503, "Catalog search is not configured."),
        (CatalogCredentialsError(), 503, "Catalog provider credentials were rejected."),
        (CatalogQuotaError(), 503, "Catalog provider quota is temporarily unavailable."),
        (CatalogTimeoutError(), 504, "Catalog provider timed out."),
        (CatalogUnavailableError(), 502, "Catalog provider is unavailable."),
        (CatalogInvalidResponseError(), 502, "Catalog provider is unavailable."),
    ],
)
def test_catalog_endpoint_returns_stable_provider_errors(
    error: CatalogProviderError,
    expected_status: int,
    expected_detail: str,
) -> None:
    client = TestClient(make_catalog_app(UserRole.ORGANIZER, StubCatalogClient(error=error)))

    response = client.get("/api/catalog/events", params={"q": "Aurora"})

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
    assert API_KEY not in response.text
