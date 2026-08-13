from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.openapi import (
    API_DESCRIPTION,
    API_VERSION,
    OPENAPI_TAGS,
    SWAGGER_UI_PARAMETERS,
    configure_openapi_session_cookie,
)
from backend.api.router import api_router
from backend.core.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the API with one explicit settings snapshot and credentialed CORS policy."""

    resolved_settings = settings or get_settings()
    application = FastAPI(
        title=resolved_settings.app_name,
        summary="Event publication, ticket reservation, and gate validation API",
        description=API_DESCRIPTION,
        version=API_VERSION,
        openapi_tags=OPENAPI_TAGS,
        swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
    )
    application.state.settings = resolved_settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved_settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=resolved_settings.api_prefix)
    configure_openapi_session_cookie(application, resolved_settings.session_cookie_name)
    return application


app = create_app()
