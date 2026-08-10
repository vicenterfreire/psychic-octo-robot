# Elite Dev Challenge 2026

This repository contains the incremental implementation of the Elite Dev 2026 technical challenge: an event and ticketing platform for organizers, customers, and gate staff.

The mandatory product flow will allow an organizer to create a local event from the Ticketmaster catalog, a customer to hold inventory and complete a simulated payment, and gate staff to validate an HMAC-signed QR ticket exactly once.

## Current Status

The project is in its documentation and architecture foundation stage. No application code or dependency manifest has been created yet.

The next planned increment is `chore(project): initialize the full-stack workspace`.

## Accepted Technology Direction

- Frontend: React, Vite, TypeScript, React Router, and TanStack Query.
- Backend: Python 3.14 and FastAPI.
- Dependency management: `uv`, `pyproject.toml`, and a committed `uv.lock`.
- Compatibility export: `requirements.txt` generated from `uv.lock`; it will not be maintained manually.
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
- [Development workflow](docs/development/workflow.md)
- [Current state](docs/development/current-state.md)
- [Future improvements](docs/future-improvements.md)
- [Original challenge](docs/challenge/Desafio-Elite-Dev-2026.pdf)

## Development Workflow

Work is delivered in small local commits following `TODO.md`. Architecture, security, domain, and major dependency decisions require candidate approval and are recorded as ADRs before implementation.

No remote push is performed by the AI collaborator. Publication remains under the candidate's control.

## Setup

Application setup instructions do not exist yet because the applications have not been initialized. This section will be expanded in the next increment and kept accurate throughout development.
