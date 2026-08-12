from typing import cast

from fastapi import Request

from backend.core.settings import Settings


def get_application_settings(request: Request) -> Settings:
    """Read the immutable settings snapshot installed by the application factory."""

    return cast(Settings, request.app.state.settings)
