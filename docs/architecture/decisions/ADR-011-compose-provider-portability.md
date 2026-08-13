# ADR-011: Compose Provider Portability

## Status

Accepted

## Context

The checked-in `compose.yaml` is portable, but the project-level npm commands were implemented by a
Windows script that always resolved Podman and `uv`. An evaluator using Docker Desktop could run
`docker compose` manually, but the advertised `npm run app:*` and `npm run db:*` commands would fail
before consulting Docker. The same Podman wrapper also depended on provider-specific status
arguments that are not accepted consistently across Compose implementations.

## Decision

- Keep `compose.yaml` as the single service definition.
- Replace the Podman-named wrapper with `scripts/compose.ps1`.
- Auto-select a running Docker engine first and otherwise the validated Podman engine.
- Allow explicit selection through `COMPOSE_PROVIDER=Docker|Podman`.
- Use Docker's installed Compose plugin without requiring `uv`.
- Preserve the pinned `podman-compose` through `uv` only for the validated Podman path.
- Keep provider-specific Windows/WSL address resolution behind the common wrapper.
- Read bind address, browser-visible host, and published ports from one ignored root `.env` shared
  with direct host development.
- Keep `APP_BIND_ADDRESS` separate from `PUBLIC_HOST`; the former may be `0.0.0.0`, while the latter
  must be a navigable hostname or IPv4 address.
- Write the discovered host database URL to ignored `backend/.env.compose` instead of a
  provider-named file.
- Use only Compose commands supported by both validated providers in the shared lifecycle surface.

## Alternatives Considered

### Document `docker compose` Separately

This leaves the primary project commands misleading: the same npm command would work for one
evaluator and fail for another despite an equivalent running engine.

### Require Docker Only

Docker Compose is widely available, but removing the already validated Podman path would add a new
mandatory local tool and discard the candidate's working environment.

### Require Podman Only

This keeps the existing script small but makes Podman and `uv` accidental requirements even though
the application and Compose file do not depend on them.

### Maintain Two Independent Wrappers

Separate scripts would duplicate lifecycle, health, port, and generated-environment behavior and
would be likely to drift.

## Consequences

- Evaluators can use the same npm lifecycle commands with Docker Desktop or Podman Desktop.
- Docker users do not need Python or `uv` for the container workflow.
- Podman-specific WSL recovery remains available without leaking into the Docker path.
- Automatic selection prefers Docker when both engines are running; users can override this
  explicitly.
- The orchestration wrapper remains Windows PowerShell-specific. Other systems can execute the
  standard Compose file directly.
- Provider portability does not guarantee that Windows exposes a Podman WSL port to the LAN; that
  network boundary is diagnosed separately in `TROUBLESHOOTING.md`.
- Host-process Vite and Uvicorn use the same network settings without requiring nested npm argument
  forwarding.

## Revisit When

- A cross-platform scripting layer provides concrete evaluator value.
- Podman ships a consistently available Compose provider that makes the pinned fallback obsolete.
- Production deployment replaces this local Compose topology.
