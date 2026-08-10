from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.catalog.dependencies import get_ticketmaster_client
from backend.catalog.schemas import CatalogEvent
from backend.catalog.ticketmaster import CatalogEventSnapshot
from backend.core.settings import Settings
from backend.database.engine import get_engine
from backend.database.models import (
    CatalogSnapshot,
    Event,
    Reservation,
    ReservationStatus,
    User,
    UserRole,
)
from backend.database.seed import CUSTOMER_ONE_ID, ORGANIZER_ID
from backend.main import create_app

pytestmark = pytest.mark.integration

PROVIDER_EVENT_ID = "event-management-integration-test"


class StubCatalogClient:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.provider_name = "Original Ticketmaster Name"

    def get_event_snapshot(self, provider_event_id: str) -> CatalogEventSnapshot:
        self.calls.append(provider_event_id)
        return CatalogEventSnapshot(
            event=CatalogEvent(
                provider_event_id=provider_event_id,
                name=self.provider_name,
                description="Original provider description.",
                image_url="https://images.test/original.jpg",
                source_url="https://ticketmaster.test/original",
            ),
            raw_data={
                "id": provider_event_id,
                "name": self.provider_name,
                "provider_only": {"classification": "Music"},
            },
        )


def make_user(user_id: UUID = ORGANIZER_ID, role: UserRole = UserRole.ORGANIZER) -> User:
    return User(
        id=user_id,
        email=f"{role.value}.{user_id}@example.com",
        password_hash="not-used-in-event-tests",
        role=role,
    )


def make_event_app(user: User, catalog: StubCatalogClient) -> FastAPI:
    application = create_app(Settings(ticketmaster_api_key="test-key"))
    application.dependency_overrides[get_current_user] = lambda: user
    application.dependency_overrides[get_ticketmaster_client] = lambda: catalog
    return application


def event_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "provider_event_id": PROVIDER_EVENT_ID,
        "name": "Local Aurora Session",
        "description": "Local organizer copy.",
        "venue_name": "Gather Test Hall",
        "address": "100 Test Avenue",
        "city": "Sao Paulo",
        "country_code": "BR",
        "start_at": "2032-09-21T22:00:00-03:00",
        "capacity": 10,
        "price_minor": 12500,
        "currency": "BRL",
    }
    payload.update(overrides)
    return payload


def cleanup_test_event() -> None:
    with Session(get_engine()) as database, database.begin():
        snapshot_ids = list(
            database.scalars(
                select(CatalogSnapshot.id).where(
                    CatalogSnapshot.provider_event_id == PROVIDER_EVENT_ID
                )
            )
        )
        if not snapshot_ids:
            return
        event_ids = list(
            database.scalars(select(Event.id).where(Event.catalog_snapshot_id.in_(snapshot_ids)))
        )
        if event_ids:
            database.execute(delete(Reservation).where(Reservation.event_id.in_(event_ids)))
            database.execute(delete(Event).where(Event.id.in_(event_ids)))
        database.execute(delete(CatalogSnapshot).where(CatalogSnapshot.id.in_(snapshot_ids)))


def test_organizer_creates_updates_lists_and_publishes_an_owned_snapshot() -> None:
    cleanup_test_event()
    catalog = StubCatalogClient()
    application = make_event_app(make_user(), catalog)

    try:
        with TestClient(application) as client:
            created_response = client.post("/api/events", json=event_payload())
            assert created_response.status_code == 201
            created = created_response.json()
            event_id = UUID(created["id"])
            assert created["organizer_id"] == str(ORGANIZER_ID)
            assert created["status"] == "draft"
            assert created["source"]["name"] == "Original Ticketmaster Name"
            assert catalog.calls == [PROVIDER_EVENT_ID]

            catalog.provider_name = "Changed at Ticketmaster"
            listed_response = client.get("/api/events/organizer")
            assert listed_response.status_code == 200
            listed_event = next(
                item for item in listed_response.json()["items"] if item["id"] == str(event_id)
            )
            assert listed_event["source"]["name"] == "Original Ticketmaster Name"
            assert catalog.calls == [PROVIDER_EVENT_ID]

            with Session(get_engine()) as database, database.begin():
                snapshot = database.scalar(
                    select(CatalogSnapshot).where(
                        CatalogSnapshot.provider_event_id == PROVIDER_EVENT_ID
                    )
                )
                assert snapshot is not None
                assert snapshot.raw_data["provider_only"] == {"classification": "Music"}
                database.add(
                    Reservation(
                        customer_id=CUSTOMER_ONE_ID,
                        event_id=event_id,
                        quantity=3,
                        status=ReservationStatus.PENDING,
                        expires_at=datetime.now(UTC) + timedelta(minutes=10),
                    )
                )

            unsafe_response = client.put(
                f"/api/events/{event_id}",
                json={
                    key: value
                    for key, value in event_payload(capacity=2).items()
                    if key != "provider_event_id"
                },
            )
            assert unsafe_response.status_code == 409
            assert "(3)" in unsafe_response.json()["detail"]

            updated_response = client.put(
                f"/api/events/{event_id}",
                json={
                    key: value
                    for key, value in event_payload(capacity=3, city="Campinas").items()
                    if key != "provider_event_id"
                },
            )
            assert updated_response.status_code == 200
            assert updated_response.json()["capacity"] == 3
            assert updated_response.json()["city"] == "Campinas"

            stranger = make_user(uuid4())
            application.dependency_overrides[get_current_user] = lambda: stranger
            assert (
                client.put(
                    f"/api/events/{event_id}",
                    json={
                        key: value
                        for key, value in event_payload().items()
                        if key != "provider_event_id"
                    },
                ).status_code
                == 404
            )
            assert client.get("/api/events/organizer").json() == {"items": []}

            application.dependency_overrides[get_current_user] = lambda: make_user()
            published_response = client.post(f"/api/events/{event_id}/publish")
            assert published_response.status_code == 200
            assert published_response.json()["status"] == "published"
    finally:
        cleanup_test_event()


def test_event_input_and_role_are_rejected_before_provider_access() -> None:
    catalog = StubCatalogClient()
    organizer_client = TestClient(make_event_app(make_user(), catalog))

    invalid_response = organizer_client.post(
        "/api/events",
        json=event_payload(start_at="2020-01-01T00:00:00Z", price_minor=-1, capacity=0),
    )
    assert invalid_response.status_code == 422
    assert catalog.calls == []

    gate_client = TestClient(make_event_app(make_user(role=UserRole.GATE), catalog))
    denied_response = gate_client.post("/api/events", json=event_payload())
    assert denied_response.status_code == 403
    assert catalog.calls == []
