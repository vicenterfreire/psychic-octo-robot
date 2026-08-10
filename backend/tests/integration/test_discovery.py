from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.core.settings import Settings
from backend.database.engine import get_engine
from backend.database.models import (
    CatalogProvider,
    CatalogSnapshot,
    Event,
    EventStatus,
    Reservation,
    ReservationStatus,
)
from backend.database.seed import CUSTOMER_ONE_ID, ORGANIZER_ID
from backend.main import create_app

pytestmark = pytest.mark.integration

PROVIDER_PREFIX = "discovery-integration-"


def cleanup_discovery_events() -> None:
    with Session(get_engine()) as database, database.begin():
        snapshot_ids = list(
            database.scalars(
                select(CatalogSnapshot.id).where(
                    CatalogSnapshot.provider_event_id.startswith(PROVIDER_PREFIX)
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


def add_event(
    database: Session,
    *,
    suffix: str,
    name: str,
    status: EventStatus,
    start_at: datetime,
    capacity: int = 10,
) -> Event:
    snapshot = CatalogSnapshot(
        provider=CatalogProvider.TICKETMASTER,
        provider_event_id=f"{PROVIDER_PREFIX}{suffix}",
        name=f"Provider {name}",
        description="Provider description must stay outside the public response.",
        image_url=f"https://images.test/{suffix}.jpg",
        source_url=f"https://ticketmaster.test/{suffix}",
        raw_data={"private_provider_field": suffix},
    )
    database.add(snapshot)
    database.flush()
    event = Event(
        organizer_id=ORGANIZER_ID,
        catalog_snapshot_id=snapshot.id,
        name=name,
        description=f"Local details for {name}.",
        venue_name="Discovery Arena",
        address="100 Search Avenue",
        city="Curitiba",
        country_code="BR",
        start_at=start_at,
        capacity=capacity,
        price_minor=12345,
        currency="BRL",
        status=status,
    )
    database.add(event)
    database.flush()
    return event


def add_reservation(
    database: Session,
    event_id: UUID,
    *,
    quantity: int,
    status: ReservationStatus,
    created_at: datetime,
    expires_at: datetime,
) -> None:
    database.add(
        Reservation(
            customer_id=CUSTOMER_ONE_ID,
            event_id=event_id,
            quantity=quantity,
            status=status,
            created_at=created_at,
            expires_at=expires_at,
        )
    )


def test_public_discovery_filters_searches_and_calculates_availability() -> None:
    cleanup_discovery_events()
    now = datetime.now(UTC)
    with Session(get_engine()) as database, database.begin():
        published = add_event(
            database,
            suffix="published",
            name="Discovery Alpha Night",
            status=EventStatus.PUBLISHED,
            start_at=now + timedelta(days=30),
        )
        draft = add_event(
            database,
            suffix="draft",
            name="Discovery Alpha Draft",
            status=EventStatus.DRAFT,
            start_at=now + timedelta(days=31),
        )
        past = add_event(
            database,
            suffix="past",
            name="Discovery Alpha Past",
            status=EventStatus.PUBLISHED,
            start_at=now - timedelta(days=1),
        )
        published_id = published.id
        draft_id = draft.id
        past_id = past.id

        add_reservation(
            database,
            published_id,
            quantity=2,
            status=ReservationStatus.APPROVED,
            created_at=now - timedelta(minutes=5),
            expires_at=now + timedelta(minutes=5),
        )
        add_reservation(
            database,
            published_id,
            quantity=3,
            status=ReservationStatus.PENDING,
            created_at=now - timedelta(minutes=5),
            expires_at=now + timedelta(minutes=5),
        )
        add_reservation(
            database,
            published_id,
            quantity=4,
            status=ReservationStatus.PENDING,
            created_at=now - timedelta(minutes=20),
            expires_at=now - timedelta(minutes=10),
        )
        add_reservation(
            database,
            published_id,
            quantity=1,
            status=ReservationStatus.DECLINED,
            created_at=now - timedelta(minutes=5),
            expires_at=now + timedelta(minutes=5),
        )

    application = create_app(Settings())
    try:
        with TestClient(application) as client:
            response = client.get("/api/events", params={"q": "  DISCOVERY ALPHA  "})
            assert response.status_code == 200
            assert response.json()["items"] == [
                {
                    "id": str(published_id),
                    "name": "Discovery Alpha Night",
                    "description": "Local details for Discovery Alpha Night.",
                    "venue_name": "Discovery Arena",
                    "address": "100 Search Avenue",
                    "city": "Curitiba",
                    "country_code": "BR",
                    "start_at": (now + timedelta(days=30)).isoformat().replace("+00:00", "Z"),
                    "capacity": 10,
                    "available_quantity": 5,
                    "price_minor": 12345,
                    "currency": "BRL",
                    "image_url": "https://images.test/published.jpg",
                }
            ]
            serialized = response.json()["items"][0]
            assert "organizer_id" not in serialized
            assert "status" not in serialized
            assert "source" not in serialized
            assert "raw_data" not in serialized

            assert client.get("/api/events", params={"q": "%"}).json() == {"items": []}
            assert client.get(f"/api/events/{draft_id}").status_code == 404
            assert client.get(f"/api/events/{past_id}").status_code == 404

            detail_response = client.get(f"/api/events/{published_id}")
            assert detail_response.status_code == 200
            assert detail_response.json() == serialized
            assert client.get(f"/api/events/{uuid4()}").status_code == 404
    finally:
        cleanup_discovery_events()
