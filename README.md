# Elite Dev Challenge 2026

This repository contains the incremental implementation of the Elite Dev 2026 technical challenge: an event and ticketing platform for organizers, customers, and gate staff.

The mandatory product flow will allow an organizer to create a local event from the Ticketmaster catalog, a customer to hold inventory and complete a simulated payment, and gate staff to validate an HMAC-signed QR ticket exactly once.

## Current Status

The runnable project, persistence, authentication, and Ticketmaster catalog foundations are complete:

- `frontend/` contains a React, Vite, and TypeScript single-page application.
- `backend/` contains a Python 3.14 and FastAPI application.
- PostgreSQL runs through the checked-in Compose definition and has a versioned Alembic schema.
- The seed creates the four required accounts and one stable published event.
- The frontend calls the backend through a credentialed JSON client.
- Users authenticate through fixed seven-day opaque sessions stored in PostgreSQL and restored through an HTTP-only cookie.
- Organizer, customer, and gate routes are separated in both frontend navigation and reusable backend authorization dependencies.
- Organizers can search and select normalized Ticketmaster events without exposing the provider credential to the browser.

The next planned increment is `feat(events): implement organizer event management`.

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

The official [Discovery API v2 documentation](https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/) describes account setup and the event-search contract. The browser calls only `GET /api/catalog/events?q=...`; the backend adds the `apikey` parameter when it contacts Ticketmaster.

Search runs only when an Organizer submits the form and returns at most 12 normalized items. Missing or rejected credentials, quota exhaustion, timeout, invalid data, and provider unavailability produce stable messages without returning upstream payloads or secrets.

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

- Frontend: React, Vite, TypeScript, React Router, and TanStack Query.
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

Authentication and catalog search are complete, but local event creation and all reservation, payment, ticket, and gate business APIs remain scheduled as later commits. Catalog selection is currently transient and becomes persistable in the event-management increment. The provider contract was validated with deterministic HTTP transports; a live Ticketmaster request was not executed because no developer key is stored in the workspace. Server-side catalog caching, login rate limiting, session rotation/device management, automatic expired-session cleanup, and production-topology CSRF hardening are intentionally deferred.
