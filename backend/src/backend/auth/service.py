import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import cast

from sqlalchemy import select, update
from sqlalchemy.orm import Session as DatabaseSession
from sqlalchemy.sql import func

from backend.auth.passwords import DUMMY_PASSWORD_HASH, verify_password
from backend.database.models import Session as SessionRecord
from backend.database.models import User

SESSION_TOKEN_BYTES = 32


@dataclass(frozen=True, slots=True)
class IssuedSession:
    """Raw browser credential and its fixed database-authoritative expiration time."""

    raw_token: str
    expires_at: datetime


def digest_session_token(raw_token: str) -> bytes:
    """Digest a high-entropy session credential before persistence.

    SHA-256 is suitable because session tokens are random; passwords use Argon2id instead.
    """

    return hashlib.sha256(raw_token.encode("utf-8")).digest()


def authenticate_user(
    database: DatabaseSession,
    email: str,
    password: str,
) -> User | None:
    """Verify normalized credentials while equalizing unknown-user password work."""

    user = database.scalar(select(User).where(User.email == email.strip().lower()))
    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_matches = verify_password(password, password_hash)

    if user is None or not password_matches:
        return None

    return user


def issue_session(
    database: DatabaseSession,
    user: User,
    lifetime_seconds: int,
) -> IssuedSession:
    """Create and commit a fixed-lifetime opaque session using PostgreSQL time.

    Only the token digest is persisted. The raw credential is returned once for the HTTP-only
    cookie and must not be logged or stored elsewhere.
    """

    database_now = cast(datetime | None, database.scalar(select(func.now())))
    if database_now is None:
        raise RuntimeError("The database did not return its current time.")

    raw_token = secrets.token_urlsafe(SESSION_TOKEN_BYTES)
    expires_at = database_now + timedelta(seconds=lifetime_seconds)
    database.add(
        SessionRecord(
            user_id=user.id,
            token_digest=digest_session_token(raw_token),
            created_at=database_now,
            expires_at=expires_at,
        )
    )
    database.commit()
    return IssuedSession(raw_token=raw_token, expires_at=expires_at)


def find_user_by_session(database: DatabaseSession, raw_token: str) -> User | None:
    """Resolve only an unrevoked session whose deadline is after PostgreSQL current time."""

    return database.scalar(
        select(User)
        .join(SessionRecord, SessionRecord.user_id == User.id)
        .where(
            SessionRecord.token_digest == digest_session_token(raw_token),
            SessionRecord.revoked_at.is_(None),
            SessionRecord.expires_at > func.now(),
        )
    )


def revoke_session(database: DatabaseSession, raw_token: str) -> None:
    """Idempotently revoke the matching server-side session using PostgreSQL time."""

    database.execute(
        update(SessionRecord)
        .where(
            SessionRecord.token_digest == digest_session_token(raw_token),
            SessionRecord.revoked_at.is_(None),
        )
        .values(revoked_at=func.now())
    )
    database.commit()
