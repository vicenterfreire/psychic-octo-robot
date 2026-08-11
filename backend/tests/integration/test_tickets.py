from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.core.settings import Settings
from backend.database.engine import get_engine
from backend.database.models import Reservation, ReservationStatus, Ticket, User, UserRole
from backend.database.seed import CUSTOMER_ONE_ID, CUSTOMER_TWO_ID, EVENT_ID
from backend.main import create_app
from backend.tickets.signing import TicketSigner

pytestmark = pytest.mark.integration

RESERVATION_ID = UUID("66666666-6666-4666-8666-666666666660")
TICKET_ONE_ID = UUID("77777777-7777-4777-8777-777777777771")
TICKET_TWO_ID = UUID("77777777-7777-4777-8777-777777777772")
TEST_SECRET = "ticket-signing-integration-secret-32-bytes"


def make_user(user_id: UUID = CUSTOMER_ONE_ID, role: UserRole = UserRole.CUSTOMER) -> User:
    return User(
        id=user_id,
        email=f"{role.value}.{user_id}@example.com",
        password_hash="not-used-in-ticket-tests",
        role=role,
    )


def make_ticket_app(user: User | None = None, secret: str | None = TEST_SECRET) -> FastAPI:
    application = create_app(
        Settings(
            frontend_origin="http://frontend.test",
            ticket_hmac_secret=secret,
        )
    )
    resolved_user = user or make_user()
    application.dependency_overrides[get_current_user] = lambda: resolved_user
    return application


def reset_ticket_fixture() -> None:
    with Session(get_engine()) as database, database.begin():
        database.execute(delete(Ticket).where(Ticket.id.in_([TICKET_ONE_ID, TICKET_TWO_ID])))
        database.execute(delete(Reservation).where(Reservation.id == RESERVATION_ID))


def add_issued_tickets() -> None:
    reset_ticket_fixture()
    now = datetime.now(UTC)
    with Session(get_engine()) as database, database.begin():
        database.add(
            Reservation(
                id=RESERVATION_ID,
                customer_id=CUSTOMER_ONE_ID,
                event_id=EVENT_ID,
                quantity=2,
                status=ReservationStatus.APPROVED,
                created_at=now,
                expires_at=now + timedelta(minutes=10),
            )
        )
        database.add_all(
            [
                Ticket(
                    id=TICKET_ONE_ID,
                    reservation_id=RESERVATION_ID,
                    ticket_number=1,
                    issued_at=now,
                ),
                Ticket(
                    id=TICKET_TWO_ID,
                    reservation_id=RESERVATION_ID,
                    ticket_number=2,
                    issued_at=now,
                    revoked_at=now,
                ),
            ]
        )


def test_customer_lists_signed_tickets_and_bearer_view_is_minimized() -> None:
    add_issued_tickets()
    application = make_ticket_app()
    signer = TicketSigner(TEST_SECRET)

    try:
        with TestClient(application) as client:
            response = client.get("/api/tickets")
            assert response.status_code == 200
            assert response.headers["cache-control"] == "no-store"
            items = response.json()["items"]
            assert [item["ticket_number"] for item in items] == [1, 2]
            assert all(item["event"]["name"] == "Aurora Live 2030" for item in items)
            assert all(item["is_used"] is False for item in items)
            assert [item["is_revoked"] for item in items] == [False, True]

            token = items[0]["token"]
            assert signer.verify(token) == TICKET_ONE_ID
            assert "customer.one@example.com" not in token
            assert items[0]["share_url"] == f"http://frontend.test/tickets/share/{token}"

            shared_response = client.get(f"/api/tickets/shared/{token}")
            assert shared_response.status_code == 200
            assert shared_response.headers["cache-control"] == "no-store"
            shared = shared_response.json()
            assert shared["ticket_number"] == 1
            assert shared["is_revoked"] is False
            assert shared["event"]["name"] == "Aurora Live 2030"
            assert "id" not in shared
            assert "token" not in shared
            assert "share_url" not in shared
            assert "customer_id" not in shared
            assert "reservation_id" not in shared

            revoked_token = items[1]["token"]
            revoked_shared = client.get(f"/api/tickets/shared/{revoked_token}").json()
            assert revoked_shared["is_revoked"] is True

            version, identifier, signature = token.split(".")
            changed_signature = signature[:-1] + ("A" if signature[-1] != "A" else "B")
            invalid_tokens = [
                f"v2.{identifier}.{signature}",
                f"{version}.{'0' * 32}.{signature}",
                f"{version}.{identifier}.{changed_signature}",
                signer.sign(uuid4()),
            ]
            for invalid_token in invalid_tokens:
                assert client.get(f"/api/tickets/shared/{invalid_token}").status_code == 404

            application.dependency_overrides[get_current_user] = lambda: make_user(CUSTOMER_TWO_ID)
            assert client.get("/api/tickets").json() == {"items": []}

            application.dependency_overrides[get_current_user] = lambda: make_user(
                role=UserRole.GATE
            )
            assert client.get("/api/tickets").status_code == 403
    finally:
        reset_ticket_fixture()


def test_ticket_endpoints_fail_closed_without_a_valid_signing_secret() -> None:
    add_issued_tickets()
    application = make_ticket_app(secret=None)

    try:
        with TestClient(application) as client:
            assert client.get("/api/tickets").status_code == 503
            assert client.get("/api/tickets/shared/not-a-ticket").status_code == 503
    finally:
        reset_ticket_fixture()
