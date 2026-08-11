from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import delete
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
from backend.database.seed import CUSTOMER_ONE_ID, EVENT_ID, GATE_ID, ORGANIZER_ID
from backend.main import create_app
from backend.tickets.signing import TicketSigner

pytestmark = pytest.mark.integration

TEST_SECRET = "gate-validation-integration-secret-32-bytes"
OTHER_SNAPSHOT_ID = UUID("44444444-4444-4444-8444-444444444440")
OTHER_EVENT_ID = UUID("55555555-5555-4555-8555-555555555550")
RESERVATION_ID = UUID("66666666-6666-4666-8666-666666666650")
VALID_TICKET_ID = UUID("77777777-7777-4777-8777-777777777750")
USED_TICKET_ID = UUID("77777777-7777-4777-8777-777777777751")
REVOKED_TICKET_ID = UUID("77777777-7777-4777-8777-777777777752")
CONCURRENT_TICKET_ID = UUID("77777777-7777-4777-8777-777777777753")
TICKET_IDS = [
    VALID_TICKET_ID,
    USED_TICKET_ID,
    REVOKED_TICKET_ID,
    CONCURRENT_TICKET_ID,
]


def make_user(role: UserRole = UserRole.GATE) -> User:
    user_id = GATE_ID if role == UserRole.GATE else CUSTOMER_ONE_ID
    return User(
        id=user_id,
        email=f"{role.value}@example.com",
        password_hash="not-used-in-gate-tests",
        role=role,
    )


def make_gate_app(secret: str | None = TEST_SECRET) -> FastAPI:
    application = create_app(Settings(ticket_hmac_secret=secret))
    application.dependency_overrides[get_current_user] = lambda: make_user()
    return application


def reset_gate_fixture() -> None:
    with Session(get_engine()) as database, database.begin():
        database.execute(delete(Ticket).where(Ticket.id.in_(TICKET_IDS)))
        database.execute(delete(Reservation).where(Reservation.id == RESERVATION_ID))
        database.execute(delete(Event).where(Event.id == OTHER_EVENT_ID))
        database.execute(delete(CatalogSnapshot).where(CatalogSnapshot.id == OTHER_SNAPSHOT_ID))


def add_gate_fixture() -> None:
    reset_gate_fixture()
    issued_at = datetime.now(UTC) - timedelta(minutes=5)
    state_time = issued_at + timedelta(minutes=1)
    with Session(get_engine()) as database, database.begin():
        database.add(
            CatalogSnapshot(
                id=OTHER_SNAPSHOT_ID,
                provider=CatalogProvider.TICKETMASTER,
                provider_event_id="gate-integration-past-event",
                name="Past gate event",
                description="Gate selection fixture.",
                image_url=None,
                source_url=None,
                raw_data={"id": "gate-integration-past-event"},
            )
        )
        database.add(
            Event(
                id=OTHER_EVENT_ID,
                organizer_id=ORGANIZER_ID,
                catalog_snapshot_id=OTHER_SNAPSHOT_ID,
                name="Past gate event",
                description="A published event that remains selectable after its start.",
                venue_name="Gate Hall",
                address="20 Entry Street",
                city="Sao Paulo",
                country_code="BR",
                start_at=issued_at - timedelta(days=1),
                capacity=10,
                price_minor=10000,
                currency="BRL",
                status=EventStatus.PUBLISHED,
            )
        )
        database.add(
            Reservation(
                id=RESERVATION_ID,
                customer_id=CUSTOMER_ONE_ID,
                event_id=EVENT_ID,
                quantity=4,
                status=ReservationStatus.APPROVED,
                created_at=issued_at - timedelta(minutes=5),
                expires_at=issued_at,
            )
        )
        database.add_all(
            [
                Ticket(
                    id=VALID_TICKET_ID,
                    reservation_id=RESERVATION_ID,
                    ticket_number=1,
                    issued_at=issued_at,
                ),
                Ticket(
                    id=USED_TICKET_ID,
                    reservation_id=RESERVATION_ID,
                    ticket_number=2,
                    issued_at=issued_at,
                    used_at=state_time,
                    used_by_user_id=GATE_ID,
                ),
                Ticket(
                    id=REVOKED_TICKET_ID,
                    reservation_id=RESERVATION_ID,
                    ticket_number=3,
                    issued_at=issued_at,
                    revoked_at=state_time,
                ),
                Ticket(
                    id=CONCURRENT_TICKET_ID,
                    reservation_id=RESERVATION_ID,
                    ticket_number=4,
                    issued_at=issued_at,
                ),
            ]
        )


def validate(client: TestClient, event_id: UUID, token: str) -> Response:
    return cast(
        Response,
        client.post(
            "/api/gate/validations",
            json={"event_id": str(event_id), "token": token},
        ),
    )


def test_gate_lists_published_events_and_returns_authoritative_outcomes() -> None:
    add_gate_fixture()
    application = make_gate_app()
    signer = TicketSigner(TEST_SECRET)

    try:
        with TestClient(application) as client:
            events_response = client.get("/api/gate/events")
            assert events_response.status_code == 200
            assert events_response.headers["cache-control"] == "no-store"
            event_ids = {item["id"] for item in events_response.json()["items"]}
            assert str(EVENT_ID) in event_ids
            assert str(OTHER_EVENT_ID) in event_ids

            invalid_tokens = ["not-a-ticket", signer.sign(uuid4())]
            valid_token = signer.sign(VALID_TICKET_ID)
            version, identifier, signature = valid_token.split(".")
            changed_signature = signature[:-1] + ("A" if signature[-1] != "A" else "B")
            invalid_tokens.append(f"{version}.{identifier}.{changed_signature}")
            for invalid_token in invalid_tokens:
                response = validate(client, EVENT_ID, invalid_token)
                assert response.status_code == 200
                assert response.json()["outcome"] == "invalid"

            wrong_event = validate(client, OTHER_EVENT_ID, f"  {valid_token}\n")
            assert wrong_event.json()["outcome"] == "wrong_event"

            used_at_wrong_event = validate(client, OTHER_EVENT_ID, signer.sign(USED_TICKET_ID))
            assert used_at_wrong_event.json()["outcome"] == "wrong_event"

            revoked = validate(client, EVENT_ID, signer.sign(REVOKED_TICKET_ID))
            assert revoked.json()["outcome"] == "invalid"

            already_used = validate(client, EVENT_ID, signer.sign(USED_TICKET_ID))
            assert already_used.json()["outcome"] == "already_used"
            assert already_used.json()["ticket_number"] == 2
            assert already_used.json()["used_at"] is not None

            accepted = validate(client, EVENT_ID, valid_token)
            assert accepted.status_code == 200
            assert accepted.headers["cache-control"] == "no-store"
            assert accepted.json()["outcome"] == "valid"
            assert accepted.json()["ticket_number"] == 1
            assert accepted.json()["used_at"] is not None

            repeated = validate(client, EVENT_ID, valid_token)
            assert repeated.json()["outcome"] == "already_used"
            assert repeated.json()["used_at"] == accepted.json()["used_at"]

            unknown_event = validate(client, uuid4(), signer.sign(CONCURRENT_TICKET_ID))
            assert unknown_event.status_code == 404

            application.dependency_overrides[get_current_user] = lambda: make_user(
                UserRole.CUSTOMER
            )
            assert client.get("/api/gate/events").status_code == 403
            assert validate(client, EVENT_ID, signer.sign(CONCURRENT_TICKET_ID)).status_code == 403

        with Session(get_engine()) as database:
            accepted_ticket = database.get(Ticket, VALID_TICKET_ID)
            assert accepted_ticket is not None
            assert accepted_ticket.used_at is not None
            assert accepted_ticket.used_by_user_id == GATE_ID
    finally:
        reset_gate_fixture()


def test_concurrent_gate_validations_accept_a_ticket_only_once() -> None:
    add_gate_fixture()
    application = make_gate_app()
    token = TicketSigner(TEST_SECRET).sign(CONCURRENT_TICKET_ID)
    barrier = Barrier(3)

    def submit_validation() -> str:
        with TestClient(application) as client:
            barrier.wait()
            response = validate(client, EVENT_ID, token)
            return cast(str, response.json()["outcome"])

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = [executor.submit(submit_validation) for _ in range(2)]
            barrier.wait()
            outcomes = sorted(response.result(timeout=10) for response in responses)

        assert outcomes == ["already_used", "valid"]
        with Session(get_engine()) as database:
            ticket = database.get(Ticket, CONCURRENT_TICKET_ID)
            assert ticket is not None
            assert ticket.used_at is not None
            assert ticket.used_by_user_id == GATE_ID
    finally:
        reset_gate_fixture()


def test_gate_validation_fails_closed_without_a_signing_secret() -> None:
    application = make_gate_app(secret=None)

    with TestClient(application) as client:
        assert client.get("/api/gate/events").status_code == 200
        response = validate(client, EVENT_ID, "not-a-ticket")
        assert response.status_code == 503
