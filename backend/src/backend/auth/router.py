from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session as DatabaseSession

from backend.auth.dependencies import CurrentUser
from backend.auth.schemas import CurrentUserResponse, LoginRequest
from backend.auth.service import authenticate_user, issue_session, revoke_session
from backend.core.dependencies import get_application_settings
from backend.core.settings import Settings
from backend.database.dependencies import get_database_session

router = APIRouter(prefix="/auth", tags=["authentication"])

Database = Annotated[DatabaseSession, Depends(get_database_session)]
ApplicationSettings = Annotated[Settings, Depends(get_application_settings)]


@router.post("/login", response_model=CurrentUserResponse)
def login(
    credentials: LoginRequest,
    response: Response,
    database: Database,
    settings: ApplicationSettings,
) -> CurrentUserResponse:
    user = authenticate_user(database, credentials.email, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"Cache-Control": "no-store"},
        )

    issued_session = issue_session(database, user, settings.session_lifetime_seconds)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=issued_session.raw_token,
        max_age=settings.session_lifetime_seconds,
        expires=issued_session.expires_at,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
    return CurrentUserResponse.model_validate(user)


@router.get("/me", response_model=CurrentUserResponse)
def get_session_user(response: Response, current_user: CurrentUser) -> CurrentUserResponse:
    response.headers["Cache-Control"] = "no-store"
    return CurrentUserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    database: Database,
    settings: ApplicationSettings,
) -> None:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if raw_token:
        revoke_session(database, raw_token)

    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
