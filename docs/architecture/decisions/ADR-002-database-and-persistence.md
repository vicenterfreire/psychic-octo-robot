# ADR-002: Database and Persistence

## Status

Accepted

## Context

The application must persist users, sessions, events, reservations, and tickets. It must also prevent overselling and duplicate check-in under concurrent requests. Local setup must be repeatable for the evaluator.

## Decision

- Use PostgreSQL as the relational database.
- Run local PostgreSQL through a Compose-compatible `compose.yaml` using Docker or Podman.
- Use synchronous SQLAlchemy 2 for mapping and queries.
- Use Psycopg 3 as the PostgreSQL driver.
- Use Alembic for versioned schema migrations.
- Use normal synchronous FastAPI route functions for database-backed operations so blocking database work runs through FastAPI's thread pool.
- Use explicit short transactions and PostgreSQL row locking for inventory and check-in decisions.
- Use Pydantic models at API boundaries rather than exposing SQLAlchemy models directly.

## Alternatives Considered

### SQLite

It offers the easiest local setup and serializable writes, but PostgreSQL better demonstrates the required concurrent reservation behavior and supports a later hosted deployment without changing database semantics.

### SQLModel

It can reduce duplication between persistence and validation models, but it couples API and database concerns and still needs Alembic for disciplined migrations.

### Raw Psycopg queries

It offers maximum SQL visibility but increases repetitive mapping and migration work for a time-constrained challenge.

### Asynchronous SQLAlchemy

It can increase I/O concurrency but adds `AsyncSession`, async fixture, and transaction-lifecycle complexity. The expected challenge traffic does not justify that cost.

## Consequences

- Concurrency behavior can be tested against the same database engine used by the application.
- PostgreSQL is required for persistence and integration tests. Docker and Podman are supported
  reproducible local providers, but an existing reachable PostgreSQL instance works through the
  same `DATABASE_URL` without code changes.
- The candidate must understand sessions, transactions, locks, migrations, and ORM-generated queries.
- Synchronous database operations must not be called directly from `async def` utility paths that bypass FastAPI's thread-pool handling.
- External Ticketmaster calls must happen outside database transactions.

## Revisit When

- Measured traffic shows the synchronous database model is a bottleneck.
- Deployment constraints require a different PostgreSQL driver or connection-pooling strategy.
- Database access becomes complex enough to justify more explicit SQL for selected paths.
