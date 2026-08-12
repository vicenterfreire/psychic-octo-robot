from collections.abc import Iterator

from sqlalchemy.orm import Session

from backend.database.engine import get_engine


def get_database_session() -> Iterator[Session]:
    """Yield one request-scoped session while feature services own transaction commits."""

    with Session(get_engine()) as database:
        yield database
