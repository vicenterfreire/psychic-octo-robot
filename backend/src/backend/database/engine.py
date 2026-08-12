from functools import lru_cache

from sqlalchemy import Engine, create_engine

from backend.core.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return the process-wide engine for the cached database URL.

    Pool pre-ping recovers stale pooled connections; changing ``DATABASE_URL`` requires a process
    restart or explicit cache cleanup in tests.
    """

    return create_engine(get_settings().database_url, pool_pre_ping=True)
