# Current State

## Snapshot

- Date: 2026-08-10.
- Branch: local `main`, based on published commit `14d5d9c` and developed through small local commits.
- Phase: runnable full-stack foundation.
- Frontend: React, Vite, and TypeScript application initialized.
- Backend: Python 3.14 and FastAPI application initialized.
- Database schema: not initialized.
- Automated tests: one frontend integration-boundary test and one backend health-route test.
- Deployment: not selected.

## Implemented Application Foundation

- Root commands delegate development and quality tasks without introducing a second workspace manager.
- The frontend has application providers, route configuration, a feature-oriented folder boundary, a credentialed JSON API client, status feedback, and a responsive application shell.
- The backend has an application factory, environment-backed settings, explicit credentialed CORS configuration, API routing, and a typed health endpoint.
- Frontend dependencies are locked by `frontend/package-lock.json`.
- Backend runtime and development dependencies are locked by `backend/uv.lock`.
- `backend/requirements.txt` is generated from the runtime portion of `uv.lock` for compatibility and is not hand-maintained.
- Environment examples contain no secrets and the applications have safe local defaults.

## Validated Environment

- Node.js 22.21.0.
- npm 10.9.4.
- `uv` 0.12.3.
- `uv`-managed CPython 3.14.7.
- The candidate confirmed that Podman Desktop is initialized and usable from a new terminal; PostgreSQL is not introduced until the next commit.

## Validation Result

- Frontend formatting, linting, type checking, component test, and production build pass.
- Backend lock verification, formatting, linting, strict type checking, route test with branch coverage, and package build pass.
- The generated requirements dependency content matches a fresh export from `uv.lock`.
- Both development servers start together.
- `GET /api/health` returns the expected payload and credentialed CORS headers for the configured frontend origin.
- The frontend development server returns the expected application shell.

## Accepted Technical Direction

- PostgreSQL through Podman Compose.
- Synchronous SQLAlchemy 2, Psycopg 3, and Alembic.
- TanStack Query for server state.
- Seven-day opaque sessions and Argon2id password hashes.
- Ten-minute temporary reservations using database time and lazy expiration.
- Ticketmaster catalog snapshots and quantity inventory.
- HMAC-signed bearer tickets with online one-time validation.

## Known Limitations

- The status screen is scaffolding, not a challenge business feature.
- No persistence, authentication, authorization, or domain workflow exists yet.
- The backend test emits an upstream FastAPI/Starlette deprecation warning about the current test client transport, but the test passes and application behavior is unaffected.
- The challenge receipt date and exact seven-day deadline are not recorded.
- Deployment topology and production cookie strategy remain deferred.

## Next Commit

`feat(database): model persistence and seed evaluation data`
