# Backend Knowledge Base

## Current Responsibility

The backend is a FastAPI modular monolith. It owns API behavior, authentication, authorization, Ticketmaster access, persistence, reservation concurrency, simulated checkout, ticket authenticity/presentation state, and authoritative Gate validation.

## Current Structure

- `src/backend/main.py` creates the FastAPI application and installs cross-origin policy.
- `src/backend/api/router.py` is the composition point for HTTP feature routers.
- `src/backend/api/routes/health.py` provides the initial health contract.
- `src/backend/auth/` owns password verification, opaque-session lifecycle, authentication routes, and reusable authorization checks.
- `src/backend/catalog/` owns Ticketmaster transport, response validation, normalization, and organizer-only search.
- `src/backend/events/` owns organizer-scoped event commands, responses, lifecycle rules, and persistence transactions.
- `src/backend/gate/` owns Gate event selection, validation outcomes, and one-time ticket consumption.
- `src/backend/reservations/` owns Customer-scoped holds, database deadlines, inventory locking, lazy expiration, payment simulation, and ticket-row issuance.
- `src/backend/tickets/` owns signing configuration, token verification, Customer ticket reads, and minimized bearer sharing responses.
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

Backend dependencies provide the authoritative current user and role checks. Event, reservation, and private ticket queries include the authenticated owner where required. Frontend route guards alone never authorize a request.

## External Catalog Boundary

`GET /api/catalog/events?q=...` requires an Organizer session. The backend sends `apikey`, the normalized keyword, `source=ticketmaster`, `locale=*`, a relevance sort, and a fixed limit of 12 to the official [Discovery API v2 event search](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/).

The search response is validated and reduced to provider name, provider event identifier, name, description, one safe public image URL, and the public source URL. Dates, venues, arbitrary embedded data, rate-limit metadata, and credentials do not cross the browser boundary. Local date, venue, capacity, and price remain organizer-owned event fields.

Event creation does not trust the selected card as a snapshot source. It sends only its external identifier and local form data, fetches the detail through the server-side client, rejects a mismatched response identifier, and persists both normalized source fields and the provider JSON. Existing events never resynchronize automatically.

Requests have a configurable five-second default timeout. Missing/rejected credentials and exhausted quota map to `503`, timeouts to `504`, and transport or invalid-response failures to `502`. Upstream bodies and exception URLs are never returned because either may contain provider details or the query-string credential.

Search is explicit rather than keystroke-driven and has no automatic retry. This protects the provider's finite quota and avoids duplicate calls during outages. A new synchronous client is opened per search; connection pooling, caching, and retry policy remain unnecessary at the current challenge scale.

## Organizer Event Boundary

`GET /api/events/organizer` scopes the collection by the authenticated Organizer. Creation produces a draft; full replacement updates local editable fields; publication is a separate idempotent state transition. Updates and publication select the event by both identifier and owner and lock that row, so a foreign identifier is indistinguishable from an unknown one.

Dates must carry a timezone and remain in the future. Capacity and price have bounded API validation in addition to database constraints. Before a capacity reduction, the service sums approved reservations and unexpired pending holds using PostgreSQL time. The new capacity must cover that committed quantity. Event editing, reservation creation, and payment use the same event-first lock order.

## Published Discovery Boundary

`GET /api/events` and `GET /api/events/{id}` are public because discovery itself is not an authorization boundary. Both query only local events with `published` status and a start later than PostgreSQL's current time. They do not call Ticketmaster and return a minimized contract without organizer identity, lifecycle status, provider links, or raw snapshots.

The optional `q` parameter is trimmed and matched case-insensitively against event name, venue, and city. SQLAlchemy's auto-escaped containment treats `%` and `_` as user text rather than SQL wildcard controls. Results are ordered by start time and bounded to 50 while pagination remains deferred.

A correlated aggregate calculates committed quantity for each event from approved reservations and pending reservations whose expiry is still in the future according to PostgreSQL. `available_quantity` is clamped at zero for defensive presentation. This read does not lock inventory: it is a useful snapshot, while the reservation command recalculates under an event-row lock before creating a hold.

## Temporary Reservation Boundary

`POST /api/reservations` requires the Customer role and accepts an event identifier plus positive quantity. The service selects only an upcoming published event with `FOR UPDATE`, reads PostgreSQL time, marks stale pending rows for that event, and sums approved quantity plus pending quantity whose deadline remains in the future. It creates a ten-minute pending hold only when the requested quantity fits; otherwise it returns `409` with the availability observed inside that transaction.

The event row is the inventory mutex. Reservation creation and Organizer capacity changes acquire the same lock before calculating committed quantity, so concurrent operations serialize without a long browser-held transaction or a second inventory system. Ticketmaster is never contacted inside this transaction.

`GET /api/reservations/{id}` finds a reservation by both identifier and authenticated Customer, returning the same `404` for an unknown or foreign resource. It marks that specific pending row expired when its database deadline has passed. Both private responses use `Cache-Control: no-store` and include `expires_at` and the sampled `server_time` used by the UI.

Discovery can ignore an expired pending row without first changing its status because the timestamp predicate is the inventory rule. Creating or restoring a hold also persists the observed expired state. This lazy approach needs no worker for correctness; a scheduled cleanup becomes worthwhile only if stale-row volume creates operational cost.

## Simulated Checkout Boundary

`POST /api/reservations/{id}/payment` requires the Customer role, ownership, and an explicit `approved` or `declined` simulation outcome. This contract is intentionally transparent and collects no fake card data. Private responses remain non-cacheable.

The service first resolves the owned reservation's event, locks that event, and then reloads and locks the reservation. This event-then-reservation order matches inventory operations and serializes concurrent payment requests. PostgreSQL time is sampled only after both locks are held.

For a pending hold, expiration has priority over the requested outcome. A valid decline marks the reservation declined and releases quantity. A valid approval marks it approved and inserts ticket numbers `1..quantity` inside the same commit. The database unique constraint on reservation and ticket number provides a second defense against duplicate issuance.

Approved, declined, and expired are terminal. A repeated request returns the stored status and current ticket count, even when its requested outcome conflicts with the first result. A declined or expired Customer retries by creating a new hold because the previous quantity has already returned to availability.

## Signed Ticket Boundary

`GET /api/tickets` requires a Customer session and joins only tickets from that Customer's approved reservations. It reconstructs each stable credential from the persisted UUID and the configured secret, returns its bearer sharing URL, and marks the response non-cacheable. The database stores no plaintext bearer credential.

The token is `v1.<32-lowercase-hex-UUID>.<unpadded-base64url-HMAC-SHA-256>`. The canonical signed payload is `v1:<identifier>`, the dedicated `TICKET_HMAC_SECRET` must contain at least 32 bytes, and verification uses `hmac.compare_digest`. A missing or short secret produces `503`; changing it changes all derived credentials. No personal, reservation, or event data is embedded in the token.

`GET /api/tickets/shared/{token}` is public because the token is an intentional bearer capability. The service verifies the signature before querying, then still requires a ticket backed by an approved reservation. Malformed, tampered, unsupported, unknown-but-validly-signed, and absent tickets all return the same `404`. The response omits ticket UUID, token, share URL, reservation, and Customer identity, but includes the event presentation fields and current use/revocation state.

HMAC proves origin, not current validity. PostgreSQL remains authoritative for approval, use, and revocation, and the Gate module uses that state to enforce one-time admission atomically.

## Gate Validation Boundary

`GET /api/gate/events` requires the Gate role and lists at most 100 published events. It deliberately does not apply the public discovery future-date filter: a published event remains selectable while entry continues after its scheduled start. Gate-to-event assignment is outside the mandatory scope.

`POST /api/gate/validations` accepts one selected event UUID and a stripped, bounded token. All four ticket decisions return a stable response with `outcome`, optional ticket number, and optional usage time. Authorization failures, missing signing configuration, invalid request shape, and an unknown/unpublished selected event remain HTTP errors rather than ticket outcomes.

After the event context is accepted, the HMAC is verified before any ticket row is trusted. Malformed, tampered, unsupported, or unknown identifiers return `invalid`. An authentic identifier selects its approved-reservation ticket with `SELECT FOR UPDATE`; a revoked ticket is invalid, an event mismatch is `wrong_event`, and an existing usage timestamp is `already_used`. Event mismatch has priority over prior-use disclosure for another event.

For a valid ticket, PostgreSQL time, `used_at`, and `used_by_user_id` are committed together. Concurrent requests block on the same ticket row. The first transition commits `valid`; the waiter reads the updated row and returns `already_used`. No external call runs in this transaction.

## Persistence Boundary

The schema contains users, opaque-session records, immutable catalog snapshots, organizer-owned events, temporary reservations, and one ticket row per issued admission. PostgreSQL constraints protect local invariants such as normalized emails, valid roles and statuses, positive capacity and quantities, fixed-length session digests, unique ticket positions, and coherent usage/revocation timestamps.

Enums are stored as strings with explicit named `CHECK` constraints. This keeps migrations easy to review and makes adding a state a normal versioned constraint change instead of a PostgreSQL enum-type operation.

Money uses integer minor units and timestamps include timezone information. The application supplies UUID identifiers; PostgreSQL remains authoritative for creation timestamps and later reservation-expiration decisions.

The local Podman hook writes an ignored `backend/.env.podman` only when it resolves a usable database address. A user-defined process `DATABASE_URL` or `backend/.env` takes precedence.

## Quality Boundary

Ruff owns formatting and linting, mypy runs in strict mode, and pytest with branch coverage protects behavior. Coverage is evidence for the tested foundation, not a project-wide target or a substitute for risk-focused tests. The root test-report hook also writes a JUnit XML result for automated inspection.
