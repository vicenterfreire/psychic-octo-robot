# Current State

## Snapshot

- Date: 2026-08-10.
- Branch: local `main`, based on published commit `14d5d9c` and developed through small local commits.
- Phase: runnable full-stack and persistence foundation.
- Frontend: React, Vite, and TypeScript application initialized.
- Backend: Python 3.14 and FastAPI application initialized.
- Database: PostgreSQL 17 schema migrated and seeded through Podman.
- Automated tests: one frontend test, one backend route test, and three PostgreSQL integration tests.
- Deployment: not selected.

## Implemented Persistence Foundation

- `compose.yaml` defines a healthy PostgreSQL service with a named persistent volume.
- The PowerShell project hook resolves the candidate's Podman Desktop executable even when the current process has a stale `PATH`.
- The hook runs a pinned Compose provider through `uvx` and adapts to missing WSL localhost forwarding without changing global Podman settings.
- SQLAlchemy models represent users, sessions, catalog snapshots, events, reservations, and tickets.
- Named database constraints protect roles, states, normalized values, quantities, money, timestamps, ownership references, session digests, and ticket usage shape.
- Alembic revision `2db7467132b0` creates the initial schema without detected metadata drift.
- The idempotent seed creates one organizer, two customers, one gate user, one Ticketmaster-style snapshot, and one published event.
- Seed passwords use the accepted Argon2id implementation and are never stored in plaintext.
- Backend runtime dependencies are locked and `requirements.txt` has been regenerated from `uv.lock`.

## Validated Environment

- Node.js 22.21.0 and npm 10.9.4.
- `uv` 0.12.3 with managed CPython 3.14.7.
- Podman Desktop 6.0.2 with a running WSL machine.
- PostgreSQL 17.10 from `postgres:17-alpine`.
- `podman-compose` 1.6.0 executed in an isolated `uvx` environment.

## Validation Result

- PostgreSQL starts healthy through the project hook.
- Reset removes only the project volume and recreates an empty database.
- Alembic upgrades an empty database to the current head.
- `alembic check` reports no schema drift.
- The first seed inserts all evaluation records and the second inserts none.
- Direct database inspection confirmed seven tables, 35 constraints, four Argon2id hashes, and the published event.
- PostgreSQL rejects a reservation with quantity zero.
- All four backend tests pass with 93% coverage of the current backend.

## Known Limitations

- No database session is injected into HTTP routes yet; that begins with authentication.
- Role and ownership relationships are structurally represented, but business authorization remains application logic for later commits.
- Cross-table rules such as "tickets only from approved reservations" cannot be expressed by simple row constraints and will be enforced transactionally by services.
- The Podman hook is Windows-specific; other systems can use the standard `compose.yaml` with their installed Compose provider.
- The backend test client still emits an upstream FastAPI/Starlette deprecation warning.
- Deployment topology and production secrets remain deferred.

## Next Commit

`feat(auth): implement persistent opaque-session authentication`
