# ADR-008: Testing Strategy

## Status

Accepted

## Context

Tests are optional in the challenge, but the most important requirements involve security, authorization, concurrency, and one-time state changes. Maximizing coverage would compete with the seven-day deadline.

## Decision

- Use pytest and pytest-cov for backend unit and integration tests.
- Test FastAPI through its supported HTTP testing client while keeping business-rule tests independent of HTTP where useful.
- Run persistence integration tests against a dedicated PostgreSQL test database from the Compose environment.
- Use Vitest and Testing Library for focused frontend interactions.
- Use Playwright for one complete browser flow across Organizer, Customer, and Gate roles after the happy path works.
- Prioritize sessions, role and ownership boundaries, active and expired holds, inventory concurrency, payment idempotency, HMAC tampering, wrong-event validation, and duplicate check-in.
- Consider `mutmut` only after the critical Python suite is stable and the mandatory application and documentation are complete.
- Restrict mutation testing to critical backend modules and stop if runtime threatens the deadline.

## Alternatives Considered

### No automated tests

This is permitted by the challenge but leaves the hardest correctness claims unsupported.

### Broad coverage targets from the beginning

They can reward trivial tests and delay the complete product flow.

### SQLite integration tests

They run quickly but do not exercise the PostgreSQL locking and transaction behavior that protects inventory.

### Mutation testing across the whole repository

It can provide useful fault-detection evidence but is expensive and unsuitable before the base suite is stable.

## Consequences

- Test effort follows business risk rather than file count.
- Integration tests require the PostgreSQL test service.
- Browser tests are deliberately few and may run more slowly.
- Mutation results supplement tests; they do not become a delivery gate unless later accepted.

## Revisit When

- Critical behavior is complete ahead of schedule.
- Production deployment or CI introduces different risk and runtime constraints.
- Surviving mutants reveal systematic gaps worth addressing.
