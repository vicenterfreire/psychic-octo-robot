# ADR-013: Railway Deployment

## Status

Accepted

## Context

The challenge awards an optional differential for a published application. The local Compose and
Quick Tunnel topologies prove the application but do not provide a permanent URL. Publication must
preserve the opaque cookie session, trusted camera HTTPS, PostgreSQL concurrency guarantees, and a
simple evaluator experience without turning deployment into a second application architecture.

Railway was selected by the candidate. The remaining decision is how to divide and connect the
monorepo services.

## Decision

- Deploy `frontend`, `backend`, and Railway PostgreSQL as three services in one Railway project and
  environment.
- Expose only the Nginx frontend service through a permanent Railway HTTPS domain.
- Keep browser API and Swagger requests relative and same-origin. Nginx proxies them to FastAPI
  through `backend.RAILWAY_PRIVATE_DOMAIN` and fixed internal port `8000`.
- Keep FastAPI and PostgreSQL private; they receive no public application domains.
- Use each isolated project directory and Dockerfile as its Railway service root.
- Version service build, pre-deploy, healthcheck, and restart configuration in service-local
  `railway.toml` files. Secrets and cross-service references remain Railway variables.
- Run Alembic and the idempotent evaluation seed in the backend pre-deploy container before the new
  application deployment becomes active.
- Normalize provider-generic PostgreSQL URL schemes to the installed Psycopg 3 SQLAlchemy scheme at
  the configuration boundary.

## Alternatives Considered

### Public Frontend and Public Backend Domains

This avoids an Nginx runtime template but makes the opaque cookie cross-origin. It adds CORS,
SameSite, cookie-domain, build-time API URL, and two-domain verification risk without a requirement
for direct public API access.

### Import the Local Compose File

Railway can import part of a Compose definition, but the current file deliberately contains local
port publication, a local database credential, an ignored backend env file, startup orchestration,
and an optional Cloudflare tunnel. Reusing it remotely would blur local and hosted responsibilities.

### One Container Running Nginx and FastAPI

One public service reduces Railway configuration but requires a multi-process supervisor, couples
independent health and restart lifecycles, and discards the existing isolated Dockerfiles.

### Different Providers for Frontend and Backend

Vercel plus Railway or similar combinations are valid, but they restore cross-origin session and
configuration work while increasing evaluator and operational surface.

### Keep Only Quick Tunnel

Quick Tunnel is random, temporary, public development infrastructure with no stable submission URL
or availability guarantee. It does not earn the hosted differential.

## Consequences

- Evaluators receive one stable HTTPS origin for the application, API, Swagger, session, and phone
  camera.
- FastAPI and PostgreSQL remain off the public network, reducing exposed surface.
- Local host, Compose, and Quick Tunnel behavior remains unchanged because the Nginx template has
  local upstream defaults.
- Railway service names, root directories, config paths, fixed internal ports, and reference
  variables become part of deployment configuration and must remain aligned.
- Migrations have one pre-deploy owner rather than running in every application replica.
- The seeded credentials and Swagger mutation surface are publicly reachable through the gateway;
  only disposable challenge data may be used.
- Railway provides managed TLS and deployment lifecycle primitives, but this challenge deployment
  still lacks full production monitoring, backup policy, rate limiting, and secret rotation.

## Revisit When

- Direct third-party API clients require a separately public backend domain.
- Multiple backend replicas require zero-downtime migration compatibility rules.
- The application handles real users, payments, or confidential event data.
- Railway pricing, limits, networking, or availability no longer fit the project.
- A custom domain, WAF, CDN, or formal observability stack becomes necessary.
