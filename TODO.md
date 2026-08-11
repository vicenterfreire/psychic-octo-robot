# Development Plan

## Current Status

The requirements, architecture decisions, runnable full-stack foundation, PostgreSQL persistence layer, opaque-session authentication, and organizer Ticketmaster search are complete. Local event management and later business workflows have not been implemented yet. No later planned task is considered done until its changes are validated, staged, and committed locally.

Commit progress: 5 of 15 planned increments complete; 10 remain.

The local `main` branch is based on published commit `14d5d9c`. Local project commits remain unpushed until the candidate chooses to publish them.

## Accepted Architecture Direction

- Frontend: React, Vite, and TypeScript.
- Backend: Python 3.14 and FastAPI.
- Database: PostgreSQL.
- Local database runtime: Podman with a Compose-compatible `compose.yaml` workflow.
- External catalog: Ticketmaster Discovery API.
- Inventory model: quantity-based general admission; no seat map in the mandatory scope.
- Authentication: persistent opaque sessions stored in PostgreSQL and referenced by an HTTP-only cookie.
- Ticket authenticity: persistent, versioned HMAC-signed ticket tokens.
- Reservation model: temporary inventory holds with an explicit expiration time.
- Testing: risk-focused automated tests; mutation testing only if the mandatory flow and critical tests are complete and the deadline remains safe.
- Deployment provider: deliberately deferred until the mandatory end-to-end flow is complete.

Additional accepted implementation direction:

- Python dependency management: `uv`, `pyproject.toml`, and committed `uv.lock`.
- Python compatibility export: generated and committed `requirements.txt`; never maintained manually.
- Persistence: synchronous SQLAlchemy 2, Psycopg 3, and Alembic.
- Password hashing: Argon2id through `pwdlib[argon2]`.
- Frontend state: TanStack Query for server state and local state for forms and countdowns; no general global state store.
- Session lifetime: fixed seven days, no sliding renewal, immediate logout revocation.
- Reservation lifetime: configurable ten-minute default using PostgreSQL time and lazy expiration; no background worker initially.
- Test tools: pytest/pytest-cov, Vitest/Testing Library, Playwright, and conditional focused `mutmut` use.

## Resolved Decision Gate

The initial RED decisions were accepted by the candidate and are recorded in `docs/architecture/decisions/`:

- ADR-001: technology stack and repository.
- ADR-002: database and persistence.
- ADR-003: external catalog and inventory model.
- ADR-004: session authentication and authorization.
- ADR-005: password hashing.
- ADR-006: temporary reservation lifecycle.
- ADR-007: ticket authenticity, sharing, and validation.
- ADR-008: testing strategy.

---

## Done - docs(project): establish requirements and architecture decisions

### Goal

Create the persistent project knowledge base and record all accepted decisions before implementation.

### Implemented

- Aligned the previously unborn local `main` branch with the published `origin/main` history without rewriting the remote commit.
- Documented functional requirements, non-functional requirements, constraints, ambiguities, and explicit exclusions.
- Resolved the initial RED decision gate with candidate approval.
- Created eight ADRs covering stack, repository organization, persistence, external catalog, inventory, authentication, password hashing, reservation lifecycle, ticket security, and testing.
- Created the architecture overview, domain overview, current-state document, development workflow, and future-improvements backlog.
- Replaced the placeholder README with an accurate project introduction.
- Recorded `requirements.txt` as a generated compatibility export from `uv.lock`.
- Reviewed and refined this development plan.

### Validation

- Compared the consolidated requirements against the complete challenge PDF.
- Confirmed that all eight ADRs contain the required headings and `Accepted` status.
- Confirmed that all local Markdown links resolve.
- Confirmed that Markdown files contain no trailing whitespace.
- Confirmed that no application code or dependency manifest was introduced.
- Confirmed that local `main` is based on published commit `14d5d9c`.
- Recorded that the current Codex process has not inherited the candidate's newly updated tool `PATH`; tool versions will be revalidated in the next technical increment.

### Expected Result

The repository contains a reviewed, traceable, and interview-defensible plan with no application implementation yet.

### Next

Initialize the React/Vite/TypeScript frontend and Python/FastAPI backend workspace.

---

## Done - chore(project): initialize the full-stack workspace

### Goal

Create the smallest runnable foundation for the frontend and backend.

### Implemented

- Configured the root workspace and shared development commands.
- Initialized the React, Vite, and TypeScript frontend under `frontend/`.
- Initialized the Python and FastAPI backend under `backend/`.
- Configured the accepted Python dependency-management workflow.
- Generated `requirements.txt` from `uv.lock` as a committed compatibility artifact.
- Added formatting, linting, type-checking, test, build, and development commands.
- Added environment examples without committing secrets.
- Established feature-oriented module boundaries without introducing unnecessary abstraction layers.
- Configured local frontend-to-backend communication with credentialed requests.
- Added a minimal health contract and frontend status interface to prove the integration boundary.

### Validation

- Started both applications together and confirmed their expected HTTP responses.
- Confirmed the backend health payload and explicit credentialed CORS headers.
- Passed frontend Prettier, Oxlint, TypeScript, Vitest, and Vite production build checks.
- Passed backend lock verification, Ruff formatting and linting, strict mypy, pytest with branch coverage, and package build checks.
- Confirmed that a fresh `uv.lock` export has the same dependency content as the committed `requirements.txt`.
- Confirmed that environment examples contain no secrets and local artifacts are ignored.

### Expected Result

Both applications start locally and expose minimal health or placeholder interfaces.

### Next

Model PostgreSQL persistence and add reproducible evaluation seed data.

---

## Done - feat(database): model persistence and seed evaluation data

### Goal

Create the PostgreSQL schema required by the complete workflow and make evaluator setup reproducible.

### Implemented

- Added a Compose-compatible PostgreSQL 17 service with a named volume and health check.
- Added a Windows Podman hook that resolves stale `PATH`, runs pinned Compose through `uvx`, and adapts to WSL networking.
- Configured synchronous SQLAlchemy 2, Psycopg 3, Alembic, and Argon2id seed hashing.
- Modeled users, sessions, external catalog snapshots, events, reservations, tickets, and ticket usage.
- Represented reservation status and expiration explicitly.
- Stored monetary values as integer minor units.
- Added ownership, role, uniqueness, capacity, status, normalization, digest, and timestamp constraints.
- Created and reviewed initial migration `2db7467132b0`.
- Seeded one organizer, two customers, one gate user, one published event, and one stable Ticketmaster-style snapshot.
- Documented database startup, migration, reset, seed, credentials, and troubleshooting behavior.
- Added PostgreSQL integration tests for seed correctness, idempotency, and quantity constraints.

### Validation

- Started PostgreSQL through the project Podman Compose hook and confirmed healthy status.
- Deleted and recreated only the project volume, then applied migrations to the empty database.
- Ran the seed twice: the first inserted all required data and the second inserted zero rows.
- Confirmed `alembic check` reports no metadata drift and the database is at head.
- Inspected seven tables, 35 constraints, four Argon2id hashes, and the published seed event.
- Passed Ruff, strict mypy, and four backend tests against PostgreSQL with 93% current backend coverage.

### Expected Result

A fresh PostgreSQL database can be started, migrated, and populated with the required evaluation data.

### Next

Implement login, restoration, logout, persistent opaque sessions, and role boundaries.

---

## Done - feat(auth): implement persistent opaque-session authentication

### Goal

Authenticate the three required roles without requiring users to log in again every time they reopen the site.

### Implemented

- Centralized Argon2id password hashing and verification with the effective `m=65536,t=3,p=4` parameters and dummy verification for unknown identities.
- Generated 256-bit opaque session credentials and stored only their SHA-256 digests in PostgreSQL.
- Added fixed seven-day expiration, database-time validation, immediate current-session revocation, and no sliding renewal.
- Set persistent HTTP-only, `SameSite=Lax` cookies with environment-controlled `Secure` behavior and no-store authentication responses.
- Added login, current-session, and logout endpoints backed by synchronous database dependencies.
- Added reusable backend role and ownership authorization checks for future resource endpoints.
- Built login, session restoration, role-protected routes, and logout flows with TanStack Query.
- Added a local test-report hook that emits Vitest JSON, pytest JUnit XML, and a summary JSON under ignored `.artifacts/`.

### Validation

- Passed frontend formatting, linting, strict TypeScript, three interaction tests, and the Vite production build.
- Passed backend Ruff formatting/linting, strict mypy, and 11 tests against PostgreSQL with 93% coverage.
- Confirmed valid login, equal invalid-credential responses, persistent restoration, expiration, logout revocation, and production `Secure` cookie behavior.
- Confirmed the response never exposes the raw credential and PostgreSQL contains only its digest.
- Confirmed role and ownership denial behavior and frontend cross-role redirection.
- Parsed the generated JSON/XML reports and confirmed both test suites report no failures.
- Exercised the live HTTP server: login as Gate, HTTP-only cookie restoration, `204` logout, and subsequent `401` access denial.

### Expected Result

Each seeded user can remain authenticated for the accepted lifetime and access only the functionality allowed for its role.

### Next

Integrate organizer-only Ticketmaster catalog search without exposing the provider credential.

---

## Done - feat(catalog): integrate the Ticketmaster event catalog

### Goal

Allow organizers to search external source material while keeping provider credentials on the backend.

### Implemented

- Added a synchronous server-side Ticketmaster Discovery client with a five-second default timeout and a fixed 12-result limit.
- Promoted `httpx` to a locked runtime dependency and regenerated the derived `requirements.txt`.
- Kept `TICKETMASTER_API_KEY` in backend-only environment configuration and out of all browser requests and responses.
- Added an organizer-only `GET /api/catalog/events` endpoint with normalized and trimmed search input.
- Reduced upstream data to provider, external identifier, name, description, one safe image URL, and source URL.
- Mapped missing/rejected credentials, quota, timeout, transport, invalid JSON, empty results, and upstream failure into stable outcomes.
- Built an intentional Organizer catalog interface with explicit search, responsive result cards, empty/error states, external source links, and transient selection.

### Validation

- Reviewed the official Ticketmaster Discovery v2 event-search, authentication, response, and rate-limit contracts.
- Passed 17 focused backend catalog cases using `httpx.MockTransport`, including success, normalization, safe URLs, input validation, empty, configuration, credentials, quota, timeout, unavailable, malformed, and authorization paths.
- Passed all 28 backend tests against PostgreSQL with 95% coverage.
- Passed all six frontend tests, including search, selection, empty, stable error, and browser-request credential checks.
- Passed frontend/backend formatting, linting, strict type checking, builds, lock verification, and Alembic drift detection.
- Confirmed through a live local HTTP server that an authenticated Organizer receives a stable `503` when no Ticketmaster key is configured.
- Did not execute a live Ticketmaster success request because no provider credential is stored in the workspace.

### Expected Result

An organizer can search Ticketmaster and select an external catalog item without exposing the API credential.

### Next

Persist the selected source snapshot and implement organizer-owned local event creation, editing, listing, and publication.

---

## Done - feat(events): implement organizer event management

### Goal

Allow organizers to create and manage local events derived from Ticketmaster data.

### Implemented

- Persist a snapshot of the selected Ticketmaster item.
- Let the organizer define date, location, total capacity, and price.
- Support the minimal event lifecycle required for creation, editing, and publication.
- Allow organizers to list and edit only their own events.
- Reject invalid dates, prices, capacities, and unsafe capacity reductions.
- Build the minimal organizer event screens without adding an analytics dashboard.

### Validation

- Created an event from a backend-verified Ticketmaster detail and persisted its immutable raw snapshot.
- Confirmed list, update, and publication ownership enforcement against PostgreSQL.
- Confirmed invalid local details and capacity reductions below active or approved reservations are rejected.
- Confirmed a newly created event remains a draft until explicit publication with a future start.
- Confirmed later provider changes do not modify an existing source snapshot or trigger another provider call.
- Passed eight frontend tests and 32 backend tests, including PostgreSQL event-management integration.
- Passed formatting, linting, strict type checking, production builds, lock verification, and Alembic drift detection.
- Generated and parsed successful Vitest JSON, pytest JUnit XML, and summary JSON reports.

### Expected Result

An organizer can create, edit, and publish a locally owned event based on Ticketmaster content.

### Next

Expose only published local events through customer discovery and basic text search.

---

## Done - feat(discovery): implement published event discovery

### Goal

Let customers find published events and inspect the information required to start a reservation.

### Implemented

- Listed only upcoming published local events through public PostgreSQL-backed endpoints.
- Added case-insensitive basic text search over event name, venue, and city.
- Returned minimized list/detail contracts with date, location, price, image, and current availability.
- Calculated availability from approved quantity and unexpired pending holds using PostgreSQL time.
- Built responsive public and authenticated Customer listing/detail screens.
- Preserved advanced filters and pagination for the optional backlog.

### Validation

- Confirmed drafts and past events never appear in public list or detail responses.
- Confirmed case-insensitive search, whitespace normalization, literal wildcard handling, and empty states.
- Confirmed expired and declined reservations do not reduce displayed availability.
- Confirmed the public response excludes Organizer, lifecycle, provider-link, and raw snapshot fields.
- Passed 11 frontend tests and 33 backend tests with successful JSON/XML reports.
- Passed formatting, linting, strict type checking, lock verification, builds, and Alembic drift detection.
- Exercised live Ticketmaster search/detail calls without exposing the credential and a live local discovery HTTP query against the seed.

### Expected Result

A customer can find a published event and proceed to quantity selection.

### Next

Create temporary inventory holds with PostgreSQL-time expiry and transactional capacity protection.

---

## Done - feat(reservations): implement temporary inventory holds

### Goal

Protect the customer's selected quantity for a short payment window without overselling the event.

### Implemented

- Create pending reservations with a configurable expiration timestamp.
- Use PostgreSQL time and transactional locking as the source of truth for expiration and capacity.
- Expire stale pending reservations lazily during availability and reservation operations, leaving payment observation for its own increment.
- Reserve quantity atomically while accounting for sold tickets and unexpired holds.
- Reject requests that exceed the currently available quantity.
- Expose the reservation deadline to the frontend.
- Build a visible countdown and clear expired-reservation recovery flow.
- Avoid queues or background workers in the initial implementation.

### Validation

- Confirmed that an active hold reduces availability and an expired hold immediately stops consuming it.
- Confirmed Customer ownership, role denial, insufficient inventory, and non-cacheable private responses.
- Ran simultaneous four-ticket attempts against capacity five: one succeeded, one conflicted, and active quantity remained four.
- Confirmed that the frontend corrects a skewed browser clock from the server timestamp and refetches when the displayed deadline elapses.
- Passed 14 frontend tests and 35 backend tests with successful JSON/XML reports and 94% backend coverage.

### Expected Result

A customer receives a time-limited hold, and concurrent customers cannot reserve more than the remaining inventory.

### Next

Simulate deterministic payment and atomically finalize, decline, or expire the protected reservation.

---

## feat(checkout): simulate payment and finalize reservations

### Goal

Convert a valid temporary hold into tickets or release it after a declined or expired payment.

### Planned

- Add deterministic approved and declined payment scenarios.
- Verify that the pending reservation still belongs to the customer and has not expired.
- Atomically convert an approved reservation into a paid reservation and create its tickets.
- Mark a declined reservation accordingly and release its held quantity immediately.
- Return a clear expired state when payment arrives after the deadline.
- Make repeated payment submissions idempotent.
- Build confirmation, refusal, expiry, and retry interfaces.

### Validation

- Exercise approved, declined, expired, repeated, and concurrent payment attempts.
- Confirm that tickets are generated only once for an approved reservation.
- Confirm that declined and expired reservations restore availability.

### Expected Result

The payment simulation completes the reservation safely while preserving the temporary-hold customer experience.

---

## feat(tickets): issue HMAC-signed QR tickets and sharing links

### Goal

Give customers persistent, presentable, shareable, and verifiable tickets.

### Planned

- Create one ticket per approved quantity.
- Define and document a compact, versioned HMAC token format.
- Use a dedicated application secret and constant-time signature verification.
- Keep personal data out of the token and QR payload.
- Generate QR images for issued tickets.
- Add the customer "My Tickets" area.
- Add bearer sharing links that reveal only the minimum ticket information.
- Keep usage and revocation state in PostgreSQL.

### Validation

- Confirm that valid tokens survive page reloads and can be shared.
- Reject modified identifiers, signatures, and unsupported token versions.
- Confirm that personal data is absent from QR payloads and public sharing responses.

### Expected Result

Customers can view and share persistent QR tickets that cannot be fabricated without the HMAC secret.

---

## feat(gate): validate ticket codes exactly once

### Goal

Implement the authoritative gate-validation workflow before adding camera integration.

### Planned

- Let gate users select the published event being validated.
- Add manual ticket-code entry.
- Verify token format and HMAC signature.
- Return valid, invalid, already used, and wrong-event states.
- Atomically mark a valid ticket as used only when it is unused and belongs to the selected event.
- Build large, unambiguous gate feedback states suitable for fast operation.

### Validation

- Test valid, malformed, tampered, already-used, and wrong-event codes.
- Test concurrent validation attempts for the same ticket.
- Confirm that exactly one concurrent request can accept the ticket.

### Expected Result

Gate staff can validate manually entered tickets, and the same ticket cannot be accepted twice.

---

## feat(gate): add camera-based QR reading

### Goal

Complete the required gate interface while preserving manual validation as a reliable fallback.

### Planned

- Evaluate and document the QR-scanning dependency before adding it.
- Request camera permission only from the gate screen.
- Read QR tokens and submit them through the existing validation flow.
- Prevent repeated scans while a validation request is in progress.
- Handle unsupported browsers, denied permissions, missing cameras, and scan errors.
- Keep manual code entry immediately accessible.

### Validation

- Exercise scanning on at least one supported desktop or mobile browser.
- Exercise permission denial and unavailable-camera fallbacks.
- Confirm that camera scanning produces the same four authoritative outcomes as manual entry.

### Expected Result

Gate staff can validate through the camera or fall back to manual entry without losing functionality.

---

## test(core): cover critical business and end-to-end risks

### Goal

Protect the behavior most important to correctness, security, and interview defensibility.

### Planned

- Test authentication, persistent sessions, expiry, logout, and role boundaries.
- Test organizer and customer ownership rules.
- Test active and expired reservation holds.
- Test concurrent inventory reservation.
- Test approved, declined, expired, repeated, and concurrent payment behavior.
- Test HMAC tampering and unsupported token versions.
- Test wrong-event, duplicate, and concurrent check-in.
- Add focused frontend interaction tests for reservation expiry and gate fallback states.
- Add one browser-level happy path across organizer, customer, and gate roles.

### Validation

- Run all backend, frontend, integration, and browser tests.
- Record the test environment and commands in the README.
- Confirm that tests fail when their protected business rule is deliberately broken during local verification.

### Expected Result

Critical domain, authorization, concurrency, and ticket-validation behavior is reproducibly verified.

---

## test(quality): evaluate focused mutation testing

### Goal

Measure whether critical tests detect meaningful defects without threatening delivery.

### Entry Condition

- The mandatory end-to-end application is complete.
- Critical tests are stable.
- Documentation is current.
- The remaining deadline is sufficient for a bounded experiment.

### Planned

- Select and document a Python mutation-testing tool.
- Restrict the first run to reservation, payment, authorization, and ticket-validation modules.
- Review surviving mutants and add tests only when they reveal a meaningful behavioral gap.
- Record excluded files and timeout limits.
- Stop the experiment if runtime or maintenance cost threatens the deadline.

### Expected Result

Either critical backend tests gain evidence of fault-detection quality, or mutation testing is explicitly deferred with a documented reason.

---

## docs(delivery): finalize evaluator documentation

### Goal

Make the completed project easy to configure, exercise, understand, and defend.

### Planned

- Finalize installation, Podman Compose, migration, seed, environment, and execution instructions.
- Document seeded credentials and a concise evaluator walkthrough.
- Document known limitations and troubleshooting steps.
- Explain architecture, reservation expiry, concurrency control, session security, and HMAC ticket validation.
- Describe AI tools, AI-assisted work, candidate-owned decisions, and versioned artifacts.
- Update current state, future improvements, and every relevant ADR.
- Validate the repository from a clean local setup.

### Validation

- Follow the README from a clean environment as closely as practical.
- Run all release checks and the complete mandatory walkthrough.
- Confirm that documented limitations match actual behavior.

### Expected Result

An evaluator can run and understand the complete application without private guidance.

---

# Optional Backlog

Only consider these after the mandatory flow, critical tests, and delivery documentation are complete:

- Advanced event filters.
- Cancellation with inventory restoration.
- Assigned gate users per event.
- Scheduled cleanup of expired reservation records.
- Real-time availability updates.
- Numbered seat-map sales.
- Broader mutation testing.
- Additional accessibility and visual polish.
- Production deployment.
