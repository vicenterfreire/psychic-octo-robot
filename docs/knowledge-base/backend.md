# Backend Knowledge Base

## Current Responsibility

The backend is a FastAPI modular monolith. It owns API behavior and will later own authorization, business rules, Ticketmaster access, persistence, reservation concurrency, payments, and ticket validation.

## Current Structure

- `src/backend/main.py` creates the FastAPI application and installs cross-origin policy.
- `src/backend/api/router.py` is the composition point for HTTP feature routers.
- `src/backend/api/routes/health.py` provides the initial health contract.
- `src/backend/core/settings.py` reads process configuration into an immutable settings object.
- `src/backend/database/models.py` defines the complete relational mapping and database constraints.
- `src/backend/database/engine.py` creates the synchronous SQLAlchemy engine.
- `src/backend/database/seed.py` inserts stable, idempotent evaluation data.
- `migrations/` contains the Alembic schema history.
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

SQLAlchemy 2 maps persistence, Psycopg 3 connects to PostgreSQL, Alembic owns schema changes, and `pwdlib` creates the accepted Argon2id seed hashes. Database-backed FastAPI routes will remain synchronous so FastAPI can run blocking work in its thread pool.

## Persistence Boundary

The schema contains users, opaque-session records, immutable catalog snapshots, organizer-owned events, temporary reservations, and one ticket row per issued admission. PostgreSQL constraints protect local invariants such as normalized emails, valid roles and statuses, positive capacity and quantities, fixed-length session digests, unique ticket positions, and coherent usage timestamps.

Enums are stored as strings with explicit named `CHECK` constraints. This keeps migrations easy to review and makes adding a state a normal versioned constraint change instead of a PostgreSQL enum-type operation.

Money uses integer minor units and timestamps include timezone information. The application supplies UUID identifiers; PostgreSQL remains authoritative for creation timestamps and later reservation-expiration decisions.

The local Podman hook writes an ignored `backend/.env.podman` only when it resolves a usable database address. A user-defined process `DATABASE_URL` or `backend/.env` takes precedence.

## Quality Boundary

Ruff owns formatting and linting, mypy runs in strict mode, and pytest with branch coverage protects behavior. Coverage is evidence for the tested foundation, not a project-wide target or a substitute for risk-focused tests.
