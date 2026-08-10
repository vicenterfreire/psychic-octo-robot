# Backend Knowledge Base

## Current Responsibility

The backend is a FastAPI modular monolith. It owns API behavior, authentication, authorization, and persistence, and will later own Ticketmaster access, reservation concurrency, payments, and ticket validation.

## Current Structure

- `src/backend/main.py` creates the FastAPI application and installs cross-origin policy.
- `src/backend/api/router.py` is the composition point for HTTP feature routers.
- `src/backend/api/routes/health.py` provides the initial health contract.
- `src/backend/auth/` owns password verification, opaque-session lifecycle, authentication routes, and reusable authorization checks.
- `src/backend/core/settings.py` reads process configuration into an immutable settings object.
- `src/backend/database/dependencies.py` supplies one synchronous SQLAlchemy session per request.
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

SQLAlchemy 2 maps persistence, Psycopg 3 connects to PostgreSQL, Alembic owns schema changes, and `pwdlib` creates and verifies the accepted Argon2id hashes. `PasswordHash.recommended()` currently resolves to Argon2id version 19 with `m=65536,t=3,p=4`; the encoded hashes remain self-describing. Database-backed FastAPI routes remain synchronous so FastAPI can run blocking database and password work in its thread pool.

## Authentication and Authorization Boundary

`POST /api/auth/login` normalizes the email and returns the same `401` response for an unknown identity or a wrong password. Unknown identities still run a dummy Argon2id verification to reduce timing differences. A successful login creates 32 random bytes, sends their URL-safe representation only in the cookie, and persists the 32-byte SHA-256 digest.

`GET /api/auth/me` resolves the cookie digest against an unrevoked, unexpired database session using PostgreSQL time. `POST /api/auth/logout` revokes the matching row immediately and expires the browser cookie. Sessions have a fixed seven-day lifetime and are not renewed during requests.

The cookie is HTTP-only, `SameSite=Lax`, scoped to `/`, and conditionally `Secure`; authentication responses are marked `Cache-Control: no-store`. SHA-256 is appropriate here because the input is a high-entropy random credential. It is not used for passwords, which require the deliberately expensive Argon2id function.

Backend dependencies provide the authoritative current user and role checks. The ownership helper compares a resource owner identifier to that user. Actual event, reservation, and ticket routes must invoke these checks when those resources are implemented; frontend route guards alone never authorize a request.

## Persistence Boundary

The schema contains users, opaque-session records, immutable catalog snapshots, organizer-owned events, temporary reservations, and one ticket row per issued admission. PostgreSQL constraints protect local invariants such as normalized emails, valid roles and statuses, positive capacity and quantities, fixed-length session digests, unique ticket positions, and coherent usage timestamps.

Enums are stored as strings with explicit named `CHECK` constraints. This keeps migrations easy to review and makes adding a state a normal versioned constraint change instead of a PostgreSQL enum-type operation.

Money uses integer minor units and timestamps include timezone information. The application supplies UUID identifiers; PostgreSQL remains authoritative for creation timestamps and later reservation-expiration decisions.

The local Podman hook writes an ignored `backend/.env.podman` only when it resolves a usable database address. A user-defined process `DATABASE_URL` or `backend/.env` takes precedence.

## Quality Boundary

Ruff owns formatting and linting, mypy runs in strict mode, and pytest with branch coverage protects behavior. Coverage is evidence for the tested foundation, not a project-wide target or a substitute for risk-focused tests. The root test-report hook also writes a JUnit XML result for automated inspection.
