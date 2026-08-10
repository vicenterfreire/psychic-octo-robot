from uuid import UUID

import pytest
from fastapi import HTTPException

from backend.auth.authorization import ensure_owner, ensure_role
from backend.database.models import User, UserRole

ORGANIZER_ID = UUID("11111111-1111-4111-8111-111111111111")
ANOTHER_USER_ID = UUID("22222222-2222-4222-8222-222222222222")


def make_user(role: UserRole = UserRole.ORGANIZER) -> User:
    return User(
        id=ORGANIZER_ID,
        email="organizer@example.com",
        password_hash="not-used-in-authorization-tests",
        role=role,
    )


def test_role_authorization_allows_only_the_expected_role() -> None:
    organizer = make_user()

    ensure_role(organizer, UserRole.ORGANIZER)
    with pytest.raises(HTTPException) as denied:
        ensure_role(organizer, UserRole.CUSTOMER, UserRole.GATE)

    assert denied.value.status_code == 403


def test_ownership_authorization_rejects_another_user() -> None:
    organizer = make_user()

    ensure_owner(organizer, ORGANIZER_ID)
    with pytest.raises(HTTPException) as denied:
        ensure_owner(organizer, ANOTHER_USER_ID)

    assert denied.value.status_code == 403
