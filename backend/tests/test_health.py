from fastapi.testclient import TestClient

from backend.core.settings import Settings
from backend.main import create_app


def test_health_endpoint_reports_service_status() -> None:
    settings = Settings(frontend_origin="http://frontend.test")

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/health", headers={"Origin": settings.frontend_origin})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "backend"}
    assert response.headers["access-control-allow-origin"] == settings.frontend_origin
    assert response.headers["access-control-allow-credentials"] == "true"
