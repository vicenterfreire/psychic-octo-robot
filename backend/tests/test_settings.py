import pytest

from backend.core.settings import get_settings


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://"])
def test_generic_postgresql_urls_select_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    scheme: str,
) -> None:
    # Arrange
    monkeypatch.setenv("DATABASE_URL", f"{scheme}user:password@database:5432/application")
    get_settings.cache_clear()

    try:
        # Act
        settings = get_settings()

        # Assert
        assert settings.database_url == (
            "postgresql+psycopg://user:password@database:5432/application"
        )
    finally:
        get_settings.cache_clear()


def test_explicit_database_driver_is_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    database_url = "postgresql+psycopg://user:password@database:5432/application"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    try:
        # Act
        settings = get_settings()

        # Assert
        assert settings.database_url == database_url
    finally:
        get_settings.cache_clear()
