from typing import Any

from fastapi.testclient import TestClient

from backend.api.openapi import OPAQUE_SESSION_SCHEME_NAME, OPENAPI_TAGS
from backend.core.settings import Settings
from backend.main import create_app

HTTP_METHODS = {"delete", "get", "head", "options", "patch", "post", "put", "trace"}


def test_swagger_ui_exposes_the_generated_openapi_document() -> None:
    application = create_app(Settings())

    with TestClient(application) as client:
        response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text
    assert "url: '/openapi.json'" in response.text
    assert '"displayRequestDuration": true' in response.text
    assert '"tryItOutEnabled": true' in response.text


def test_openapi_documents_domain_operations_and_opaque_cookie_security() -> None:
    cookie_name = "documented_test_session"
    application = create_app(Settings(session_cookie_name=cookie_name))

    schema = application.openapi()
    operations = _operations(schema)

    assert schema["info"]["title"] == "Elite Dev Challenge API"
    assert schema["info"]["summary"] == (
        "Event publication, ticket reservation, and gate validation API"
    )
    assert schema["info"]["version"] == "0.1.0"
    assert "does not use JWT authentication" in schema["info"]["description"]
    assert schema["tags"] == OPENAPI_TAGS
    assert all(operation.get("summary") for operation in operations)
    assert all(operation.get("description") for operation in operations)

    security_scheme = schema["components"]["securitySchemes"][OPAQUE_SESSION_SCHEME_NAME]
    assert security_scheme["type"] == "apiKey"
    assert security_scheme["in"] == "cookie"
    assert security_scheme["name"] == cookie_name
    assert schema["paths"]["/api/auth/me"]["get"]["security"] == [{OPAQUE_SESSION_SCHEME_NAME: []}]
    assert schema["paths"]["/api/reservations"]["post"]["security"] == [
        {OPAQUE_SESSION_SCHEME_NAME: []}
    ]
    assert "security" not in schema["paths"]["/api/auth/login"]["post"]
    assert "security" not in schema["paths"]["/api/events"]["get"]
    assert "security" not in schema["paths"]["/api/tickets/shared/{token}"]["get"]

    login_properties = schema["components"]["schemas"]["LoginRequest"]["properties"]
    assert login_properties["email"]["examples"] == ["organizer@example.com"]
    assert "Plaintext password" in login_properties["password"]["description"]


def _operations(schema: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        operation
        for path_item in schema["paths"].values()
        for method, operation in path_item.items()
        if method in HTTP_METHODS
    ]
