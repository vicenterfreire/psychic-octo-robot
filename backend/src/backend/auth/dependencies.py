from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyCookie
from sqlalchemy.orm import Session as DatabaseSession

from backend.api.openapi import DEFAULT_SESSION_COOKIE_NAME, OPAQUE_SESSION_SCHEME_NAME
from backend.auth.authorization import ensure_role
from backend.auth.service import find_user_by_session
from backend.core.dependencies import get_application_settings
from backend.core.settings import Settings
from backend.database.dependencies import get_database_session
from backend.database.models import User, UserRole

Database = Annotated[DatabaseSession, Depends(get_database_session)]
ApplicationSettings = Annotated[Settings, Depends(get_application_settings)]
DocumentedSessionCredential = Annotated[
    str | None,
    Security(
        APIKeyCookie(
            name=DEFAULT_SESSION_COOKIE_NAME,
            scheme_name=OPAQUE_SESSION_SCHEME_NAME,
            description=(
                "Opaque HTTP-only browser session. Execute POST /api/auth/login in this Swagger "
                "UI to create it; the browser sends it automatically afterward."
            ),
            auto_error=False,
        )
    ),
]


def get_current_user(
    request: Request,
    _documented_session: DocumentedSessionCredential,
    database: Database,
    settings: ApplicationSettings,
) -> User:
    """Resolve an active opaque session or stop the request at the authentication boundary."""

    raw_token = request.cookies.get(settings.session_cookie_name)
    user = find_user_by_session(database, raw_token) if raw_token else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"Cache-Control": "no-store"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole) -> Callable[[CurrentUser], User]:
    """Create a FastAPI dependency that authorizes any one of the supplied roles."""

    def dependency(current_user: CurrentUser) -> User:
        ensure_role(current_user, *allowed_roles)
        return current_user

    return dependency
