# Backend Knowledge Base

## Current Responsibility

The backend is a FastAPI modular monolith. It owns API behavior, authentication, authorization, Ticketmaster access, and persistence, and will later own reservation concurrency, payments, and ticket validation.

## Current Structure

- `src/backend/main.py` creates the FastAPI application and installs cross-origin policy.
- `src/backend/api/router.py` is the composition point for HTTP feature routers.
- `src/backend/api/routes/health.py` provides the initial health contract.
- `src/backend/auth/` owns password verification, opaque-session lifecycle, authentication routes, and reusable authorization checks.
- `src/backend/catalog/` owns Ticketmaster transport, response validation, normalization, and organizer-only search.
- `src/backend/events/` owns organizer-scoped event commands, responses, lifecycle rules, and persistence transactions.
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

`httpx` is the synchronous Ticketmaster transport. It is a runtime dependency because the application, not only its tests, performs the provider request. The mock transport used by tests exercises the same request and parsing code without consuming a real quota.

## Authentication and Authorization Boundary

`POST /api/auth/login` normalizes the email and returns the same `401` response for an unknown identity or a wrong password. Unknown identities still run a dummy Argon2id verification to reduce timing differences. A successful login creates 32 random bytes, sends their URL-safe representation only in the cookie, and persists the 32-byte SHA-256 digest.

`GET /api/auth/me` resolves the cookie digest against an unrevoked, unexpired database session using PostgreSQL time. `POST /api/auth/logout` revokes the matching row immediately and expires the browser cookie. Sessions have a fixed seven-day lifetime and are not renewed during requests.

The cookie is HTTP-only, `SameSite=Lax`, scoped to `/`, and conditionally `Secure`; authentication responses are marked `Cache-Control: no-store`. SHA-256 is appropriate here because the input is a high-entropy random credential. It is not used for passwords, which require the deliberately expensive Argon2id function.

Backend dependencies provide the authoritative current user and role checks. The ownership helper compares a resource owner identifier to that user. Actual event, reservation, and ticket routes must invoke these checks when those resources are implemented; frontend route guards alone never authorize a request.

## External Catalog Boundary

`GET /api/catalog/events?q=...` requires an Organizer session. The backend sends `apikey`, the normalized keyword, `source=ticketmaster`, `locale=*`, a relevance sort, and a fixed limit of 12 to the official [Discovery API v2 event search](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/).

The search response is validated and reduced to provider name, provider event identifier, name, description, one safe public image URL, and the public source URL. Dates, venues, arbitrary embedded data, rate-limit metadata, and credentials do not cross the browser boundary. Local date, venue, capacity, and price remain organizer-owned event fields.

Event creation does not trust the selected card as a snapshot source. It sends only its external identifier and local form data, fetches the detail through the server-side client, rejects a mismatched response identifier, and persists both normalized source fields and the provider JSON. Existing events never resynchronize automatically.

Requests have a configurable five-second default timeout. Missing/rejected credentials and exhausted quota map to `503`, timeouts to `504`, and transport or invalid-response failures to `502`. Upstream bodies and exception URLs are never returned because either may contain provider details or the query-string credential.

Search is explicit rather than keystroke-driven and has no automatic retry. This protects the provider's finite quota and avoids duplicate calls during outages. A new synchronous client is opened per search; connection pooling, caching, and retry policy remain unnecessary at the current challenge scale.

## Organizer Event Boundary

`GET /api/events/organizer` scopes the collection by the authenticated Organizer. Creation produces a draft; full replacement updates local editable fields; publication is a separate idempotent state transition. Updates and publication select the event by both identifier and owner and lock that row, so a foreign identifier is indistinguishable from an unknown one.

Dates must carry a timezone and remain in the future. Capacity and price have bounded API validation in addition to database constraints. Before a capacity reduction, the service sums approved reservations and unexpired pending holds using PostgreSQL time. The new capacity must cover that committed quantity. This rule is already future-compatible with the reservation transaction, which will acquire the same event-row lock before allocating inventory.

## Published Discovery Boundary

`GET /api/events` and `GET /api/events/{id}` are public because discovery itself is not an authorization boundary. Both query only local events with `published` status and a start later than PostgreSQL's current time. They do not call Ticketmaster and return a minimized contract without organizer identity, lifecycle status, provider links, or raw snapshots.

The optional `q` parameter is trimmed and matched case-insensitively against event name, venue, and city. SQLAlchemy's auto-escaped containment treats `%` and `_` as user text rather than SQL wildcard controls. Results are ordered by start time and bounded to 50 while pagination remains deferred.

A correlated aggregate calculates committed quantity for each event from approved reservations and pending reservations whose expiry is still in the future according to PostgreSQL. `available_quantity` is clamped at zero for defensive presentation. This read does not lock inventory: it is a useful snapshot, while the reservation command will recalculate under an event-row lock before creating a hold.

## Persistence Boundary

The schema contains users, opaque-session records, immutable catalog snapshots, organizer-owned events, temporary reservations, and one ticket row per issued admission. PostgreSQL constraints protect local invariants such as normalized emails, valid roles and statuses, positive capacity and quantities, fixed-length session digests, unique ticket positions, and coherent usage timestamps.

Enums are stored as strings with explicit named `CHECK` constraints. This keeps migrations easy to review and makes adding a state a normal versioned constraint change instead of a PostgreSQL enum-type operation.

Money uses integer minor units and timestamps include timezone information. The application supplies UUID identifiers; PostgreSQL remains authoritative for creation timestamps and later reservation-expiration decisions.

The local Podman hook writes an ignored `backend/.env.podman` only when it resolves a usable database address. A user-defined process `DATABASE_URL` or `backend/.env` takes precedence.

## Quality Boundary

Ruff owns formatting and linting, mypy runs in strict mode, and pytest with branch coverage protects behavior. Coverage is evidence for the tested foundation, not a project-wide target or a substitute for risk-focused tests. The root test-report hook also writes a JUnit XML result for automated inspection.
