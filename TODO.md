# Development Plan

## Current Status

The mandatory application, risk-focused tests, evaluator documentation, and first candidate review
refactor are complete. Three approved post-delivery maintainability and local-execution increments
remain before the candidate's final publication review.

Commit progress: 16 of 19 planned increments complete; 3 remain.

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
- Ticket QR rendering: localized SVG generation through `qrcode.react`; authenticity remains a backend responsibility.
- Test tools: pytest/pytest-cov, Vitest/Testing Library, Playwright, and conditional focused `mutmut` use.
- Frontend modules: feature-first, with local `components/` and `hooks/` directories only when
  needed; types remain with their owning contract or component.

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
- ADR-009: frontend module organization.

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

## Done - feat(checkout): simulate payment and finalize reservations

### Goal

Convert a valid temporary hold into tickets or release it after a declined or expired payment.

### Implemented

- Add deterministic approved and declined payment scenarios.
- Verify that the pending reservation still belongs to the customer and has not expired.
- Atomically convert an approved reservation into a paid reservation and create its tickets.
- Mark a declined reservation accordingly and release its held quantity immediately.
- Return a clear expired state when payment arrives after the deadline.
- Make repeated payment submissions idempotent.
- Build confirmation, refusal, expiry, and retry interfaces.

### Validation

- Exercised approved, declined, expired, repeated, contradictory, foreign-owner, invalid-outcome, and concurrent payment attempts.
- Confirmed that repeated and simultaneous approvals return one stable terminal result and create each ticket number once.
- Confirmed that declined and expired reservations issue no tickets and restore availability immediately.
- Passed 15 frontend tests and 38 backend tests with successful JSON/XML reports and 94% backend coverage.

### Expected Result

The payment simulation completes the reservation safely while preserving the temporary-hold customer experience.

### Next

Sign issued ticket identifiers, present QR credentials, and add private and shareable ticket views.

---

## Done - feat(tickets): issue HMAC-signed QR tickets and sharing links

### Goal

Give customers persistent, presentable, shareable, and verifiable tickets.

### Implemented

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
- Passed 17 frontend tests and 43 backend tests with successful JSON/XML reports and 94% backend coverage.
- Passed frontend formatting, linting, and strict TypeScript checks plus backend Ruff and strict mypy checks.
- Applied Alembic revision `91ec7f95d3b1` and confirmed the current schema matches the SQLAlchemy metadata.

### Expected Result

Customers can view and share persistent QR tickets that cannot be fabricated without the HMAC secret.

### Next

Add authoritative manual gate validation with atomic one-time use.

---

## Done - feat(gate): validate ticket codes exactly once

### Goal

Implement the authoritative gate-validation workflow before adding camera integration.

### Implemented

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
- Passed 21 frontend tests and 46 backend tests with successful JSON/XML reports and 95% backend coverage.
- Passed frontend formatting, linting, strict TypeScript, and production build plus backend Ruff, strict mypy, and package build checks.
- Exercised the live Gate route in desktop and 390-pixel mobile layouts with no console errors or horizontal overflow.

### Expected Result

Gate staff can validate manually entered tickets, and the same ticket cannot be accepted twice.

### Next

Add camera-based QR reading while preserving this manual validation path unchanged.

---

## Done - feat(gate): add camera-based QR reading

### Goal

Complete the required gate interface while preserving manual validation as a reliable fallback.

### Implemented

- Evaluated current browser-scanning alternatives and recorded the candidate-approved `@zxing/browser` decision in ADR-007.
- Locked the Node.js 22-compatible 0.1.x scanner line after the current peer dependency proved to require Node.js 24.
- Kept the camera off until an explicit Gate action and lazy-loaded the decoder only after that action.
- Preferred an environment-facing camera and stopped scanner controls after the first decoded QR.
- Submitted camera and manual tokens through the same authoritative validation mutation.
- Prevented duplicate scan callbacks and form changes while a validation is in progress.
- Released camera controls on cancellation, event changes, pending validation, and route cleanup.
- Mapped unsupported browsers, denied permission, missing cameras, busy hardware, and generic startup failures to manual-fallback guidance.
- Kept the scanned token available for an exact retry when no authoritative network response arrives.
- Updated the approved-checkout recovery link so the complete customer-to-camera demonstration leads directly to My Tickets.

### Validation

- Passed 29 frontend tests, including explicit camera opt-in, duplicate callback suppression, denied permission, missing camera, unsupported API, and all four outcomes through scanned input.
- Passed all 46 backend tests against PostgreSQL with 95% coverage and successful JSON/XML report parsing.
- Passed frontend formatting, linting, strict TypeScript, and production build; the build keeps the scanner in a separate lazy chunk.
- Confirmed through a live browser that the camera starts only after a click, a pending permission request can be cancelled safely, and manual entry remains immediately available.
- The available browser had no physical camera, so optical capture remains a short device-level evaluator check; automated decoding callbacks cover the complete application flow.
- Confirmed that the temporary browser walkthrough data was removed without resetting or changing other local records.

### Expected Result

Gate staff can validate through the camera or fall back to manual entry without losing functionality.

### Next

Consolidate the risk-focused critical suite and add the planned cross-role browser happy path.

---

## Done - test(core): cover critical business and end-to-end risks

### Goal

Protect the behavior most important to correctness, security, and interview defensibility.

### Implemented

- Test authentication, persistent sessions, expiry, logout, and role boundaries.
- Test organizer and customer ownership rules.
- Test active and expired reservation holds.
- Test concurrent inventory reservation.
- Test approved, declined, expired, repeated, and concurrent payment behavior.
- Test HMAC tampering and unsupported token versions.
- Test wrong-event, duplicate, and concurrent check-in.
- Add focused frontend interaction tests for reservation expiry and gate fallback states.
- Add one browser-level happy path across organizer, customer, and gate roles.
- Run core and browser suites against separate disposable PostgreSQL databases.
- Add root hooks for browser installation, core tests, E2E tests, and combined machine-readable reporting.

### Validation

- Run all backend, frontend, integration, and browser tests.
- Record the test environment and commands in the README.
- Confirm that tests fail when their protected business rule is deliberately broken during local verification.
- Passed 29 Vitest interactions, 46 pytest tests with 95% backend coverage, and one complete Playwright Chromium flow.
- Confirmed the HMAC tampering test fails when signature comparison is temporarily removed and passes after restoration.
- Passed frontend/backend formatting, linting, strict type checks, production builds, and aggregate report parsing.

### Expected Result

Critical domain, authorization, concurrency, and ticket-validation behavior is reproducibly verified.

### Next

Evaluate bounded mutation testing without threatening delivery.

---

## Done - test(quality): evaluate focused mutation testing

### Goal

Measure whether critical tests detect meaningful defects without threatening delivery.

### Entry Condition

- The mandatory end-to-end application is complete.
- Critical tests are stable.
- Documentation is current.
- The remaining deadline is sufficient for a bounded experiment.

### Evaluated

- Retained the candidate-approved `mutmut` selection from ADR-008.
- Confirmed that the mandatory flow and critical suite satisfy the experiment entry conditions.
- Attempted dependency resolution through both `uv` and the installed Python's `pip`.
- Deferred installation after both routes exhausted retries against the unavailable local PyPI proxy.
- Left `pyproject.toml`, `uv.lock`, and the virtual environment unchanged rather than committing an unavailable dependency.
- Defined the four critical modules, matching focused tests, excluded areas, survivor-review policy, disposable-database requirement, and resume procedure.
- Limited a future first run to 20 minutes total and 30 seconds per mutant where supported.
- Rejected a project-specific mutation runner because its implementation and validation cost would threaten delivery.

### Validation

- Confirmed the two failed package-resolution attempts made no tracked or environment dependency changes.
- Re-ran the complete critical suite and release checks after documenting the deferral.
- Preserved the previous manual evidence that the HMAC tampering test detects removal of signature comparison without presenting it as an automated mutation result.

### Expected Result

Either critical backend tests gain evidence of fault-detection quality, or mutation testing is explicitly deferred with a documented reason.

### Next

Finalize evaluator-facing setup, walkthrough, architecture, and limitation documentation.

---

## Done - docs(delivery): finalize evaluator documentation

### Goal

Make the completed project easy to configure, exercise, understand, and defend.

### Implemented

- Finalized installation, environment, Podman Compose, migration, seed, execution, and quality
  instructions in the README.
- Added a challenge-coverage matrix, seeded credentials, and a step-by-step evaluator walkthrough.
- Added practical troubleshooting for Podman, ports, schema/seed, signing configuration,
  Ticketmaster, browser/API configuration, camera access, and missing tools.
- Kept architecture, reservation expiry and concurrency, session security, HMAC signing, and
  one-time Gate validation explanations beside the evaluator flow.
- Added a dedicated disclosure of the AI tool, AI-assisted work, candidate-owned decisions and
  actions, shared review boundary, and versioned intermediate artifacts.
- Made the deliberately missing hosted deployment and candidate-owned remote publication explicit.
- Updated the architecture overview, current state, future-improvement boundary, and this plan.
- Reviewed all eight accepted ADRs against the finished implementation; no decision changed or
  required supersession.
- Extracted, rendered, and visually reviewed all five challenge pages before the final requirements
  cross-check.

### Validation

- Validated a frontend clean install from `package-lock.json` with an offline `npm ci` dry run.
- Synchronized the backend from `uv.lock` in locked offline mode and changed no dependency files.
- Reused healthy PostgreSQL, confirmed the schema at head, and confirmed the seed inserts no
  duplicate records.
- Passed formatting, linting, strict frontend/backend type checks, frontend production build, and
  backend source/wheel builds.
- Passed 29 Vitest tests, 46 pytest tests with 95% backend coverage, and one Playwright cross-role
  flow; the machine-readable aggregate reported success and both isolated databases were dropped.
- Confirmed Alembic detects no model/migration drift and all local Markdown links resolve.
- Cross-checked the documented limitations against the challenge, repository, automated flow, and
  known physical-camera boundary.

### Expected Result

An evaluator can run and understand the complete application without private guidance.

### Next

The original 15-increment mandatory plan is complete. Candidate review may add explicitly planned
post-delivery increments before public GitHub publication and challenge submission.

---

## Done - refactor(project): clarify module and process boundaries

### Goal

Address the candidate's architecture review without introducing new framework dependencies or
changing application behavior.

### Implemented

- Kept frontend features as the primary boundary while moving supporting UI into local
  `components/` directories and the session hook into `auth/hooks/`.
- Kept route pages, API contracts, utilities, and focused page tests at feature roots.
- Moved the cross-flow header to the navigation feature and generic primitive-value event
  formatters to `src/lib/`.
- Removed the obsolete `RoleHomePage`, which had no route or consumer after the real role flows
  replaced its initial placeholders.
- Kept TypeScript interfaces with their owner instead of creating one file per declaration.
- Retained the existing custom CSS and avoided a post-delivery Tailwind dependency and visual
  rewrite.
- Made the zero-argument settings and engine caches explicitly one-entry process singletons.
- Added ADR-009 and updated the architecture/frontend/backend knowledge base with the accepted
  boundaries and trade-offs.

### Validation

- Passed frontend Prettier, Oxlint, strict TypeScript, all 29 Vitest tests, and the Vite production
  build.
- Passed backend Ruff formatting/linting, strict mypy, and source/wheel builds.
- Passed the project core-test hook against an isolated PostgreSQL database: 29 frontend tests and
  46 backend tests with 95% backend coverage; the allowlisted test database was dropped afterward.
- Confirmed no stale import points to the pre-refactor file locations.

### Expected Result

Each frontend business feature remains cohesive while larger features expose predictable local
locations for hooks and supporting components; process-scoped backend factories communicate their
actual cache lifecycle.

### Next

Document only critical public contracts and non-obvious invariants with native Python and
TypeScript documentation formats.

---

## docs(code): document critical contracts and invariants

### Goal

Improve interview and maintenance guidance without duplicating self-explanatory signatures.

### Planned

- Use Python docstrings and TSDoc/JSDoc rather than C/C++-oriented Doxygen syntax.
- Document security, concurrency, transaction, time-authority, external-integration, and lifecycle
  behavior where it is not obvious from the signature.
- Cover exported or reusable contracts that benefit from an explicit guarantee.
- Leave trivial wrappers, obvious private helpers, and purely presentational components free of
  boilerplate comments.
- Record the documentation policy in the knowledge base.

### Expected Result

Important behavior is easier to defend and maintain, while comments remain trustworthy and useful.

### Next

Document and streamline the workflow for an existing PostgreSQL installation.

---

## chore(database): support externally managed PostgreSQL

### Goal

Make the existing `DATABASE_URL` boundary obvious and convenient when PostgreSQL runs outside
Podman.

### Planned

- Document database/user creation and configuration for a locally installed PostgreSQL server.
- Add a preparation command that migrates and seeds an already-running PostgreSQL instance without
  starting Podman.
- Keep destructive test database operations restricted to explicit allowlisted names.
- Clarify that the PostgreSQL location is configurable while the database vendor remains an
  intentional architecture decision.

### Expected Result

An evaluator can use either the reproducible Podman service or an existing PostgreSQL installation
without application-code changes.

### Next

Containerize the frontend and backend and extend Compose to run the complete local application.

---

## chore(containers): run the full application with Compose

### Goal

Provide one reproducible local path for PostgreSQL, FastAPI, and the built React application.

### Planned

- Add production-oriented Dockerfiles for the frontend and backend.
- Extend `compose.yaml` with explicit service dependencies, health checks, environment boundaries,
  and named volumes where appropriate.
- Preserve the existing direct host-development workflow.
- Document build, startup, shutdown, configuration, migration, seed, and troubleshooting commands.
- Validate the complete role flow through the composed services.

### Expected Result

The evaluator can start and exercise the full stack through one Compose-compatible workflow while
developers can still run either application directly on the host.

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
