import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[3]


def normalize_database_url(database_url: str) -> str:
    """Select Psycopg 3 when a provider supplies a generic PostgreSQL URL scheme."""

    for generic_scheme in ("postgres://", "postgresql://"):
        if database_url.startswith(generic_scheme):
            return database_url.replace(generic_scheme, "postgresql+psycopg://", 1)
    return database_url


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable process configuration shared through the FastAPI application state."""

    app_name: str = "Elite Dev Challenge API"
    environment: str = "development"
    api_prefix: str = "/api"
    frontend_origin: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://elite:elite@localhost:5432/elite_dev"
    session_cookie_name: str = "gather_session"
    session_lifetime_seconds: int = 7 * 24 * 60 * 60
    session_cookie_secure: bool = False
    reservation_lifetime_seconds: int = 10 * 60
    ticket_hmac_secret: str | None = None
    ticketmaster_api_key: str | None = None
    ticketmaster_timeout_seconds: float = 5.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process settings snapshot with environment variables taking precedence.

    The zero-argument cache deliberately creates one instance per process. Restart the process, or
    clear this cache in a test, after changing configuration values.
    """

    load_dotenv(BACKEND_ROOT / ".env", override=False)
    load_dotenv(BACKEND_ROOT / ".env.compose", override=False)

    environment = os.getenv("APP_ENV", "development")
    secure_cookie_default = environment != "development"

    return Settings(
        environment=environment,
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
        database_url=normalize_database_url(
            os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg://elite:elite@localhost:5432/elite_dev",
            )
        ),
        session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "gather_session"),
        session_lifetime_seconds=int(os.getenv("SESSION_LIFETIME_SECONDS", str(7 * 24 * 60 * 60))),
        session_cookie_secure=os.getenv("SESSION_COOKIE_SECURE", str(secure_cookie_default)).lower()
        == "true",
        reservation_lifetime_seconds=int(os.getenv("RESERVATION_LIFETIME_SECONDS", "600")),
        ticket_hmac_secret=os.getenv("TICKET_HMAC_SECRET") or None,
        ticketmaster_api_key=os.getenv("TICKETMASTER_API_KEY") or None,
        ticketmaster_timeout_seconds=float(os.getenv("TICKETMASTER_TIMEOUT_SECONDS", "5")),
    )
