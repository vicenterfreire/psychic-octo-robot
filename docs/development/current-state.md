# Current State

## Snapshot

- Date: 2026-08-10.
- Branch: local `main`, based on published commit `14d5d9c`.
- Phase: requirements and architecture foundation.
- Application code: not initialized.
- Database schema: not initialized.
- Automated tests: not initialized.
- Deployment: not selected.

## Implemented Documentation

- Consolidated functional and non-functional requirements.
- Accepted architecture overview.
- ADRs for stack, persistence, external catalog, inventory, authentication, passwords, temporary reservations, ticket security, and testing.
- Domain vocabulary and invariants.
- Incremental development workflow.
- Development plan and future-improvements backlog.

## Accepted Technical Direction

- React, Vite, and TypeScript frontend.
- Python 3.14 and FastAPI backend.
- `uv` with `uv.lock`; generated `requirements.txt` for compatibility.
- PostgreSQL through Podman Compose.
- Synchronous SQLAlchemy 2, Psycopg 3, and Alembic.
- TanStack Query for server state.
- Seven-day opaque sessions and Argon2id password hashes.
- Ten-minute temporary reservations using database time and lazy expiration.
- Ticketmaster catalog snapshots and quantity inventory.
- HMAC-signed bearer tickets with online one-time validation.

## Environment Observation

The candidate reports that Python, `uv`, and Podman were installed and validated in a new terminal. The current Codex process still has an older `PATH` snapshot and could not resolve those commands. It can resolve Node.js 22.21.0, but the npm launcher visible to this process references a missing global npm module.

The next technical increment must revalidate all required executable paths before generating application files. This is an environment observation, not an application failure.

## Known Limitations

- No application can be run yet.
- No setup command has been validated yet.
- The challenge receipt date and exact seven-day deadline are not recorded.
- Deployment topology and production cookie strategy remain deferred.

## Next Commit

`chore(project): initialize the full-stack workspace`
