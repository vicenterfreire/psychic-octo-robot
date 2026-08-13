# Non-Functional Requirements

## Delivery Constraints

- The challenge allows seven calendar days from receipt. The receipt date has not yet been recorded in the repository.
- The mandatory end-to-end flow takes priority over optional sophistication.
- The final source must be published in a public GitHub repository by the candidate.
- Commit history must be incremental and use descriptive English messages.

## Required Technologies

- The frontend must use React.
- The backend must use one of the allowed runtimes; this project selected Python and FastAPI.
- The project must use a documented database; this project selected PostgreSQL.

## Documentation

- The README must explain setup, configuration, database preparation, seed data, execution, tests, and known limitations.
- Behavior that is incomplete or not working must be stated explicitly.
- Architecture decisions and important rejected alternatives must remain versioned as ADRs.
- AI tools, AI-assisted work, candidate-owned decisions, and useful intermediate artifacts must be disclosed before delivery.

## Security

- Passwords must be stored with an approved password-hashing algorithm and unique salts.
- Session cookies must be inaccessible to frontend JavaScript.
- Raw opaque session tokens must not be stored in the database.
- Provider credentials and HMAC secrets must not enter source control or browser responses.
- Authorization must be enforced by the backend, not only by hidden frontend routes.
- Ticket signatures must be compared safely and ticket usage must remain server-authoritative.

## Data Integrity and Concurrency

- Event capacity, active holds, completed sales, and ticket usage must remain consistent under concurrent requests.
- PostgreSQL transactions and locking are the source of truth for inventory changes.
- Slow external calls must not execute inside inventory or check-in transactions.
- Repeated payment and validation requests must have safe, deterministic outcomes.

## Usability and Accessibility

- The primary flow must work on modern desktop and mobile browsers.
- Gate feedback must be immediately distinguishable and readable.
- Manual ticket entry must remain available when camera access fails or is denied.
- Forms must expose validation and recovery guidance instead of failing silently.
- The interface should look intentionally designed and avoid generic generated-dashboard patterns.

## Operability

- Local PostgreSQL must be reproducible through a Compose-compatible file with Docker or Podman.
- The complete local application should be reproducible through one Compose-compatible workflow
  without making Podman a requirement for direct host execution or an existing PostgreSQL server.
- Physical phone-camera evaluation may use an explicitly temporary public HTTPS tunnel, but that
  workflow must remain optional, disclose its exposure, and not be presented as production deploy.
- Database migrations and seed commands must be documented.
- Dependency versions must be reproducible through lockfiles.
- `requirements.txt` is a generated compatibility artifact derived from `uv.lock`, not a second dependency source of truth.

## Testing Quality

- Tests focus on domain rules, authentication, authorization, inventory concurrency, payment idempotency, ticket authenticity, and one-time validation.
- Integration tests use PostgreSQL rather than replacing database behavior with an in-memory substitute.
- Mutation testing is attempted only after the mandatory flow and critical suite are stable and only if it does not threaten the deadline.

## Optional Evaluation Differentials

- Advanced search filters.
- Organizer analytics dashboard.
- Cancellation with inventory restoration.
- Real-time availability.
- Numbered seat maps.
- Additional automated tests.
- Production deployment, which adds one point according to the challenge.
