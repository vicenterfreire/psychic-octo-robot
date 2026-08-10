# Elite Dev Challenge 2026

This repository contains the incremental implementation of the Elite Dev 2026 technical challenge: an event and ticketing platform for organizers, customers, and gate staff.

The mandatory product flow will allow an organizer to create a local event from the Ticketmaster catalog, a customer to hold inventory and complete a simulated payment, and gate staff to validate an HMAC-signed QR ticket exactly once.

## Current Status

The runnable project foundation is complete:

- `frontend/` contains a React, Vite, and TypeScript single-page application.
- `backend/` contains a Python 3.14 and FastAPI application.
- The frontend calls the backend through a credentialed JSON client.
- Both applications expose a minimal status interface used to validate local integration.

The next planned increment is `feat(database): model persistence and seed evaluation data`.

## Prerequisites

The current increment was validated with:

- Node.js 22.21.0 and npm 10.9.4.
- `uv` 0.12.3.
- `uv`-managed CPython 3.14.7.
- Podman Desktop for the PostgreSQL increment that follows.

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

The checked-in `.env.example` files document optional local configuration, and the current defaults work without copying them. Vite automatically reads an untracked `frontend/.env` file. Backend overrides are process environment variables; set them in the terminal before starting FastAPI.

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

Use `npm run format` to apply Prettier and Ruff formatting.

## Accepted Technology Direction

- Frontend: React, Vite, TypeScript, React Router, and TanStack Query.
- Backend: Python 3.14 and FastAPI.
- Dependency management: `uv`, `pyproject.toml`, and a committed `uv.lock`.
- Compatibility export: `requirements.txt` generated from `uv.lock`; it is not maintained manually.
- Persistence: PostgreSQL, SQLAlchemy 2, Alembic, and Psycopg 3.
- Local database: Podman with a Compose-compatible `compose.yaml`.
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
- [Current state](docs/development/current-state.md)
- [Future improvements](docs/future-improvements.md)
- [Original challenge](docs/challenge/Desafio-Elite-Dev-2026.pdf)

## Development Workflow

Work is delivered in small local commits following `TODO.md`. Architecture, security, domain, and major dependency decisions require candidate approval and are recorded as ADRs before implementation.

No remote push is performed by the AI collaborator. Publication remains under the candidate's control.

## Current Limitations

This increment contains only the application shell and health integration. PostgreSQL, authentication, catalog access, event management, reservations, payments, tickets, and gate validation are intentionally scheduled as later commits.
