# Elite Dev Challenge 2026

This repository contains the incremental implementation of the Elite Dev 2026 technical challenge: an event and ticketing platform for organizers, customers, and gate staff.

The mandatory product flow will allow an organizer to create a local event from the Ticketmaster catalog, a customer to hold inventory and complete a simulated payment, and gate staff to validate an HMAC-signed QR ticket exactly once.

## Current Status

The runnable project, persistence, authentication, Ticketmaster catalog, organizer management, published-event discovery, temporary inventory holds, simulated checkout, signed ticket presentation, and complete gate validation are implemented:

- `frontend/` contains a React, Vite, and TypeScript single-page application.
- `backend/` contains a Python 3.14 and FastAPI application.
- PostgreSQL runs through the checked-in Compose definition and has a versioned Alembic schema.
- The seed creates the four required accounts and one stable published event.
- The frontend calls the backend through a credentialed JSON client.
- Users authenticate through fixed seven-day opaque sessions stored in PostgreSQL and restored through an HTTP-only cookie.
- Organizer, customer, and gate routes are separated in both frontend navigation and reusable backend authorization dependencies.
- Organizers can search and select normalized Ticketmaster events without exposing the provider credential to the browser.
- Organizers can create a local draft from a trusted provider snapshot, edit only their own events, and publish explicitly.
- Visitors and Customers can search upcoming published events and inspect date, location, price, and current availability.
- Customers can hold a selected quantity for a PostgreSQL-timed payment window without overselling under concurrent requests.
- Customers can deterministically approve or decline the simulation; approval finalizes the reservation and issues exactly one persistent ticket row per unit.
- Customers can reopen a private ticket collection, render HMAC-signed QR credentials, and share minimized bearer views without exposing personal data.
- Gate staff can select a published event, scan its QR through a browser camera or enter the token manually, and receive an atomic valid, invalid, already-used, or wrong-event result.

The next planned increment is `test(core): cover critical business and end-to-end risks`.

## Prerequisites

The current increment was validated with:

- Node.js 22.21.0 and npm 10.9.4.
- `uv` 0.12.3.
- `uv`-managed CPython 3.14.7.
- Podman Desktop 6.0.2 with an initialized and running Podman machine.

## Setup

Install the frontend dependencies from the committed npm lockfile:

```powershell
npm --prefix frontend ci
```

Create and synchronize the backend environment from the committed `uv.lock`:

```powershell
uv --directory backend sync --locked --managed-python
```

`backend/requirements.txt` is a runtime-only compatibility export generated from `uv.lock`. It is committed for evaluators that require `pip`, but it must never be edited manually.

The checked-in `.env.example` files document optional local configuration. Vite automatically reads an untracked `frontend/.env` file. The backend loads untracked `backend/.env` and `backend/.env.podman` files without overriding variables already defined by the process.

## Prepare PostgreSQL

Create the container, wait for PostgreSQL, apply the schema, and seed the evaluation data:

```powershell
npm run db:prepare
```

The project hook locates `podman.exe` from `PATH` or known Podman Desktop installation directories. It runs the pinned `podman-compose` 1.6.0 provider through `uvx`, so no global Compose installation or MCP server is required. When Podman's WSL port is not forwarded to Windows localhost, the hook resolves the current machine address and writes the ignored `backend/.env.podman` connection file.

Database lifecycle commands:

```powershell
npm run db:up
npm run db:status
npm run db:logs
npm run db:down
```

`db:down` preserves the named PostgreSQL volume. `npm run db:reset` deletes only this project's database volume and starts an empty database; run migrations and seed afterward, or use `npm run db:prepare`.

The Compose credentials `elite` / `elite` are deliberately public local-development defaults. Production credentials must come from environment secrets.

## Seeded Evaluation Data

| Role | Email | Password |
| --- | --- | --- |
| Organizer | `organizer@example.com` | `Organizer123!` |
| Customer | `customer.one@example.com` | `Customer123!` |
| Customer | `customer.two@example.com` | `Customer123!` |
| Gate | `gate@example.com` | `Gate123!` |

The seed also creates the published `Aurora Live 2030` event with capacity 100 and a BRL 150.00 price stored as `15000` minor units. Passwords are persisted only as Argon2id hashes.

## Authentication and Sessions

Open `http://localhost:5173/login` and use any seeded account. The backend exposes `POST /api/auth/login`, `GET /api/auth/me`, and `POST /api/auth/logout`.

Passwords use Argon2id through `pwdlib` with the current recommended parameters `m=65536,t=3,p=4`. Login creates a cryptographically random opaque credential, sends it only as an HTTP-only `SameSite=Lax` cookie, and stores only its SHA-256 digest in PostgreSQL. The fixed seven-day session survives browser restarts, does not renew on activity, and is revoked server-side on logout.

Local HTTP development sets `SESSION_COOKIE_SECURE=false`. Non-development configuration defaults it to `true`, which requires HTTPS. The backend remains authoritative for roles and resource ownership; frontend route guards provide navigation and user experience, not a security boundary.

## Ticketmaster Configuration

Create a Ticketmaster developer key and place it only in the untracked `backend/.env` file:

```dotenv
TICKETMASTER_API_KEY=your-key-here
TICKETMASTER_TIMEOUT_SECONDS=5
```

The official [Discovery API v2 documentation](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/) describes account setup, event search, and event detail contracts. The browser calls only the local catalog and event APIs; the backend adds the `apikey` parameter when it contacts Ticketmaster.

Search runs only when an Organizer submits the form and returns at most 12 normalized items. Missing or rejected credentials, quota exhaustion, timeout, invalid data, and provider unavailability produce stable messages without returning upstream payloads or secrets.

Creating an event sends the selected provider identifier back to the backend. The backend fetches that item again, verifies the returned identifier, and stores its provider response as an immutable snapshot beside the Organizer's editable local date, venue, capacity, and price. A later provider change therefore does not silently alter an existing local event.

The configured credential was exercised against both the live Ticketmaster search and event-detail endpoints. Validation output contained only normalized identifiers/names and confirmed that the credential was absent from the persisted snapshot candidate.

## Organizer Event Management

The Organizer workspace lists only events owned by the current account. `POST /api/events` creates a draft, `PUT /api/events/{id}` replaces its editable local details, and `POST /api/events/{id}/publish` makes publication explicit. Unknown or foreign event identifiers return the same not-found outcome, avoiding cross-account disclosure.

Capacity cannot be reduced below approved reservations or pending reservations whose hold has not expired according to PostgreSQL time. Event editing, reservation creation, and checkout use the same event-row lock order before their inventory decisions. Dates must be timezone-aware and in the future; money crosses the API and is stored as integer minor units.

## Published Event Discovery

`GET /api/events?q=...` and `GET /api/events/{id}` are public read endpoints backed only by local PostgreSQL data. They expose upcoming published events and never depend on Ticketmaster availability. Drafts, past events, organizer identity, provider payloads, and management state are excluded from the public contract.

Basic text search is case-insensitive across local event name, venue, and city and returns at most 50 upcoming results ordered by start time. Advanced filters and pagination remain deliberately deferred. Availability is calculated as capacity minus approved quantities and unexpired pending holds according to PostgreSQL time. It is an informative snapshot; the reservation transaction remains authoritative when the Customer selects a quantity.

The public interface is available at `http://localhost:5173/events`. A seeded Customer sees the same discovery flow at `/customer`, with event details under the corresponding public or authenticated route.

## Temporary Reservation Holds

An authenticated Customer submits quantity through `POST /api/reservations`. The backend locks the published, upcoming event row, uses PostgreSQL time, marks stale holds when encountered, recalculates approved and active pending quantity, and creates the hold only when enough inventory remains. Concurrent reservation creation and capacity edits take the same event lock, so their final inventory decisions are serialized.

Holds last ten minutes by default. Set `RESERVATION_LIFETIME_SECONDS` in `backend/.env` only when a different local demonstration window is useful. Discovery immediately ignores a hold after its database deadline even if its stored status has not yet been updated by a later operation.

The Customer is redirected to `/customer/reservations/{id}`, which restores the private hold with `GET /api/reservations/{id}` after reload. The API returns both `expires_at` and `server_time`; the browser corrects its display for local clock skew, but only the backend may decide whether the hold is valid. An expired screen links back to the event so the Customer can select quantity again.

## Simulated Checkout

`POST /api/reservations/{id}/payment` accepts an explicit deterministic `approved` or `declined` simulation outcome. No card or financial data is collected and no real charge occurs. The first terminal result wins: repeated or contradictory submissions return the stored result instead of changing it.

Checkout locks the event and the Customer-owned reservation in that order, then samples PostgreSQL time. An expired hold becomes `expired`; a declined hold releases inventory immediately; an approved hold becomes `approved` and creates one persistent ticket row for each reserved unit in the same transaction. Concurrent approval requests therefore cannot duplicate tickets, and the unique reservation/ticket-number constraint remains a second integrity barrier.

The hold screen presents approval, refusal, expiration, and retry guidance and restores terminal results after reload. Approved ticket rows are exposed by the signed-ticket flow described below.

## Signed Tickets and Sharing

Set a stable, high-entropy ticket-signing secret in the untracked `backend/.env` file before opening ticket pages:

```dotenv
TICKET_HMAC_SECRET=replace-with-at-least-32-random-bytes
```

One local way to generate a suitable value is:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Keep the generated value stable. Replacing it invalidates signatures produced with the previous value until key rotation is implemented. Missing or shorter-than-32-byte secrets make ticket endpoints fail closed with `503` rather than issue unverifiable credentials.

Each approved ticket is represented by `v1.<32-lowercase-hex-UUID>.<base64url-HMAC-SHA-256>`. The signature covers the canonical `v1:<identifier>` payload and is checked with a constant-time comparison. The token and QR contain no name, email, reservation identifier, or event details. HMAC establishes that the credential was issued by this application; PostgreSQL still determines whether its reservation is approved and whether the ticket is used or revoked.

An authenticated Customer opens the private collection at `/customer/tickets`. The frontend renders the signed token as an SVG QR through `qrcode.react`. The same token appears in `/tickets/share/{token}` as an intentionally bearer-style link: anyone who receives it can present the ticket, so the interface warns the Customer to share it only with someone trusted. The public response is non-cacheable and limited to presentation state plus the event details needed by the recipient.

## Gate Validation

Sign in as the seeded Gate user and open `/gate`. `GET /api/gate/events` lists up to 100 published events, including events whose start time has passed so admission can continue after the scheduled start. Gate assignment is deliberately broad in the challenge scope: any Gate user may validate any published event.

Manual submission calls `POST /api/gate/validations` with the selected event identifier and ticket token. The backend verifies the HMAC before trusting ticket state, locks the ticket row with `SELECT FOR UPDATE`, and then applies a deterministic result:

- `valid`: the authentic, approved, unused, unrevoked ticket belongs to the selected event; `used_at` and the Gate user are committed together.
- `invalid`: the token is malformed, tampered, unknown, revoked, or not backed by an approved reservation.
- `wrong_event`: the authentic ticket belongs to a different event.
- `already_used`: the authentic ticket for the selected event has a previous usage timestamp.

The row lock serializes concurrent attempts. Exactly one request can change an unused ticket to used; a competing request waits and then observes `already_used`. All business results use a stable `200` response contract, while authentication, configuration, and missing-event failures remain HTTP errors. Responses are non-cacheable.

The camera remains off until the Gate user selects `Start camera`. That action lazily loads the QR-only `@zxing/browser` decoder, requests an environment-facing camera, and stops capture on the first decoded value before calling the same validation endpoint. A validation already in progress cannot trigger a second request. Changing the selected event, stopping the camera, or leaving the screen also releases the active scanner.

Denied permission, missing or busy cameras, unsupported browser APIs, and startup failures produce recovery guidance without hiding the manual field. The decoded QR text has no client-side authority: only the four backend outcomes control admission. If a network failure occurs after a scan, the captured text remains in the manual field so the operator can retry the exact credential.

Browser camera access requires a secure context. `http://localhost:5173` is accepted for same-computer development by modern browsers; testing from a phone or another computer must serve the frontend over HTTPS. The 0.1.x scanner line is deliberately locked because it supports the project's Node.js 22 runtime; the current 0.2.x peer dependency requires Node.js 24.

## Run Locally

Start each application in a separate terminal from the repository root:

```powershell
npm run dev:backend
```

```powershell
npm run dev:frontend
```

Open `http://localhost:5173`. The backend health endpoint is available at `http://localhost:8000/api/health`.

The frontend API base URL defaults to `http://localhost:8000/api`. Set `VITE_API_URL` in `frontend/.env` only when the backend uses another address. The backend accepts credentialed browser requests only from the configured `FRONTEND_ORIGIN`, which defaults to `http://localhost:5173`.

## Quality Commands

The root scripts delegate to the appropriate frontend and backend tools:

```powershell
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
```

Prepare PostgreSQL before `npm test`; the backend suite intentionally exercises the real database. Use `npm run format` to apply Prettier and Ruff formatting.

For machine-readable results, run:

```powershell
npm run test:report
```

This writes ignored local artifacts to `.artifacts/test-results/`: Vitest JSON, pytest JUnit XML, and `summary.json` with suite exit codes and test counts. The hook runs both suites even when one fails, making it suitable for automated inspection.

## Accepted Technology Direction

- Frontend: React, Vite, TypeScript, React Router, TanStack Query, localized SVG QR rendering through `qrcode.react`, and lazily loaded camera decoding through `@zxing/browser`.
- Backend: Python 3.14 and FastAPI.
- Dependency management: `uv`, `pyproject.toml`, and a committed `uv.lock`.
- Compatibility export: `requirements.txt` generated from `uv.lock`; it is not maintained manually.
- Persistence: PostgreSQL, SQLAlchemy 2, Alembic, and Psycopg 3.
- Local database: Podman with a Compose-compatible `compose.yaml`.
- External catalog: backend-only Ticketmaster Discovery API access through `httpx`.
- Authentication: seven-day opaque database sessions stored in an HTTP-only cookie.
- Password hashing: Argon2id through `pwdlib`.
- Ticket authenticity: versioned HMAC-signed ticket tokens.
- Testing: focused backend, frontend, integration, and browser tests; bounded mutation testing only after the critical suite is stable.

## Documentation

- [Development plan](TODO.md)
- [Functional requirements](docs/requirements/functional.md)
- [Non-functional requirements](docs/requirements/non-functional.md)
- [Architecture overview](docs/architecture/overview.md)
- [Architecture decisions](docs/architecture/decisions/)
- [Domain knowledge](docs/knowledge-base/domain.md)
- [Backend knowledge](docs/knowledge-base/backend.md)
- [Frontend knowledge](docs/knowledge-base/frontend.md)
- [Development workflow](docs/development/workflow.md)
- [Database workflow](docs/development/database.md)
- [Current state](docs/development/current-state.md)
- [Future improvements](docs/future-improvements.md)
- [Original challenge](docs/challenge/Desafio-Elite-Dev-2026.pdf)

## Development Workflow

Work is delivered in small local commits following `TODO.md`. Architecture, security, domain, and major dependency decisions require candidate approval and are recorded as ADRs before implementation.

No remote push is performed by the AI collaborator. Publication remains under the candidate's control.

## Current Limitations

The mandatory organizer, Customer, ticket, and camera/manual Gate flows are implemented. Camera scanning still depends on a secure browser context, user permission, and usable hardware, so manual entry remains permanently available. Displayed availability can change before a hold is created; only a successful reservation response guarantees a temporary quantity. HMAC key rotation and a ticket-revocation command are not implemented; the schema and responses already retain revocation state for later workflows. Server-side catalog caching, advanced discovery filters, pagination, background stale-row cleanup, login rate limiting, session rotation/device management, automatic expired-session cleanup, and production-topology CSRF hardening are intentionally deferred.
