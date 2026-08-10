from datetime import datetime, timedelta
from typing import cast

from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DatabaseSession
from sqlalchemy.sql import func

from backend.auth.service import digest_session_token
from backend.core.settings import Settings
from backend.database.engine import get_engine
from backend.database.models import Session as SessionRecord
from backend.database.seed import CUSTOMER_ONE_ID
from backend.main import create_app

TEST_SETTINGS = Settings(frontend_origin="http://frontend.test")


def remove_session(raw_token: str) -> None:
    with DatabaseSession(get_engine()) as database:
        database.execute(
            delete(SessionRecord).where(
                SessionRecord.token_digest == digest_session_token(raw_token)
            )
        )
        database.commit()


def test_login_persists_only_a_digest_and_restores_the_session() -> None:
    client = TestClient(create_app(TEST_SETTINGS))
    login_response = client.post(
        "/api/auth/login",
        json={"email": "organizer@example.com", "password": "Organizer123!"},
    )

    assert login_response.status_code == 200
    assert login_response.json() == {
        "id": "11111111-1111-4111-8111-111111111111",
        "email": "organizer@example.com",
        "role": "organizer",
    }
    assert login_response.headers["cache-control"] == "no-store"

    set_cookie = login_response.headers["set-cookie"]
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert f"Max-Age={TEST_SETTINGS.session_lifetime_seconds}" in set_cookie
    assert "Secure" not in set_cookie

    raw_token = client.cookies.get(TEST_SETTINGS.session_cookie_name)
    assert raw_token is not None
    assert raw_token not in login_response.text

    try:
        with DatabaseSession(get_engine()) as database:
            session_record = database.scalar(
                select(SessionRecord).where(
                    SessionRecord.token_digest == digest_session_token(raw_token)
                )
            )

        assert session_record is not None
        assert session_record.token_digest == digest_session_token(raw_token)
        assert session_record.expires_at - session_record.created_at == timedelta(days=7)

        reopened_client = TestClient(create_app(TEST_SETTINGS))
        reopened_client.cookies.set(TEST_SETTINGS.session_cookie_name, raw_token)
        current_user_response = reopened_client.get("/api/auth/me")

        assert current_user_response.status_code == 200
        assert current_user_response.json()["role"] == "organizer"
    finally:
        remove_session(raw_token)


def test_invalid_credentials_return_the_same_error() -> None:
    client = TestClient(create_app(TEST_SETTINGS))

    unknown_user = client.post(
        "/api/auth/login",
        json={"email": "unknown@example.com", "password": "Wrong123!"},
    )
    wrong_password = client.post(
        "/api/auth/login",
        json={"email": "organizer@example.com", "password": "Wrong123!"},
    )

    assert unknown_user.status_code == 401
    assert wrong_password.status_code == 401
    assert unknown_user.json() == wrong_password.json() == {"detail": "Invalid email or password."}
    assert unknown_user.headers["cache-control"] == "no-store"
    assert wrong_password.headers["cache-control"] == "no-store"
    assert TEST_SETTINGS.session_cookie_name not in client.cookies


def test_logout_revokes_the_server_session() -> None:
    client = TestClient(create_app(TEST_SETTINGS))
    login_response = client.post(
        "/api/auth/login",
        json={"email": "customer.one@example.com", "password": "Customer123!"},
    )
    assert login_response.status_code == 200
    raw_token = client.cookies.get(TEST_SETTINGS.session_cookie_name)
    assert raw_token is not None

    try:
        logout_response = client.post("/api/auth/logout")

        assert logout_response.status_code == 204
        assert logout_response.content == b""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"

        with DatabaseSession(get_engine()) as database:
            revoked_at = database.scalar(
                select(SessionRecord.revoked_at).where(
                    SessionRecord.token_digest == digest_session_token(raw_token)
                )
            )
        assert revoked_at is not None
    finally:
        remove_session(raw_token)


def test_expired_session_is_rejected() -> None:
    raw_token = "expired-test-session-token"
    with DatabaseSession(get_engine()) as database:
        database_now = cast(datetime | None, database.scalar(select(func.now())))
        assert database_now is not None
        database.add(
            SessionRecord(
                user_id=CUSTOMER_ONE_ID,
                token_digest=digest_session_token(raw_token),
                created_at=database_now - timedelta(days=8),
                expires_at=database_now - timedelta(days=1),
            )
        )
        database.commit()

    try:
        client = TestClient(create_app(TEST_SETTINGS))
        client.cookies.set(TEST_SETTINGS.session_cookie_name, raw_token)

        assert client.get("/api/auth/me").status_code == 401
    finally:
        remove_session(raw_token)


def test_production_cookie_is_secure() -> None:
    settings = Settings(
        frontend_origin="https://frontend.test",
        environment="production",
        session_cookie_secure=True,
    )
    client = TestClient(create_app(settings), base_url="https://api.test")
    response = client.post(
        "/api/auth/login",
        json={"email": "gate@example.com", "password": "Gate123!"},
    )
    assert response.status_code == 200
    raw_token = client.cookies.get(settings.session_cookie_name)
    assert raw_token is not None

    try:
        assert "Secure" in response.headers["set-cookie"]
    finally:
        remove_session(raw_token)
