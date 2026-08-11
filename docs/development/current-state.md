# Current State

## Snapshot

- Date: 2026-08-11.
- Branch: local `main`, based on published commit `14d5d9c` and developed through small local commits.
- Phase: authoritative manual gate validation complete; camera-based QR reading is next.
- Frontend: React, Vite, and TypeScript application initialized.
- Backend: Python 3.14 and FastAPI application initialized.
- Database: PostgreSQL 17 schema migrated and seeded through Podman.
- Authentication: persistent opaque PostgreSQL sessions with role-aware frontend and backend boundaries.
- External catalog: organizer-only Ticketmaster search normalized entirely by the backend.
- Event management: trusted provider snapshots with organizer-owned draft, edit, list, and publication flows.
- Discovery: public and Customer-facing upcoming event search, details, and calculated availability.
- Reservations: ten-minute configurable holds protected by PostgreSQL time and event-row locks.
- Checkout: deterministic approval/decline with atomic, idempotent ticket-row issuance.
- Tickets: versioned HMAC credentials, private QR collection, and minimized bearer sharing views.
- Gate: published-event selection and atomic valid, invalid, already-used, or wrong-event decisions.
- Automated tests: 21 frontend tests and 46 backend tests, including PostgreSQL concurrent check-in integration.
- Deployment: not selected.

## Implemented Foundation

- `compose.yaml` defines a healthy PostgreSQL service with a named persistent volume.
- The PowerShell project hook resolves the candidate's Podman Desktop executable even when the current process has a stale `PATH`.
- The hook runs a pinned Compose provider through `uvx` and adapts to missing WSL localhost forwarding without changing global Podman settings.
- SQLAlchemy models represent users, sessions, catalog snapshots, events, reservations, and tickets.
- Named database constraints protect roles, states, normalized values, quantities, money, timestamps, ownership references, session digests, and ticket usage/revocation shape.
- Alembic revision `91ec7f95d3b1` is the current schema head and adds coherent ticket revocation timestamps.
- The idempotent seed creates one organizer, two customers, one gate user, one Ticketmaster-style snapshot, and one published event.
- Seed passwords use the accepted Argon2id implementation and are never stored in plaintext.
- Backend runtime dependencies are locked and `requirements.txt` has been regenerated from `uv.lock`.
- Login, current-session, and logout routes use fixed seven-day opaque sessions.
- Raw session credentials remain only in HTTP-only cookies; PostgreSQL stores SHA-256 digests.
- Argon2id password verification uses the shared seed utility and dummy verification for unknown identities.
- Reusable backend role and ownership checks establish the authorization boundary for later resource routes.
- The frontend restores sessions through TanStack Query and separates organizer, customer, and gate navigation.
- The test-report hook emits ignored machine-readable JSON/XML results for both suites.
- The Ticketmaster client keeps `apikey` server-side, enforces a timeout and bounded result size, validates upstream JSON, and returns a small provider-normalized HTTP contract.
- The Organizer interface supports explicit search, result selection, empty/error recovery, and provider source links.
- Event creation refetches the selected provider item on the backend, verifies its identifier, and persists the raw provider response as an immutable snapshot.
- Organizer event routes scope reads and row locks by the authenticated owner and return not found for foreign identifiers.
- Event editing validates future timezone-aware dates, integer-minor-unit prices, positive capacities, and capacity floors imposed by active or approved reservations.
- The Organizer interface creates drafts, lists local events, edits details, and publishes through explicit actions with TanStack Query invalidation.
- Public discovery queries only upcoming published local events and searches local name, venue, and city without contacting Ticketmaster.
- Public responses exclude organizer identity, lifecycle status, provider links, and raw snapshot data.
- Availability subtracts approved reservations and unexpired pending holds using PostgreSQL time in the discovery query.
- Public and authenticated Customer screens share responsive listing and detail components while preserving their navigation boundaries.
- Customer-only reservation routes create and restore owned holds without disclosing another customer's identifiers.
- Reservation creation locks the upcoming published event, expires observed stale rows, recalculates committed quantity, and rejects insufficient inventory atomically.
- Private reservation responses are non-cacheable and expose the database deadline plus server time.
- The Customer quantity form redirects to a reload-safe hold screen with a server-offset countdown and expired-hold recovery.
- Checkout accepts explicit approved/declined simulation outcomes without collecting financial data.
- Payment takes locks in event-then-reservation order, rechecks PostgreSQL expiry, and makes the first terminal state immutable.
- Approval changes the reservation and inserts one uniquely numbered ticket per unit in the same transaction.
- Decline and expiry issue no tickets and make held inventory immediately available.
- The Customer screen presents confirmation, refusal, expiration, retry, and restored terminal states.
- A dedicated ticket signer emits deterministic `v1` HMAC-SHA-256 credentials without personal data and verifies signatures with a constant-time comparison.
- Customer ticket reads are owner-scoped, approved-reservation-only, and non-cacheable; invalid, tampered, unknown, and foreign credentials reveal no ticket.
- The private “My Tickets” screen renders SVG QR credentials, while public bearer links expose only presentation state and event context.
- Gate-only routes list published events and validate manually entered credentials without exposing ticket state before HMAC verification.
- Ticket validation locks the exact ticket row, classifies revoked/event/usage state, and commits the Gate user with the PostgreSQL timestamp.
- The Gate interface presents all four outcomes with large, distinct feedback and keeps manual entry independent of camera support.

## Validated Environment

- Node.js 22.21.0 and npm 10.9.4.
- `uv` 0.12.3 with managed CPython 3.14.7.
- Podman Desktop 6.0.2 with a running WSL machine.
- PostgreSQL 17.10 from `postgres:17-alpine`.
- `podman-compose` 1.6.0 executed in an isolated `uvx` environment.

## Validation Result

- PostgreSQL starts healthy through the project hook.
- Reset removes only the project volume and recreates an empty database.
- Alembic upgrades an empty database to the current head.
- `alembic check` reports no schema drift.
- The first seed inserts all evaluation records and the second inserts none.
- Direct database inspection confirmed seven tables, 36 constraints, four Argon2id hashes, and the published event.
- PostgreSQL rejects a reservation with quantity zero.
- Login was verified for valid, unknown, and wrong-password credentials.
- Session restoration, expiration, logout revocation, cookie attributes, role denial, and ownership denial are covered.
- A live HTTP smoke test confirmed Gate login, HTTP-only cookie restoration, `204` logout, and subsequent `401` denial.
- Ticketmaster success, empty, missing-key, rejected-key, quota, timeout, unavailable, malformed, and role-denial paths are covered without a live credential.
- Provider detail snapshots, identifier matching, local persistence, ownership, invalid input, capacity reduction, and publication paths are covered.
- Discovery integration covers draft/past exclusion, case-insensitive search, wildcard escaping, response minimization, event details, and active/expired availability.
- Reservation integration confirms active-hold availability, lazy expiration, ownership, role denial, insufficient inventory, and exact ten-minute database deadlines.
- Two simultaneous four-ticket holds against capacity five consistently produce one success and one conflict, leaving four active units.
- Approved, declined, expired, repeated, contradictory, foreign-owner, invalid-outcome, and concurrent payment paths are covered.
- Two simultaneous approvals of one three-unit hold both return the approved result while PostgreSQL contains exactly ticket numbers 1, 2, and 3.
- Ticket tests cover deterministic signing, malformed and unsupported versions, identifier/signature tampering, unknown signed identifiers, missing secrets, role and ownership boundaries, response minimization, and stored revocation state.
- Gate tests cover role denial, missing signing configuration, post-start event selection, malformed/tampered/unknown/revoked credentials, wrong event, repeated usage, and PostgreSQL concurrency.
- Two simultaneous validations of one unused ticket consistently produce exactly one `valid` and one `already_used` result.
- A live Ticketmaster search returned 12 normalized results, and a live detail fetch confirmed identifier matching and credential absence from the snapshot body.
- A live local HTTP query returned only the seeded published event with the expected availability and no management fields.
- All 46 backend tests pass with 95% coverage of the current backend.
- All 21 frontend tests pass, and frontend formatting, linting, type checking, and production build succeed.
- Generated Vitest JSON, pytest JUnit XML, and summary JSON parse successfully and report no failures.
- Live browser review confirmed Gate login, event loading, manual invalid-token feedback, no console errors, and no horizontal overflow at desktop or 390-pixel mobile width.

## Known Limitations

- Event, reservation, and private ticket ownership are enforced in their backend resource queries.
- Frontend route guards improve navigation but are not security controls.
- Expired and revoked session rows are not cleaned automatically.
- Login rate limiting, session rotation/device management, and topology-specific CSRF hardening remain deferred.
- Search selection remains transient until creation; created event snapshots and local details are persistent.
- Repeated catalog searches are not cached; each explicit submission consumes one provider request.
- Discovery returns at most 50 upcoming events without pagination or advanced filters.
- Displayed availability is a read snapshot; only a successful reservation transaction guarantees a temporary quantity.
- Expiration is lazy: stale pending rows can retain that stored status until a relevant operation observes them, but stop consuming inventory at the deadline.
- Payment is an explicit deterministic simulation; it has no provider, card input, webhook, reconciliation, refund, or fraud behavior.
- Camera-based QR reading is not implemented yet; the complete manual validation path remains available.
- Ticket revocation state is persisted and presented, but no cancellation or administrative revocation command exists yet.
- The initial signing format has no key identifier or verification key ring, so changing `TICKET_HMAC_SECRET` invalidates existing tokens.
- Approved reservations and issued tickets are final; cancellation and refunds remain deferred.
- The Podman hook is Windows-specific; other systems can use the standard `compose.yaml` with their installed Compose provider.
- The backend test client still emits an upstream FastAPI/Starlette deprecation warning.
- Deployment topology and production secrets remain deferred.

## Next Commit

`feat(gate): add camera-based QR reading`
