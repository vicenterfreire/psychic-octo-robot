# ADR-010: Local Full-Stack Containers

## Status

Accepted; browser routing amended by ADR-012

## Context

The evaluator needs one reproducible command that starts PostgreSQL, the FastAPI API, and the
built React application. The existing workflow starts only PostgreSQL in Podman and runs both
applications directly on the host. Production hosting, TLS termination, and a deployment provider
remain outside the mandatory scope.

## Decision

- Keep the direct host-development workflow and add a separate full-stack Compose workflow.
- Build the backend from `uv.lock` in a multi-stage image and run FastAPI as a non-root user.
- Build the React application with its configured public API URL and serve only the generated
  static files from Nginx.
- Originally keep the browser-to-API request explicit through published host ports, with
  credentialed CORS as the integration boundary and no Nginx API proxy. ADR-012 amends only this
  routing choice for same-origin container and temporary HTTPS camera evaluation.
- Make PostgreSQL health gate backend startup and make backend health gate frontend startup.
- Apply Alembic migrations and the idempotent evaluation seed before the single local backend
  process starts.
- Load backend secrets at runtime from the untracked `backend/.env`; do not copy environment files
  into either image.
- Treat this as a local evaluation topology, not as a production deployment architecture.

## Alternatives Considered

### Run Vite and Uvicorn Development Servers in Containers

This would resemble host development but would ship source-oriented reload processes instead of
testing the same frontend build artifact an evaluator receives.

### Reverse Proxy `/api` Through Nginx

This would provide a same-origin browser topology and reduce CORS configuration, but it would add
proxy routing and hide a boundary the project already implements and tests. It becomes worthwhile
when a real production domain and TLS terminator are selected.

### Use Only Host Processes With a Containerized Database

This remains the fastest development loop, but it requires three setup paths and does not satisfy
the requested one-command full-stack evaluation path.

### Model a Production Orchestrator Now

Kubernetes, a cloud provider, managed secrets, TLS, and multiple backend replicas would require
deployment decisions unrelated to completing the local challenge flow.

## Consequences

- An evaluator can build and start the complete local application with one project command.
- The frontend image contains only static build output, and the backend image contains locked
  runtime dependencies without development tests or local secrets.
- Before ADR-012, changing the public host or published backend port required rebuilding the
  frontend because Vite substituted `VITE_API_URL` at build time. The amended container build uses
  relative `/api`; direct host development still injects its explicit API URL.
- Running migrations in backend startup is intentionally limited to this single-replica local
  topology. A production deployment should use a separate migration job.
- HTTP local execution requires `SESSION_COOKIE_SECURE=false`; production must use HTTPS, secure
  cookies, managed secrets, and topology-specific CSRF review.
- The project lifecycle wrapper supports Docker and Podman as recorded in ADR-011; neither engine
  is an application runtime dependency.
- A Podman WSL address fallback is reachable for evaluation but is not a browser secure context;
  camera testing should use direct `localhost` development or HTTPS while manual Gate entry remains
  available.

## Revisit When

- The selected Railway provider, public domain, or TLS termination strategy requires changing this
  local topology rather than complementing it through ADR-013.
- Multiple backend replicas may start concurrently.
- Runtime-configurable frontend endpoints or a same-origin reverse proxy become necessary.

ADR-012 records why phone-camera evaluation made the last condition concrete while preserving this
ADR's local-only and single-replica boundaries. ADR-013 adds a separate Railway topology with a
pre-deploy migration owner and does not replace local Compose.
