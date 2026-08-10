# ADR-001: Technology Stack and Repository

## Status

Accepted

## Context

The challenge requires React and permits Python for the backend. The application must be completed in seven calendar days, demonstrated locally, and explained by the candidate. The repository currently contains no application code.

Dependency setup must be reproducible on Windows while avoiding multiple manually maintained Python dependency lists.

## Decision

- Use React, Vite, and TypeScript for a client-rendered single-page application.
- Use Python 3.14 and FastAPI for a JSON REST API.
- Keep frontend and backend in one repository but in independent `frontend/` and `backend/` projects.
- Use npm for frontend dependencies and `uv` for the Python environment and dependencies.
- Commit `pyproject.toml` and `uv.lock` as the Python dependency sources of truth.
- Generate and commit `requirements.txt` from `uv.lock` for evaluator compatibility. Never edit it manually.
- Use a root `compose.yaml` for PostgreSQL and root documentation for shared workflows.
- Do not introduce Git worktrees or a shared cross-language package without a concrete need.

## Alternatives Considered

### Next.js full stack

It would reduce the number of processes and add deployment integrations, but server rendering is not required and framework-specific backend boundaries would make the challenge architecture less explicit.

### React with Node.js

It would use one language across the repository, but the candidate selected Python and FastAPI and wants to demonstrate that stack.

### React with Django or Spring Boot

Both are capable, but their larger framework surface would add concepts not required by the challenge.

### pip requirements files only

This is familiar but does not provide the same cross-platform lock and project workflow. Maintaining both `uv.lock` and a handwritten `requirements.txt` would create conflicting dependency sources.

### Poetry

It provides dependency management and locking but adds a packaging-oriented workflow when `uv` can manage the environment, Python version, lockfile, and exports with fewer project-specific concepts.

## Consequences

- Frontend and backend have clear responsibilities and can be explained separately.
- Two language toolchains must be installed and documented.
- Browser-to-API cookie and CORS behavior must be configured carefully.
- The generated `requirements.txt` must be refreshed and checked whenever `uv.lock` changes.
- Python 3.14 compatibility must be verified for every selected dependency.

## Revisit When

- Server rendering or a unified deployment becomes a real requirement.
- A shared schema-generation workflow would remove demonstrated duplication.
- Python 3.14 prevents use of a necessary supported dependency.
