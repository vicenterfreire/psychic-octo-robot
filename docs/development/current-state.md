# Current State

## Snapshot

- Date: 2026-08-13.
- Branch: local `main`, based on published commit `14d5d9c` and developed through small local commits.
- Phase: all 24 planned increments are committed; the local application is ready for the
  candidate's final publication review.
- Frontend: React, Vite, and TypeScript application initialized.
- Backend: Python 3.14 and FastAPI application initialized.
- Database: PostgreSQL 17 schema migrated and seeded through Docker/Podman-compatible Compose.
- Authentication: persistent opaque PostgreSQL sessions with role-aware frontend and backend boundaries.
- External catalog: organizer-only Ticketmaster search normalized entirely by the backend.
- Event management: trusted provider snapshots with organizer-owned draft, edit, list, and publication flows.
- Discovery: public and Customer-facing upcoming event search, details, and calculated availability.
- Reservations: ten-minute configurable holds protected by PostgreSQL time and event-row locks.
- Checkout: deterministic approval/decline with atomic, idempotent ticket-row issuance.
- Tickets: versioned HMAC credentials, private QR collection, and minimized bearer sharing views.
- Gate: explicit camera/manual input with atomic valid, invalid, already-used, or wrong-event decisions.
- Automated tests: 30 frontend tests, 48 backend tests, and one Playwright cross-role browser flow.
- Frontend organization: feature-first, with local component/hook directories and explicit shared
  navigation and formatting ownership under ADR-009.
- Styling: Vite CSS Modules isolate feature-owned rules and co-locate responsive behavior; global
  CSS is limited to tokens, resets, page structure, and deliberate shared primitives.
- Code documentation: selective Python docstrings and TypeScript TSDoc/JSDoc explain critical
  security, concurrency, time-authority, integration, and lifecycle contracts.
- Local execution: direct host processes or a healthy three-service Docker/Podman Compose stack;
  production deployment remains deliberately unselected.
- API documentation: generated OpenAPI plus interactive Swagger UI with domain metadata, examples,
  and the configured opaque-cookie security boundary.

## Implemented Foundation

- `compose.yaml` defines healthy PostgreSQL, FastAPI, and built React services with a named
  persistent database volume and explicit dependency order.
- Multi-stage Dockerfiles install the locked backend runtime as a non-root user and serve only the
  Vite build output from Nginx; local environment files never enter either image.
- The PowerShell project hook auto-detects a running Docker or Podman engine and accepts an explicit
  provider override.
- Docker uses its installed Compose plugin without `uv`; Podman uses the validated pinned provider,
  and its WSL address recovery remains isolated behind the common lifecycle commands.
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
- The core and browser hooks create, migrate, seed, and drop only allowlisted isolated PostgreSQL databases.
- The test-report hook emits ignored Vitest JSON, pytest JUnit XML, Playwright JSON, and one aggregate summary.
- Swagger UI is served at `/docs`, its OpenAPI source at `/openapi.json`, and full-stack startup
  prints the reachable documentation URL.
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
- Gate-only routes list published events and validate camera-scanned or manually entered credentials without exposing ticket state before HMAC verification.
- Ticket validation locks the exact ticket row, classifies revoked/event/usage state, and commits the Gate user with the PostgreSQL timestamp.
- The Gate camera remains off until explicit activation, lazily loads the QR decoder, prefers the environment camera, and stops on the first decoded credential.
- Camera cancellation, event changes, pending validation, and route cleanup stop active scanner controls; duplicate callbacks cannot create duplicate validation requests.
- Insecure origin, permission, hardware, browser-support, and startup failures keep manual entry
  visible with specific recovery guidance.
- The Gate interface presents all four outcomes with large, distinct feedback and keeps manual entry independent of camera support.
- The Playwright flow updates the seeded event as Organizer, purchases one ticket as Customer, and proves first-use/duplicate-use Gate outcomes without contacting Ticketmaster.
- The optional `mutmut` experiment is documented but deferred because the available `uv` and `pip` routes could not reach PyPI; no unresolved dependency was added.
- The README is a concise evaluator entry point containing setup, full-stack execution, seeded
  credentials, and links to the focused troubleshooting and project documentation.
- The AI collaboration disclosure separates AI-assisted work, candidate-owned decisions and actions, shared review, and versioned intermediate artifacts.

## Validated Environment

- Node.js 22.21.0 and npm 10.9.4.
- `uv` 0.12.3 with managed CPython 3.14.7.
- Podman Desktop 6.0.2 with a running WSL machine.
- PostgreSQL 17.10 from `postgres:17-alpine`.
- `podman-compose` 1.6.0 executed in an isolated `uvx` environment.
- Playwright 1.62.1 with Chrome for Testing 151.0.7922.34.
- Nginx 1.28.3 in the static frontend image.

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
- All 48 backend tests pass with 95% coverage of the current backend.
- All 30 frontend tests pass, and frontend formatting, linting, type checking, and production build
  succeed.
- The Chromium cross-role test passes at a 360-pixel viewport through Organizer edit, Customer
  approval, issued-ticket retrieval, valid Gate entry, and duplicate rejection, with width checks
  at each role surface.
- Both application images build from their committed lockfiles, and the three Compose services
  become healthy after the backend applies the current migration and idempotent seed.
- The same cross-role Playwright scenario passes against an isolated three-service Compose project;
  its dedicated volume is removed afterward while `elite_dev` remains untouched.
- The full-stack hook detects missing Windows localhost forwarding, aligns the frontend build and
  CORS origin with the current Podman machine address, and prints reachable URLs.
- `npm test` leaves `elite_dev` untouched and drops `elite_dev_test`; `npm run test:e2e` drops `elite_dev_e2e` after completion.
- Removing HMAC signature comparison temporarily makes the focused tampering test fail; restoring it returns all three signing tests to passing.
- Generated Vitest JSON, pytest JUnit XML, Playwright JSON, and summary JSON parse successfully and report no failures.
- Mutation scope, exclusions, survivor policy, disposable-database requirement, 20-minute total limit, and 30-second per-mutant limit are recorded for a later network-enabled run.
- Live browser review confirmed Gate login, event loading, camera-off-by-default behavior, explicit
  permission request on a secure origin, safe cancellation, and immediately available manual
  fallback.
- Live HTTP LAN review confirmed that the browser reports an insecure context before ZXing loads;
  the Gate screen now disables camera start with HTTPS-specific guidance rather than presenting a
  generic decoder failure.
- The browser environment had no physical camera, so optical capture remains a short device-level evaluator check; automated interaction tests exercise decoded QR submission, duplicate callback suppression, and all four authoritative outcomes.
- Final dependency setup verification passed from both lockfiles without network access or tracked
  dependency changes.
- Final `db:prepare` reused healthy PostgreSQL, found the migration at head, and inserted no
  duplicate seed records.
- Final formatting, linting, strict type checking, frontend/backend builds, Alembic drift check, and
  30-frontend/48-backend/1-browser regression suites all passed.
- All local Markdown links resolve, and all five challenge pages were extracted, rendered, visually
  reviewed, and cross-checked against the evaluator documentation.

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
- Camera access depends on a secure browser context, user permission, and usable hardware; manual validation remains the permanent fallback.
- Ticket revocation state is persisted and presented, but no cancellation or administrative revocation command exists yet.
- The initial signing format has no key identifier or verification key ring, so changing `TICKET_HMAC_SECRET` invalidates existing tokens.
- Approved reservations and issued tickets are final; cancellation and refunds remain deferred.
- The Compose and isolated-test hooks are Windows-specific; other systems can use the standard
  `compose.yaml` and equivalent commands with their installed Compose provider.
- The local Compose topology exposes HTTP ports, embeds the public API URL at build time, runs one
  backend replica, and applies migrations during startup; it is not a production topology.
- The backend test client still emits an upstream FastAPI/Starlette deprecation warning.
- Swagger UI operates against the real configured API and can mutate local data; production access
  control or disabling the route must be decided with the eventual deployment topology.
- Production hosting, TLS, managed secrets, separate migration ownership,
  monitoring, backup, and rollback remain deferred.

## Delivery Status

The mandatory application, concise evaluator workflows, full-stack Compose execution, and
interactive API documentation are complete, including the portability/mobile hardening increment.
The same `DATABASE_URL` continues to support an already-running PostgreSQL instance without
containers. The candidate retains responsibility for final review, public GitHub publication, and
challenge-form submission. Production deployment remains an optional, deliberately deferred
improvement, so no hosted URL is provided.
