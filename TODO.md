# Development Plan

## Current Status

The mandatory application and all 27 planned increments are complete. The final increment repairs
two Railway-only failures found during candidate-owned publication without changing the validated
local or Quick Tunnel topologies.

Commit progress: 27 of 27 planned increments complete; 0 remain.

The candidate has published the previous plan and created the Railway services. This final hotfix
is committed locally and remains unpushed until the candidate reviews and publishes it.

## Accepted Architecture Direction

- Frontend: React, Vite, and TypeScript.
- Backend: Python 3.14 and FastAPI.
- Database: PostgreSQL.
- Local database runtime: Docker or Podman with a Compose-compatible `compose.yaml` workflow.
- External catalog: Ticketmaster Discovery API.
- Inventory model: quantity-based general admission; no seat map in the mandatory scope.
- Authentication: persistent opaque sessions stored in PostgreSQL and referenced by an HTTP-only cookie.
- Ticket authenticity: persistent, versioned HMAC-signed ticket tokens.
- Reservation model: temporary inventory holds with an explicit expiration time.
- Testing: risk-focused automated tests; mutation testing only if the mandatory flow and critical tests are complete and the deadline remains safe.
- Local execution topology: direct host processes or a three-service Compose workflow with
  PostgreSQL, FastAPI, and the built React application.
- Temporary phone-camera evaluation: an opt-in Cloudflare Quick Tunnel reaches a same-origin Nginx
  gateway; it is public test infrastructure, not production deployment.
- Production deployment provider: Railway, using separate frontend, backend, and managed PostgreSQL
  services with only the same-origin frontend gateway publicly exposed.

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
- Frontend styling: Vite CSS Modules for feature-owned rules; tokens, resets, page structure, and
  deliberate shared primitives remain global.

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

ADR-010 records the candidate-requested local full-stack container topology and its explicit
production limitations.

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

Split the global stylesheet into smaller responsibility files without changing the styling
strategy.

---

## Done - refactor(frontend): split shared stylesheet

### Goal

Make the custom CSS easier to navigate without adding Tailwind, CSS Modules, or a new runtime
dependency.

### Implemented

- Replaced the 1,646-line `src/index.css` with one ordered `src/styles/index.css` entry point.
- Split rules into eight responsibility files: base, authentication, catalog, discovery,
  reservations, tickets, gate, and responsive overrides.
- Preserved the original cascade order and kept responsive overrides last.
- Removed selectors belonging only to the already-deleted `RoleHomePage` placeholder.
- Updated the application import, ADR-009, frontend knowledge base, README, current state, and this
  plan.

### Validation

- Passed Prettier, Oxlint, strict TypeScript, all 29 Vitest tests, and the Vite production build.
- Confirmed Vite resolves all source imports into one 22.06 kB production stylesheet with no
  remaining runtime `@import` directives.
- Confirmed the largest source stylesheet now has 331 lines.

### Expected Result

Styles remain globally ordered and visually equivalent for active screens, while each product area
can be located without navigating one application-wide file.

### Next

Isolate feature-owned styles with Vite CSS Modules while retaining explicit shared primitives.

---

## Done - refactor(frontend): isolate styles with CSS modules

### Goal

Make feature style ownership explicit and prevent accidental cross-feature selector collisions
without adding a runtime styling dependency.

### Implemented

- Co-located authentication, catalog, discovery, event, Gate, health, home, reservation, and ticket
  rules in feature-owned `*.module.css` files.
- Replaced feature class literals with CSS Module imports generated by Vite at build time.
- Kept only tokens, resets, page/header structure, buttons, links, empty states, and feedback
  primitives in the intentional global styling boundary.
- Moved every mobile override beside the feature rules it changes and removed the global
  responsive override file.
- Recorded CSS Modules as the accepted styling decision in ADR-009 without adding Tailwind,
  styled-components, or another dependency.

### Validation

- Passed Prettier, Oxlint, strict TypeScript, all 29 Vitest tests, and the Vite production build.
- Passed the Playwright cross-role flow against a disposable PostgreSQL database; the isolated
  database was dropped afterward.
- Confirmed Vite generated one 25.18 kB compiled stylesheet with locally scoped feature selectors.
- Confirmed no feature-owned class literal remains in the React source.

### Expected Result

Changing a feature module cannot silently restyle a same-named class in another feature, while
shared primitives remain easy to identify and reuse.

### Next

Document only critical public contracts and non-obvious invariants with native Python and
TypeScript documentation formats.

---

## Done - docs(code): document critical contracts and invariants

### Goal

Improve interview and maintenance guidance without duplicating self-explanatory signatures.

### Implemented

- Added PEP 257 docstrings to critical backend factories, dependencies, mappings, external adapters,
  services, signing behavior, and the isolated-database safety boundary.
- Added TSDoc/JSDoc to the frontend credentialed API client, navigation guards, event-form
  normalization, reservation clock estimation, countdown lifecycle, and Gate camera/validation
  boundaries.
- Documented security, lock order, transaction ownership, PostgreSQL time authority, idempotency,
  provider trust, bearer-token limitations, and camera fallback behavior where signatures alone
  are insufficient.
- Kept trivial route wrappers, obvious mappings, and purely presentational components free of
  duplicated signature comments.
- Recorded the selective documentation policy in the backend/frontend knowledge base and
  development workflow.

### Validation

- Passed frontend Prettier, Oxlint, strict TypeScript, all 29 Vitest tests, and the Vite production
  build.
- Passed backend Ruff formatting/linting, strict mypy, source/wheel builds, and all 46 pytest tests
  with 95% coverage.
- Ran the core-test hook against disposable PostgreSQL and confirmed `elite_dev_test` was dropped
  afterward.
- Reviewed the comments against the implementation and the challenge's security, concurrency,
  persistence, QR, camera-fallback, and documentation requirements.

### Expected Result

Important behavior is easier to defend and maintain, while comments remain trustworthy and useful.

### Next

Containerize the frontend and backend and extend Compose to run the complete local application.

---

## Done - chore(containers): run the full application with Compose

### Goal

Provide one reproducible local path for PostgreSQL, FastAPI, and the built React application.

### Implemented

- Added multi-stage frontend and backend Dockerfiles with exact validated base versions, locked
  application dependencies, minimized build contexts, static Nginx delivery, and a non-root API
  runtime.
- Extended `compose.yaml` with PostgreSQL, FastAPI, and built React services, explicit health-gated
  dependencies, runtime-only backend secrets, published-port overrides, and the existing named
  database volume.
- Added `app:build`, `app:up`, `app:down`, `app:status`, and `app:logs` hooks while keeping database
  commands and direct host development available.
- Made the Windows hook detect missing Podman WSL localhost forwarding, align the frontend public
  API URL and backend CORS origin, and print the reachable addresses.
- Documented container build/start/stop/configuration, migration and seed startup behavior,
  existing external PostgreSQL through `DATABASE_URL`, troubleshooting, and production limits.
- Recorded the local topology and rejected alternatives in ADR-010.

### Validation

- Built both images from the committed npm and `uv` lockfiles with exact Node 22.21.0, Python
  3.14.7, Nginx 1.28.3, PostgreSQL 17.10, and `uv` 0.12.3 bases.
- Stopped and restarted the full project while preserving its database volume; PostgreSQL,
  FastAPI, and Nginx all reached healthy status.
- Confirmed migration startup remained at the current head and the idempotent seed inserted zero
  duplicate records on the existing database.
- Confirmed the published frontend and backend health URLs both return HTTP 200.
- Passed the cross-role Playwright scenario once against an isolated three-service Compose project,
  including Organizer edit, Customer approval, ticket retrieval, first Gate acceptance, and
  duplicate rejection; its dedicated test volume was removed afterward.
- Passed the normal host-process Playwright flow after the Compose changes.
- Passed all 29 frontend tests and 46 backend tests with 95% backend coverage.
- Passed frontend and backend formatting, linting, strict type checks, and production/package builds.

### Expected Result

The evaluator can start and exercise the full stack through one Compose-compatible workflow while
developers can still run either application directly on the host.

### Next

Candidate final review, public GitHub publication, and challenge-form submission. These remote
actions remain intentionally outside the AI collaborator's authority.

---

## Done - docs(readme): add a concise run and test guide

### Goal

Make the shortest reliable evaluator workflow visible at the top of the README.

### Implemented

- Added a TL;DR that distinguishes one-time environment setup from the normal one-command startup.
- Documented `app:up` as the recommended Compose entry point and clarified that it builds, migrates,
  seeds, waits for health, resolves the Podman WSL address, and prints the reachable URLs.
- Added a compact mandatory-flow smoke test, automated pre-submission checks, machine-readable test
  report command, and non-destructive shutdown command.
- Clarified that `db:prepare` is not an extra step when the complete application runs through
  Compose.

### Validation

- Cross-checked every documented command against the root package scripts and Compose hook.
- Confirmed the startup behavior against `compose.yaml` and ADR-010.
- Checked the Markdown diff for whitespace errors.

### Expected Result

An evaluator can identify the required setup, start the full application, exercise the central
business flow, run the automated checks, and stop the environment without reading the detailed
reference sections first.

### Next

Candidate final review, public GitHub publication, and challenge-form submission. These remote
actions remain intentionally outside the AI collaborator's authority.

---

## Done - feat(api): expose interactive Swagger documentation

### Goal

Turn FastAPI's existing generic documentation endpoint into a useful, testable evaluator surface.

### Implemented

- Add product metadata, ordered domain tags, operation summaries, descriptions, and request examples.
- Represent the configured opaque session cookie as OpenAPI security on protected operations.
- Explain how to authenticate by executing the real login operation without introducing JWT.
- Print the reachable Swagger URL from the full-stack Podman hook.
- Protect the generated document and Swagger route with focused tests.
- Document usage, security boundaries, limitations, and the no-extra-dependency decision.

### Validation

- Confirmed `/docs` renders Swagger UI and references the generated `/openapi.json` document.
- Verified all operations have summaries and descriptions, protected operations carry the
  configured opaque-cookie scheme, and public operations remain unmarked.
- Passed Ruff formatting/linting and strict mypy for all backend source and tests.
- Passed all 29 frontend and 48 backend tests against disposable PostgreSQL with 95% backend
  coverage.
- Passed the frontend production build and backend source/wheel builds.
- Parsed the updated PowerShell hook and checked the repository diff for whitespace errors.

### Expected Result

An evaluator can open `/docs`, understand the API by domain, sign in with a seeded role, and safely
exercise the corresponding operations against the local environment.

### Next

Candidate README reorganization, final manual walkthrough, public GitHub publication, and
challenge-form submission. The candidate's current uncommitted README notes remain outside this
increment, and all remote actions remain under candidate control.

---

## Done - docs(delivery): streamline evaluator documentation

### Goal

Make local execution immediately discoverable while showing an accurate human-in-the-loop
development process instead of suggesting an unreviewed one-prompt generation flow.

### Planned

- Present the containerless setup first, with PostgreSQL plus either standard `venv`/`pip` or the
  optional `uv` workflow, followed by Docker Compose and Podman alternatives.
- Limit the remaining README content to execution, seeded credentials, troubleshooting, and links
  to complementary documentation.
- Keep architecture, behavior, validation evidence, limitations, and rejected alternatives in the
  existing focused documents under `docs/`.
- Expand the AI disclosure with concrete candidate decisions, review interventions, incremental
  authorization boundaries, and versioned evidence of technical ownership.
- Clarify that `Pode fazer o próximo commit` authorized an already discussed increment rather than
  serving as its complete specification or the entirety of the pair-programming interaction.
- Preserve transparent attribution of the substantial AI-assisted implementation work.

### Expected Result

An evaluator can run the application without navigating a long architectural README and can verify
from the linked collaboration record that the candidate directed, challenged, reviewed, and owns
the solution.

### Validation

- Passed Prettier formatting and `git diff --check` for the changed Markdown files.
- Confirmed every local Markdown link resolves.
- Confirmed the documented `pip`/`PYTHONPATH` path imports the FastAPI application and exposes the
  Alembic command without `uv`.
- Cross-checked Docker, Podman, host PostgreSQL, environment, and execution commands against the
  checked-in configuration and scripts.
- Reviewed the final README ordering and AI-collaboration wording with the candidate before commit.

### Next

Candidate decision about the optional one-point production deployment, followed by public GitHub
publication and challenge-form submission. Remote actions remain under candidate control.

---

## Done - fix(local): harden portable mobile evaluation

### Goal

Make the advertised local workflow reliable for Docker and Podman evaluators, prevent horizontal
mobile overflow, and distinguish QR-decoder failures from browser camera security restrictions.

### Implemented

- Replace the Podman-only npm wrapper with an auto-detected Docker/Podman Compose wrapper.
- Preserve the validated pinned provider only on the Podman path and remove the `uv` requirement
  from Docker execution.
- Correct provider-incompatible status behavior and use a provider-neutral generated database URL.
- Harden global and feature CSS at narrow viewports without hiding overflow.
- Run the critical cross-role browser flow in a mobile viewport and assert that pages do not exceed
  its width.
- Detect insecure camera contexts before loading ZXing and keep manual validation available.
- Move operational recovery guidance from README to root `TROUBLESHOOTING.md`, including the actual
  Windows/Podman, nested npm, CORS, LAN, and camera findings.
- Record Compose-provider portability in ADR-011.

### Validation

- Formatting, linting, strict type checking, and frontend/backend builds pass.
- All 30 frontend and 48 backend tests pass.
- The host-process Playwright flow passes at a phone-sized viewport without horizontal overflow.
- The same database lifecycle succeeds through the detected Podman provider; Docker follows the
  same provider-neutral commands.

---

## Done - fix(local): support portable HTTPS camera evaluation

### Goal

Make host-process and Compose workflows share explicit network configuration, while giving an
evaluator a trusted temporary HTTPS origin for phone-camera testing without certificate installs.

### Implemented

- Add a safe root `.env.example` for local network configuration.
- Read the ignored root `.env` from both development and Compose wrappers.
- Start Vite and Uvicorn through project hooks without user-provided `--` separators.
- Bind the Compose frontend and backend publications through `APP_BIND_ADDRESS`.
- Keep `PUBLIC_HOST` separate so wildcard binding never leaks into URLs or credentialed CORS.
- Document that Compose cannot manufacture a missing Windows-to-Podman-WSL network forward.
- Add an opt-in Compose profile using a pinned official Cloudflare Tunnel container.
- Route the temporary public HTTPS origin only to Nginx.
- Build the containerized frontend with relative `/api` requests and proxy API and Swagger paths to
  FastAPI over the private Compose network.
- Enable the opaque session cookie's `Secure` attribute only in the tunnel workflow.
- Add startup, URL, log, and shutdown hooks with an explicit public-exposure warning.
- Record the accepted RED decision, rejected local-certificate alternatives, limitations, and
  evaluator steps in ADR-012 and focused setup/troubleshooting documentation.

### Validation

- Expanded both local and tunnel Compose configurations and confirmed the expected relative API,
  pinned image, frontend target, and environment-specific cookie attributes.
- Built and started the normal three-service stack; same-origin health, Gate login, HTTP-only
  session restoration, and OpenAPI passed through Nginx.
- Created a real Quick Tunnel and confirmed HTTP 200 for the frontend, proxied health, Swagger,
  OpenAPI, Gate login, and session restoration; its cookie was both `HttpOnly` and `Secure`.
- Removed the public URL and complete temporary stack immediately after the live check.
- Passed formatting, linting, strict type checks, frontend/backend builds, all 30 frontend tests,
  and all 48 backend tests with 95% coverage.
- Passed the complete cross-role Playwright flow at a phone-sized viewport after restoring the
  secure-context and camera-API prerequisite checks.

### Next

Candidate review, public GitHub publication, optional Railway deployment, and challenge-form
submission. Remote operations remain under candidate control.

---

## Done - feat(deploy): prepare Railway publication

### Goal

Publish the challenge through Railway without breaking direct host execution, normal Compose, or
the temporary Quick Tunnel camera workflow.

### Implemented

- Parameterize the Nginx upstream at container startup while retaining `backend:8000` as the local
  default.
- Add service-local Railway configuration for Dockerfile builds, healthchecks, and backend
  migrations/seed.
- Keep the browser and API same-origin by publishing only the frontend gateway and reaching FastAPI
  through Railway private networking.
- Document exact root directories, ports, reference variables, secret handling, deployment order,
  verification, rollback, and the public seeded-account limitation.
- Record the accepted deployment architecture and rejected public two-origin alternative in
  ADR-013.
- Re-run the complete regression suite and live normal/Quick Tunnel container smoke tests.

### Result

An evaluator can open one permanent Railway HTTPS URL, authenticate with the opaque session,
exercise the full application and phone camera, and reach Swagger through the same gateway, while
all previously documented local workflows remain valid.

### Validation

- Cross-checked monorepo roots, Dockerfile builds, config-as-code, reference variables, PostgreSQL,
  private networking, public domains, and pre-deploy behavior against current Railway documentation.
- Parsed both `railway.toml` files and expanded normal and tunnel Compose configurations.
- Passed formatting, linting, strict type checks, frontend/backend builds, all 30 frontend tests,
  all 51 backend tests with 95% coverage, and the cross-role Playwright flow.
- Built and started the local stack; its Nginx template rendered `backend:8000`, and internal
  frontend, API health, OpenAPI, Gate login, and session restoration passed. The known Windows to
  Podman-WSL localhost forwarding limitation was diagnosed by the existing hook.
- Rendered `backend.railway.internal:8000` in a disposable Nginx container with a simulated private
  DNS entry and passed `nginx -t`.
- Created a real Quick Tunnel and confirmed frontend, proxied health, Swagger, OpenAPI, Gate login,
  session restoration, and `HttpOnly` plus `Secure` cookie attributes; removed the public URL and
  complete stack immediately afterward.

### Next

Candidate GitHub push, Railway service/secret configuration, live URL verification, and challenge
submission. Remote actions remain under candidate control.

---

## Done - fix(deploy): repair Railway authentication startup

### Goal

Make the live Railway backend seed evaluation data during pre-deploy and serialize opaque-session
cookie expiration consistently with Python 3.14.

### Implemented

- Invoke the compound migration and seed command through an explicit POSIX shell.
- Normalize database-provided UTC datetimes to `datetime.UTC` at the HTTP cookie boundary.
- Cover the Railway `ZoneInfo("Etc/UTC")` regression deterministically.
- Record diagnosis, manual recovery, expected logs, and live redeployment order.

### Expected result

The pre-deploy log includes the seed summary, seeded credentials return HTTP 200 from login, and
Starlette emits a persistent secure session cookie instead of raising a UTC formatting error.

### Validation

- Parsed `backend/railway.toml` and confirmed the explicit `/bin/sh -c` command is preserved.
- Reproduced Python 3.14 rejecting `ZoneInfo("Etc/UTC")` for an HTTP GMT date and accepting the
  normalized `datetime.UTC` value.
- Passed formatting, Ruff, strict frontend/backend type checks, both production builds, all 30
  frontend tests, and all 52 backend tests with 95% coverage.
- Built and started the Compose images; container logs showed Alembic, the idempotent seed summary,
  Uvicorn, and healthy API checks in sequence.
- Completed a disposable in-container Organizer login, session restoration, and logout with HTTP
  200, 200, and 204 respectively; the cookie included a valid GMT expiration.

### Next

Candidate push, backend redeploy, confirmation of the pre-deploy seed summary, frontend redeploy to
refresh its private upstream, and final live challenge verification.

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
- Production observability, backup verification, rate limiting, and restricted public Swagger.
