import argparse
import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, make_url

ALLOWED_DATABASES = {"elite_dev_test", "elite_dev_e2e"}


def parse_action() -> str:
    parser = argparse.ArgumentParser(
        description="Reset or drop a project-owned isolated PostgreSQL test database."
    )
    parser.add_argument("action", choices=("reset", "drop"))
    return parser.parse_args().action


def isolated_database_url() -> tuple[str, str]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required.")

    parsed_url = make_url(database_url)
    database_name = parsed_url.database
    if database_name not in ALLOWED_DATABASES:
        allowed = ", ".join(sorted(ALLOWED_DATABASES))
        raise RuntimeError(f"Refusing to manage {database_name!r}; allowed databases: {allowed}.")

    return parsed_url.set(database="postgres").render_as_string(hide_password=False), database_name


def terminate_connections(connection: Connection, database_name: str) -> None:
    connection.execute(
        text(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = :database_name
              AND pid <> pg_backend_pid()
            """
        ),
        {"database_name": database_name},
    )


def manage_database(action: str) -> None:
    admin_url, database_name = isolated_database_url()
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        with engine.connect() as connection:
            terminate_connections(connection, database_name)
            connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{database_name}"')
            if action == "reset":
                connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
    finally:
        engine.dispose()

    verb = "reset" if action == "reset" else "dropped"
    print(f"Isolated database {database_name} {verb}.")


if __name__ == "__main__":
    manage_database(parse_action())
