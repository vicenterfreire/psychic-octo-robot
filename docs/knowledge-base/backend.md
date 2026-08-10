# Backend Knowledge Base

## Current Responsibility

The backend is a FastAPI modular monolith. It owns API behavior and will later own authorization, business rules, Ticketmaster access, persistence, reservation concurrency, payments, and ticket validation.

## Current Structure

- `src/backend/main.py` creates the FastAPI application and installs cross-origin policy.
- `src/backend/api/router.py` is the composition point for HTTP feature routers.
- `src/backend/api/routes/health.py` provides the initial health contract.
- `src/backend/core/settings.py` reads process configuration into an immutable settings object.
- `tests/` contains risk-relevant backend tests as features are introduced.

The application factory keeps construction explicit and allows tests or future entry points to build an application with the same wiring. It is not a generic dependency-injection framework.

## Local HTTP Boundary

All business endpoints will be mounted below `/api`. The initial `GET /api/health` endpoint returns:

```json
{
  "status": "ok",
  "service": "backend"
}
```

Credentialed CORS uses one explicit `FRONTEND_ORIGIN`. A wildcard origin cannot be combined safely with browser credentials and would not match the accepted session-cookie architecture.

## Dependency Workflow

- `pyproject.toml` is the human-maintained project and tool configuration.
- `uv.lock` is the reproducible dependency resolution.
- `requirements.txt` is a generated runtime compatibility export.
- Development commands run through `uv` so tools come from the locked environment.

Database and security libraries are intentionally absent until their corresponding commits introduce and exercise them.

## Quality Boundary

Ruff owns formatting and linting, mypy runs in strict mode, and pytest with branch coverage protects behavior. Coverage is evidence for the tested foundation, not a project-wide target or a substitute for risk-focused tests.
