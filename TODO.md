# Development Plan

## Current Status

The requirements, architecture decisions, and runnable full-stack foundation are complete. PostgreSQL and business functionality have not been initialized yet. No later planned task is considered done until its changes are validated, staged, and committed locally.

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

## feat(database): model persistence and seed evaluation data

### Goal

Create the PostgreSQL schema required by the complete workflow and make evaluator setup reproducible.

### Planned

- Add a Compose-compatible PostgreSQL service that runs with Podman.
- Configure the accepted ORM or query layer and migration tooling.
- Model users, sessions, external catalog snapshots, events, reservations, tickets, and ticket usage.
- Represent reservation status and expiration explicitly.
- Store monetary values as integer minor units.
- Add ownership, role, uniqueness, capacity, status, and timestamp constraints.
- Create the initial migration.
- Seed one organizer, two customers, one gate user, and one published event with available quantity.
- Seed a stable Ticketmaster-style snapshot so the mandatory demo does not depend on external API availability.
- Document database startup, migration, reset, and seed commands.

### Validation

- Start PostgreSQL through Podman Compose.
- Apply migrations to an empty database.
- Run the seed process twice and confirm its intended repeatability behavior.
- Inspect the resulting constraints and seed records.

### Expected Result

A fresh PostgreSQL database can be started, migrated, and populated with the required evaluation data.

---

## feat(auth): implement persistent opaque-session authentication

### Goal

Authenticate the three required roles without requiring users to log in again every time they reopen the site.

### Planned

- Implement password hashing and verification using the accepted algorithm and documented parameters.
- Generate cryptographically random opaque session identifiers.
- Store only a derived session-token representation in PostgreSQL.
- Add persistent session expiration, renewal, revocation, and logout behavior.
- Set HTTP-only cookie attributes appropriate for local development and production.
- Add login, current-session, and logout endpoints.
- Enforce organizer, customer, and gate role boundaries.
- Restrict organizers to their own events and customers to their own reservations and tickets.
- Build the login, session restoration, protected-route, and logout frontend flows.

### Validation

- Test valid and invalid credentials.
- Confirm that refreshing or reopening the frontend restores an unexpired session.
- Confirm that logout and expiry revoke access.
- Confirm that each role is denied access to the other roles' protected actions.
- Inspect cookies to verify that session identifiers are not exposed to frontend JavaScript.

### Expected Result

Each seeded user can remain authenticated for the accepted lifetime and access only the functionality allowed for its role.

---

## feat(catalog): integrate the Ticketmaster event catalog

### Goal

Allow organizers to search external source material while keeping provider credentials on the backend.

### Planned

- Implement a server-side Ticketmaster Discovery client.
- Keep the Ticketmaster API key out of browser code and tracked files.
- Add organizer-only catalog search.
- Normalize Ticketmaster responses into a small internal DTO.
- Handle missing credentials, timeouts, quota responses, empty results, and provider unavailability.
- Build the organizer catalog search and selection interface.

### Validation

- Exercise successful and unsuccessful provider responses.
- Confirm that the provider credential never appears in browser requests or application responses.
- Confirm that normalized results contain only the fields needed to create a local event.

### Expected Result

An organizer can search Ticketmaster and select an external catalog item without exposing the API credential.

---

## feat(events): implement organizer event management

### Goal

Allow organizers to create and manage local events derived from Ticketmaster data.

### Planned

- Persist a snapshot of the selected Ticketmaster item.
- Let the organizer define date, location, total capacity, and price.
- Support the minimal event lifecycle required for creation, editing, and publication.
- Allow organizers to list and edit only their own events.
- Reject invalid dates, prices, capacities, and unsafe capacity reductions.
- Build the minimal organizer event screens without adding an analytics dashboard.

### Validation

- Create an event from a normalized catalog result.
- Confirm organizer ownership enforcement.
- Confirm that only valid published events become customer-visible.
- Confirm that external provider changes do not modify an existing local event snapshot.

### Expected Result

An organizer can create, edit, and publish a locally owned event based on Ticketmaster content.

---

## feat(discovery): implement published event discovery

### Goal

Let customers find published events and inspect the information required to start a reservation.

### Planned

- List only published events.
- Add mandatory basic text search.
- Show event details, date, location, price, and current availability.
- Build responsive public and customer-facing event screens.
- Preserve advanced filters for the optional backlog.

### Validation

- Confirm unpublished events never appear publicly.
- Confirm basic search behavior and empty states.
- Confirm date, location, price, and availability are displayed consistently.

### Expected Result

A customer can find a published event and proceed to quantity selection.

---

## feat(reservations): implement temporary inventory holds

### Goal

Protect the customer's selected quantity for a short payment window without overselling the event.

### Planned

- Create pending reservations with a configurable expiration timestamp.
- Use PostgreSQL time and transactional locking as the source of truth for expiration and capacity.
- Expire stale pending reservations lazily during availability, reservation, and payment operations.
- Reserve quantity atomically while accounting for sold tickets and unexpired holds.
- Reject requests that exceed the currently available quantity.
- Expose the reservation deadline to the frontend.
- Build a visible countdown and clear expired-reservation recovery flow.
- Avoid queues or background workers in the initial implementation.

### Validation

- Confirm that an active hold reduces availability for other customers.
- Confirm that an expired hold no longer consumes availability.
- Test simultaneous reservation attempts against the final available quantity.
- Confirm that the frontend uses the server deadline rather than its own clock as the authority.

### Expected Result

A customer receives a time-limited hold, and concurrent customers cannot reserve more than the remaining inventory.

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
