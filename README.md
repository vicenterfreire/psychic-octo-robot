# Elite Dev Challenge 2026

Event and ticketing platform built with React, FastAPI, and PostgreSQL. This README contains only
the setup and execution paths required for local evaluation. Architecture, implementation details,
testing evidence, trade-offs, and AI collaboration are linked under
[Complementary Documentation](#complementary-documentation).

## Setup Without Containers

This path requires only:

- Python 3.14;
- Node.js 22 with npm;
- a reachable PostgreSQL instance.

PostgreSQL may be installed on the same computer or hosted elsewhere. Create an empty database and
a login allowed to create its schema, then copy the environment files from the repository root:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Set `DATABASE_URL` in `backend/.env` to the SQLAlchemy/Psycopg connection for that database:

```dotenv
DATABASE_URL=postgresql+psycopg://app_user:app_password@localhost:5432/elite_dev
```

Set a stable `TICKET_HMAC_SECRET` with at least 32 bytes. One way to generate it is:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the generated value into `backend/.env`:

```dotenv
TICKET_HMAC_SECRET=replace-with-the-generated-value
```

To exercise live Organizer catalog search and event creation, also set the optional Ticketmaster
Discovery API credential:

```dotenv
TICKETMASTER_API_KEY=your-ticketmaster-key
```

The seeded event and all other local flows start without a Ticketmaster key.

### Backend With Standard Python, `venv`, and `pip`

The committed `requirements.txt` is generated from the locked `uv` environment specifically to
support evaluators who do not use `uv`:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install --upgrade pip
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
```

### Backend With `uv` (Alternative)

If `uv` is already available, the equivalent locked setup is:

```powershell
uv --directory backend sync --locked --managed-python
```

Only one backend dependency setup is necessary. `uv` is the development tool used by the project,
not a runtime requirement of the FastAPI application.

### Frontend Dependencies

Install the exact frontend dependency graph from its lockfile:

```powershell
npm --prefix frontend ci
```

## Run Without Containers

### Backend With `venv` and `pip`

From the repository root, apply migrations and seed once:

```powershell
$env:PYTHONPATH = (Resolve-Path backend/src)
backend/.venv/Scripts/python -m alembic -c backend/alembic.ini upgrade head
backend/.venv/Scripts/python -m backend.database.seed
```

Keep that terminal open and start FastAPI:

```powershell
backend/.venv/Scripts/python -m uvicorn backend.main:app --reload
```

### Backend With `uv`

If the alternative `uv` setup was selected, apply migrations, seed, and start FastAPI with:

```powershell
uv --directory backend run alembic upgrade head
uv --directory backend run python -m backend.database.seed
uv --directory backend run uvicorn backend.main:app --reload
```

### Frontend

In a second terminal, from the repository root:

```powershell
npm run dev:frontend
```

Open:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000/api`
- Swagger UI: `http://localhost:8000/docs`

## Setup and Run With Containers

Containers are an optional reproducibility path, not an application requirement. Choose either
Docker with Docker Compose or Podman with a Compose provider. Host Python and PostgreSQL are not
required for this path because they run inside the containers.

Create only the backend environment file:

```powershell
Copy-Item backend/.env.example backend/.env
```

Set `TICKET_HMAC_SECRET` and, optionally, `TICKETMASTER_API_KEY` as described in the containerless
setup above. Compose supplies its own internal `DATABASE_URL`.

### Docker Compose

```powershell
docker compose up --detach --build --wait
```

Inspect or stop the Docker Compose stack with:

```powershell
docker compose ps
docker compose logs --tail 100
docker compose down
```

### Podman

The project hook is the validated Windows/Podman path. It resolves Podman Desktop, runs the pinned
Compose provider through `uvx`, handles Podman WSL address differences, waits for health checks, and
prints the reachable URLs:

```powershell
npm run app:up
```

Inspect or stop the Podman stack with:

```powershell
npm run app:status
npm run app:logs
npm run app:down
```

The project hook requires Node.js/npm and `uv`; they support this specialized local orchestration,
not the containerized application itself. A separately installed Podman Compose provider may use
the checked-in `compose.yaml` directly.

Both container paths build and start PostgreSQL, apply Alembic migrations, run the idempotent seed,
start FastAPI and the built React application, and preserve PostgreSQL data when stopped normally.
Do not run `db:prepare` separately for the full-stack Compose workflow.

## Seeded Accounts

| Role      | Email                      | Password        |
| --------- | -------------------------- | --------------- |
| Organizer | `organizer@example.com`    | `Organizer123!` |
| Customer  | `customer.one@example.com` | `Customer123!`  |
| Customer  | `customer.two@example.com` | `Customer123!`  |
| Gate      | `gate@example.com`         | `Gate123!`      |

The seed also creates the published `Aurora Live 2030` event with available inventory.

## Troubleshooting

- **PostgreSQL connection fails without containers:** confirm that the server is running, the
  database exists, the login can create its schema, and `DATABASE_URL` uses the correct host and
  port.
- **Python cannot import `backend` in the `pip` workflow:** run the commands from the repository
  root and set `$env:PYTHONPATH = (Resolve-Path backend/src)` in the backend terminal.
- **Docker or Podman services do not become healthy:** inspect the corresponding Compose status and
  logs. Backend logs include migration, seed, environment, and database connection failures.
- **Port 5432, 8000, or 5173 is already in use:** stop the conflicting process. Advanced port
  overrides are documented in the [database workflow](docs/development/database.md).
- **Ticket or Gate endpoints return `503`:** confirm that `TICKET_HMAC_SECRET` in `backend/.env` is
  stable and contains at least 32 bytes, then restart the backend or Compose stack.
- **Ticketmaster search fails:** confirm `TICKETMASTER_API_KEY`, network access, and provider quota.
  The seeded event does not depend on Ticketmaster.
- **Login succeeds but the browser loses the session or cannot call the API:** keep
  `FRONTEND_ORIGIN` and `VITE_API_URL` aligned with the exact URLs being used, then restart both
  applications after environment changes.
- **Camera access fails:** use `localhost` or HTTPS, grant browser permission, and close other
  software using the camera. Manual ticket entry remains available in the Gate screen.
- **A clean container database is required:** `npm run db:reset` deletes this project's PostgreSQL
  volume. This is destructive; use it only when existing local data can be discarded.

## Complementary Documentation

These documents are not required to start the application. They provide the reasoning and evidence
behind the implementation:

- [Current implementation and validation evidence](docs/development/current-state.md)
- [Architecture overview](docs/architecture/overview.md)
- [Architecture decisions and rejected alternatives](docs/architecture/decisions/)
- [Functional requirements](docs/requirements/functional.md) and
  [non-functional requirements](docs/requirements/non-functional.md)
- [Domain](docs/knowledge-base/domain.md), [backend](docs/knowledge-base/backend.md), and
  [frontend](docs/knowledge-base/frontend.md) knowledge bases
- [Database and alternative host-development workflow](docs/development/database.md)
- [Development and testing workflow](docs/development/workflow.md)
- [AI collaboration and candidate ownership](docs/development/ai-collaboration.md)
- [Deliberately deferred improvements](docs/future-improvements.md)
- [Original challenge](docs/challenge/Desafio-Elite-Dev-2026.pdf)
