from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "backend"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API health",
    description="Public liveness endpoint used by local processes and container health checks.",
)
def get_health() -> HealthResponse:
    return HealthResponse()
