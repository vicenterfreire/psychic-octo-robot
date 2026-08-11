from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from typing import cast
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.core.settings import Settings
from backend.database.engine import get_engine
from backend.database.models import (
    CatalogProvider,
    CatalogSnapshot,
    Event,
    EventStatus,
    Reservation,
    ReservationStatus,
    Ticket,
    User,
    UserRole,
)
from backend.database.seed import CUSTOMER_ONE_ID, CUSTOMER_TWO_ID, ORGANIZER_ID
from backend.main import create_app

pytestmark = pytest.mark.integration

PROVIDER_PREFIX = "reservation-integration-"
FUTURE_START_DELAY = timedelta(days=30)


def make_user(user_id: UUID = CUSTOMER_ONE_ID, role: UserRole = UserRole.CUSTOMER) -> User:
    return User(
        id=user_id,
        email=f"{role.value}.{user_id}@example.com",
        password_hash="not-used-in-reservation-tests",
        role=role,
    )


def make_reservation_app(user: User | None = None) -> FastAPI:
    application = create_app(Settings(reservation_lifetime_seconds=600))
    resolved_user = user or make_user()
    application.dependency_overrides[get_current_user] = lambda: resolved_user
    return application


def add_event(
    suffix: str,
    capacity: int,
    *,
    status: EventStatus = EventStatus.PUBLISHED,
    starts_in: timedelta = FUTURE_START_DELAY,
) -> UUID:
    with Session(get_engine()) as database, database.begin():
        snapshot = CatalogSnapshot(
            provider=CatalogProvider.TICKETMASTER,
            provider_event_id=f"{PROVIDER_PREFIX}{suffix}",
            name="Provider reservation event",
            description="Provider description.",
            image_url=None,
            source_url=None,
            raw_data={"id": suffix},
        )
        database.add(snapshot)
        database.flush()
        event = Event(
            organizer_id=ORGANIZER_ID,
            catalog_snapshot_id=snapshot.id,
            name=f"Reservation event {suffix}",
            description="A reservation integration fixture.",
            venue_name="Reservation Hall",
            address="10 Lock Street",
            city="Sao Paulo",
            country_code="BR",
            start_at=datetime.now(UTC) + starts_in,
            capacity=capacity,
            price_minor=10000,
            currency="BRL",
            status=status,
        )
        database.add(event)
        database.flush()
        return event.id


def cleanup_reservation_events() -> None:
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
            reservation_ids = select(Reservation.id).where(Reservation.event_id.in_(event_ids))
            database.execute(delete(Ticket).where(Ticket.reservation_id.in_(reservation_ids)))
            database.execute(delete(Reservation).where(Reservation.event_id.in_(event_ids)))
            database.execute(delete(Event).where(Event.id.in_(event_ids)))
        database.execute(delete(CatalogSnapshot).where(CatalogSnapshot.id.in_(snapshot_ids)))


def test_hold_reduces_availability_expires_and_enforces_ownership() -> None:
    cleanup_reservation_events()
    event_id = add_event("lifecycle", capacity=5)
    draft_event_id = add_event("draft", capacity=5, status=EventStatus.DRAFT)
    past_event_id = add_event("past", capacity=5, starts_in=-timedelta(days=1))
    application = make_reservation_app()

    try:
        with TestClient(application) as client:
            for unavailable_event_id in (draft_event_id, past_event_id):
                assert (
                    client.post(
                        "/api/reservations",
                        json={"event_id": str(unavailable_event_id), "quantity": 1},
                    ).status_code
                    == 404
                )

            created_response = client.post(
                "/api/reservations",
                json={"event_id": str(event_id), "quantity": 4},
            )
            assert created_response.status_code == 201
            assert created_response.headers["cache-control"] == "no-store"
            created = created_response.json()
            reservation_id = UUID(created["id"])
            assert created["status"] == "pending"
            assert created["quantity"] == 4
            assert datetime.fromisoformat(created["expires_at"]) - datetime.fromisoformat(
                created["server_time"]
            ) == timedelta(minutes=10)

            assert client.get(f"/api/events/{event_id}").json()["available_quantity"] == 1
            conflict = client.post(
                "/api/reservations",
                json={"event_id": str(event_id), "quantity": 2},
            )
            assert conflict.status_code == 409
            assert conflict.json() == {"detail": "Only 1 ticket is currently available."}

            application.dependency_overrides[get_current_user] = lambda: make_user(CUSTOMER_TWO_ID)
            assert client.get(f"/api/reservations/{reservation_id}").status_code == 404

            application.dependency_overrides[get_current_user] = lambda: make_user()
            with Session(get_engine()) as database, database.begin():
                database_now = cast(datetime, database.scalar(select(func.now())))
                database.execute(
                    update(Reservation)
                    .where(Reservation.id == reservation_id)
                    .values(
                        created_at=database_now - timedelta(minutes=20),
                        expires_at=database_now - timedelta(minutes=10),
                    )
                )

            expired_response = client.get(f"/api/reservations/{reservation_id}")
            assert expired_response.status_code == 200
            assert expired_response.headers["cache-control"] == "no-store"
            assert expired_response.json()["status"] == "expired"
            assert client.get(f"/api/events/{event_id}").json()["available_quantity"] == 5

            replacement = client.post(
                "/api/reservations",
                json={"event_id": str(event_id), "quantity": 5},
            )
            assert replacement.status_code == 201

            application.dependency_overrides[get_current_user] = lambda: make_user(
                role=UserRole.GATE
            )
            assert (
                client.post(
                    "/api/reservations",
                    json={"event_id": str(event_id), "quantity": 1},
                ).status_code
                == 403
            )
    finally:
        cleanup_reservation_events()


def test_simultaneous_holds_cannot_exceed_final_availability() -> None:
    cleanup_reservation_events()
    event_id = add_event("concurrency", capacity=5)
    application = make_reservation_app()
    barrier = Barrier(3)

    def reserve_four() -> int:
        with TestClient(application) as client:
            barrier.wait()
            response = client.post(
                "/api/reservations",
                json={"event_id": str(event_id), "quantity": 4},
            )
            return cast(int, response.status_code)

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = [executor.submit(reserve_four) for _ in range(2)]
            barrier.wait()
            statuses = sorted(response.result(timeout=10) for response in responses)

        assert statuses == [201, 409]
        with Session(get_engine()) as database:
            held_quantity = database.scalar(
                select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                    Reservation.event_id == event_id,
                    Reservation.status == ReservationStatus.PENDING,
                    Reservation.expires_at > func.now(),
                )
            )
        assert held_quantity == 4
    finally:
        cleanup_reservation_events()


def test_approved_payment_issues_tickets_once_and_preserves_the_terminal_result() -> None:
    cleanup_reservation_events()
    event_id = add_event("approved-payment", capacity=5)
    application = make_reservation_app()

    try:
        with TestClient(application) as client:
            hold = client.post(
                "/api/reservations",
                json={"event_id": str(event_id), "quantity": 2},
            ).json()
            reservation_id = UUID(hold["id"])

            approved_response = client.post(
                f"/api/reservations/{reservation_id}/payment",
                json={"outcome": "approved"},
            )
            assert approved_response.status_code == 200
            assert approved_response.headers["cache-control"] == "no-store"
            assert approved_response.json()["status"] == "approved"
            assert approved_response.json()["ticket_count"] == 2

            repeated_approval = client.post(
                f"/api/reservations/{reservation_id}/payment",
                json={"outcome": "approved"},
            )
            contradictory_retry = client.post(
                f"/api/reservations/{reservation_id}/payment",
                json={"outcome": "declined"},
            )
            assert repeated_approval.json()["status"] == "approved"
            assert repeated_approval.json()["ticket_count"] == 2
            assert contradictory_retry.json()["status"] == "approved"
            assert contradictory_retry.json()["ticket_count"] == 2

            restored = client.get(f"/api/reservations/{reservation_id}")
            assert restored.json()["status"] == "approved"
            assert restored.json()["ticket_count"] == 2
            assert client.get(f"/api/events/{event_id}").json()["available_quantity"] == 3

            application.dependency_overrides[get_current_user] = lambda: make_user(CUSTOMER_TWO_ID)
            assert (
                client.post(
                    f"/api/reservations/{reservation_id}/payment",
                    json={"outcome": "approved"},
                ).status_code
                == 404
            )

        with Session(get_engine()) as database:
            ticket_numbers = list(
                database.scalars(
                    select(Ticket.ticket_number)
                    .where(Ticket.reservation_id == reservation_id)
                    .order_by(Ticket.ticket_number)
                )
            )
        assert ticket_numbers == [1, 2]
    finally:
        cleanup_reservation_events()


def test_declined_and_expired_payments_release_inventory_without_tickets() -> None:
    cleanup_reservation_events()
    event_id = add_event("released-payment", capacity=5)
    application = make_reservation_app()

    try:
        with TestClient(application) as client:
            declined_hold = client.post(
                "/api/reservations",
                json={"event_id": str(event_id), "quantity": 4},
            ).json()
            declined_id = UUID(declined_hold["id"])
            declined = client.post(
                f"/api/reservations/{declined_id}/payment",
                json={"outcome": "declined"},
            )
            assert declined.json()["status"] == "declined"
            assert declined.json()["ticket_count"] == 0
            assert client.get(f"/api/events/{event_id}").json()["available_quantity"] == 5

            declined_retry = client.post(
                f"/api/reservations/{declined_id}/payment",
                json={"outcome": "approved"},
            )
            assert declined_retry.json()["status"] == "declined"
            assert declined_retry.json()["ticket_count"] == 0

            expired_hold = client.post(
                "/api/reservations",
                json={"event_id": str(event_id), "quantity": 5},
            ).json()
            expired_id = UUID(expired_hold["id"])
            with Session(get_engine()) as database, database.begin():
                database_now = cast(datetime, database.scalar(select(func.now())))
                database.execute(
                    update(Reservation)
                    .where(Reservation.id == expired_id)
                    .values(
                        created_at=database_now - timedelta(minutes=20),
                        expires_at=database_now - timedelta(minutes=10),
                    )
                )

            expired = client.post(
                f"/api/reservations/{expired_id}/payment",
                json={"outcome": "approved"},
            )
            assert expired.json()["status"] == "expired"
            assert expired.json()["ticket_count"] == 0
            assert client.get(f"/api/events/{event_id}").json()["available_quantity"] == 5

            invalid_outcome = client.post(
                f"/api/reservations/{expired_id}/payment",
                json={"outcome": "unknown"},
            )
            assert invalid_outcome.status_code == 422
    finally:
        cleanup_reservation_events()


def test_simultaneous_approved_payments_issue_each_ticket_once() -> None:
    cleanup_reservation_events()
    event_id = add_event("concurrent-payment", capacity=5)
    application = make_reservation_app()
    with TestClient(application) as client:
        hold = client.post(
            "/api/reservations",
            json={"event_id": str(event_id), "quantity": 3},
        ).json()
    reservation_id = UUID(hold["id"])
    barrier = Barrier(3)

    def approve() -> tuple[int, str, int]:
        with TestClient(application) as client:
            barrier.wait()
            response = client.post(
                f"/api/reservations/{reservation_id}/payment",
                json={"outcome": "approved"},
            )
            body = response.json()
            return (
                cast(int, response.status_code),
                cast(str, body["status"]),
                cast(int, body["ticket_count"]),
            )

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = [executor.submit(approve) for _ in range(2)]
            barrier.wait()
            results = [response.result(timeout=10) for response in responses]

        assert results == [(200, "approved", 3), (200, "approved", 3)]
        with Session(get_engine()) as database:
            ticket_numbers = list(
                database.scalars(
                    select(Ticket.ticket_number)
                    .where(Ticket.reservation_id == reservation_id)
                    .order_by(Ticket.ticket_number)
                )
            )
        assert ticket_numbers == [1, 2, 3]
    finally:
        cleanup_reservation_events()
