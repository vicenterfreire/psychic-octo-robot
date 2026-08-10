from fastapi import APIRouter

from backend.api.routes.health import router as health_router
from backend.auth.router import router as auth_router
from backend.catalog.router import router as catalog_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(catalog_router)
