from typing import Any, cast

from fastapi import FastAPI

API_VERSION = "0.1.0"
OPAQUE_SESSION_SCHEME_NAME = "OpaqueSession"
DEFAULT_SESSION_COOKIE_NAME = "gather_session"

API_DESCRIPTION = """
API for the Elite Dev Challenge event and ticketing platform.

The central flow is **Organizer event publication -> Customer temporary reservation and simulated
payment -> Gate one-time ticket validation**. PostgreSQL is authoritative for inventory,
reservation expiration, issued-ticket state, and admission.

### Authentication in Swagger UI

1. Execute `POST /api/auth/login` with one of the seeded accounts.
2. The response stores an opaque HTTP-only session cookie in the browser.
3. Execute endpoints allowed for that account's role. Swagger UI reuses the cookie automatically.
4. Execute `POST /api/auth/logout` to revoke the server-side session.

The application deliberately does not use JWT authentication. The raw opaque credential is never
returned in a JSON response or stored in PostgreSQL, so it should not be pasted into the
**Authorize** dialog. Public operations do not require a session. Payment is deterministic and
simulated; no financial data is accepted.
"""

OPENAPI_TAGS: list[dict[str, Any]] = [
    {
        "name": "system",
        "description": "Public runtime health information.",
    },
    {
        "name": "authentication",
        "description": "Opaque session login, restoration, and server-side revocation.",
    },
    {
        "name": "catalog",
        "description": "Organizer-only Ticketmaster search normalized by the backend.",
    },
    {
        "name": "events",
        "description": "Public discovery and Organizer-owned event management.",
    },
    {
        "name": "reservations",
        "description": "Customer inventory holds and deterministic simulated payment.",
    },
    {
        "name": "tickets",
        "description": "Private Customer tickets and minimized public bearer presentation.",
    },
    {
        "name": "gate",
        "description": "Gate event selection and atomic one-time ticket validation.",
    },
]

SWAGGER_UI_PARAMETERS: dict[str, Any] = {
    "displayRequestDuration": True,
    "filter": True,
    "tryItOutEnabled": True,
}


def configure_openapi_session_cookie(application: FastAPI, cookie_name: str) -> None:
    """Align the generated cookie security scheme with this application's settings snapshot."""

    schema = application.openapi()
    components = cast(dict[str, Any], schema.setdefault("components", {}))
    security_schemes = cast(dict[str, Any], components.setdefault("securitySchemes", {}))
    opaque_session = security_schemes.get(OPAQUE_SESSION_SCHEME_NAME)
    if not isinstance(opaque_session, dict):
        raise RuntimeError("Opaque session security scheme is missing from the OpenAPI schema.")
    opaque_session["name"] = cookie_name
