import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "Elite Dev Challenge API"
    environment: str = "development"
    api_prefix: str = "/api"
    frontend_origin: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://elite:elite@localhost:5432/elite_dev"


@lru_cache
def get_settings() -> Settings:
    load_dotenv(BACKEND_ROOT / ".env", override=False)
    load_dotenv(BACKEND_ROOT / ".env.podman", override=False)

    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://elite:elite@localhost:5432/elite_dev",
        ),
    )
