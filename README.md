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
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

The root `.env` controls local binding for both host-process and Compose workflows. Its safe default
uses `127.0.0.1` and advertises `localhost`. To expose the application to the local network, set:

```dotenv
APP_BIND_ADDRESS=0.0.0.0
PUBLIC_HOST=192.168.15.130
```

Use the computer's current Wi-Fi IPv4 address for `PUBLIC_HOST`. The wildcard address is valid only
for binding and must never be used as a browser URL.

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
npm run dev:backend
```

### Backend With `uv`

If the alternative `uv` setup was selected, apply migrations, seed, and start FastAPI with:

```powershell
uv --directory backend run alembic upgrade head
uv --directory backend run python -m backend.database.seed
npm run dev:backend
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

Create the shared local configuration and backend secret files:

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
```

Set `TICKET_HMAC_SECRET` and, optionally, `TICKETMASTER_API_KEY` as described in the containerless
setup above. Compose supplies its own internal `DATABASE_URL`. The root `.env` defaults are enough
for both normal container execution and the temporary phone-camera workflow:

```dotenv
APP_BIND_ADDRESS=127.0.0.1
PUBLIC_HOST=localhost
BACKEND_PORT=8000
FRONTEND_PORT=5173
POSTGRES_PORT=5432
```

### Project Command: Docker or Podman

The project command detects a running Docker engine first and otherwise uses the validated Podman
path. It builds and starts PostgreSQL, applies migrations and seed data, starts FastAPI, and serves
the built React application. It reads `APP_BIND_ADDRESS`, `PUBLIC_HOST`, and the published ports
from the same root `.env` used by the host-process commands:

```powershell
npm run app:up
```

Inspect or stop the stack with:

```powershell
npm run app:status
npm run app:logs
npm run app:down
```

Force one provider when both are installed:

```powershell
$env:COMPOSE_PROVIDER = "Docker" # or "Podman"
npm run app:up
```

Docker uses its installed Compose plugin and does not require `uv`. The validated Windows/Podman
fallback resolves Podman Desktop and runs a pinned Compose provider through `uv`.

### Test the Camera From a Phone Without Installing a Certificate

Stop any host-process Vite or FastAPI servers using the configured ports, keep the computer online,
and start the optional Quick Tunnel profile:

```powershell
npm run app:tunnel:up
```

The command prints one temporary `https://...trycloudflare.com` application URL. Open that URL on
the phone, sign in with the seeded Gate account, select an event, and grant camera permission. The
same URL exposes the proxied API at `/api` and Swagger at `/docs`; no LAN IP, inbound firewall rule,
or certificate installation is required.

Reprint the active URL or inspect only the tunnel logs with:

```powershell
npm run app:tunnel:url
npm run app:tunnel:logs
```

The random URL is public to anyone who receives it, and the evaluation credentials are documented
below. Stop the complete temporary stack immediately after testing:

```powershell
npm run app:tunnel:down
```

This is a development-only
[Cloudflare Quick Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)
with no availability guarantee. Its URL changes when recreated, requires outbound internet access,
and is not the optional production deployment bonus described by the challenge.

### Direct Docker Compose Alternative

Run Compose directly:

```powershell
docker compose up --detach --build --wait
```

Inspect or stop the Docker Compose stack with:

```powershell
docker compose ps
docker compose logs --tail 100
docker compose down
```

Both normal container paths build and start PostgreSQL, apply Alembic migrations, run the
idempotent seed, start FastAPI and the built React application, and preserve PostgreSQL data when
stopped normally. Do not run `db:prepare` separately for the full-stack Compose workflow. The
temporary tunnel should be started through the project command above because that command also
enables the session cookie's HTTPS-only attribute.

## Publish on Railway

The repository supports an isolated Railway monorepo deployment with a public Nginx frontend, a
private FastAPI backend, and managed PostgreSQL. Railway variables replace local `.env` files, and
the backend service runs migrations and the idempotent seed before deployment.

Follow [Railway Deployment](docs/development/railway-deployment.md) for the exact service names,
root directories, config paths, variables, deployment order, verification, and rollback guidance.
Only the frontend receives a public domain; do not import the development `compose.yaml` or publish
the backend/database directly.

## Seeded Accounts

| Role      | Email                      | Password        |
| --------- | -------------------------- | --------------- |
| Organizer | `organizer@example.com`    | `Organizer123!` |
| Customer  | `customer.one@example.com` | `Customer123!`  |
| Customer  | `customer.two@example.com` | `Customer123!`  |
| Gate      | `gate@example.com`         | `Gate123!`      |

The seed also creates the published `Aurora Live 2030` event with available inventory.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for Docker/Podman selection, database recovery, LAN and
phone access, CORS diagnosis, shared host binding, Windows/Podman networking, camera security
requirements, and destructive reset guidance.

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
- [Railway publication](docs/development/railway-deployment.md)
- [AI collaboration and candidate ownership](docs/development/ai-collaboration.md)
- [Deliberately deferred improvements](docs/future-improvements.md)
- [Original challenge](docs/challenge/Desafio-Elite-Dev-2026.pdf)
