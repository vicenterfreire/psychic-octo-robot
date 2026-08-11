# Future Improvements

These improvements are deliberately deferred until the mandatory end-to-end flow, critical tests, and evaluator documentation are complete.

## Numbered Seat Maps

- **Current approach:** one general-admission inventory pool per event.
- **Limitation:** customers cannot select a specific seat or sector.
- **Possible improvement:** model venues, sections, rows, seats, and unique event-seat allocation.
- **Worthwhile when:** the product must support cinema or theater seating.

## Advanced Event Discovery

- **Current approach:** basic text search over published local events.
- **Limitation:** no date, location, category, or price filtering.
- **Possible improvement:** indexed filters, sorting, and pagination.
- **Worthwhile when:** the catalog is large enough that text search is insufficient.

## External Catalog Caching

- **Current approach:** each explicit Organizer search calls Ticketmaster once and returns at most 12 normalized events.
- **Limitation:** repeated identical searches consume the finite provider quota and repeat network latency.
- **Possible improvement:** add a short-lived server-side cache keyed by normalized query while preserving stable error behavior.
- **Worthwhile when:** measured usage or quota pressure justifies cache invalidation and operational complexity.

## Cancellation and Refunds

- **Current approach:** approved reservations and tickets are final.
- **Limitation:** inventory cannot be restored through a customer cancellation flow.
- **Possible improvement:** cancellation policy, ticket revocation, refund state, and atomic inventory restoration.
- **Worthwhile when:** real customer support and payment behavior are introduced.

## Gate Assignment

- **Current approach:** a Gate user may validate any published event.
- **Limitation:** gate authorization is broader than a production least-privilege model.
- **Possible improvement:** assign gate users to organizers, venues, or events.
- **Worthwhile when:** multiple unrelated organizers share the platform.

## Advanced Camera Controls

- **Current approach:** request an environment-facing camera and keep manual entry visible.
- **Limitation:** the operator cannot select among multiple cameras or control a supported torch from the interface.
- **Possible improvement:** list devices after permission, persist a local preference, and expose torch controls only when the active track reports support.
- **Worthwhile when:** testing on actual gate hardware shows that automatic camera selection or low-light scanning is unreliable.

## Scheduled Reservation Cleanup

- **Current approach:** expired holds are ignored or marked lazily during relevant operations.
- **Limitation:** expired rows can accumulate between operations.
- **Possible improvement:** periodic cleanup with a scheduled job while retaining timestamp-based correctness.
- **Worthwhile when:** abandoned reservation volume affects query performance or operations.

## Real-Time Availability

- **Current approach:** availability refreshes through normal API queries and mutation invalidation.
- **Limitation:** another customer's hold may not appear until refetch.
- **Possible improvement:** server-sent events or WebSockets for availability changes.
- **Worthwhile when:** measured contention makes stale displays a frequent usability issue.

## Session Hardening

- **Current approach:** fixed seven-day opaque session with immediate server-side logout.
- **Limitation:** no device list, rotation, suspicious-login detection, or per-request CSRF token.
- **Possible improvement:** session rotation, device management, shorter privileged sessions, and topology-appropriate CSRF protection.
- **Worthwhile when:** the production domain and threat model are known.

## HMAC Key Rotation

- **Current approach:** versioned tokens use one configured HMAC secret.
- **Limitation:** replacing the secret can invalidate already issued tickets.
- **Possible improvement:** key identifiers and a bounded verification key ring.
- **Worthwhile when:** production key-rotation policy or long-lived events require it.

## Real Payment Provider

- **Current approach:** deterministic approved and declined simulation.
- **Limitation:** no provider webhook, reconciliation, fraud control, or refund.
- **Possible improvement:** provider sandbox integration with idempotent webhooks and explicit payment attempts.
- **Worthwhile when:** financial transactions become a real requirement.

## Deployment and Operations

- **Current approach:** local execution; provider selection is deferred.
- **Limitation:** evaluators cannot use a hosted instance yet, and no production observability exists.
- **Possible improvement:** hosted frontend, FastAPI service, managed PostgreSQL, HTTPS secrets, health monitoring, structured logs, and CI/CD.
- **Worthwhile when:** the mandatory local flow and critical tests are stable.

## Broader Test and Mutation Coverage

- **Current approach:** risk-focused tests plus a deliberate manual mutation that proved the HMAC tampering test fails when signature comparison is removed. The first automated `mutmut` attempt was deferred without changing dependencies because the available PyPI proxy was unreachable.
- **Limitation:** automated mutation scores are unavailable, and low-risk presentation or framework glue may remain lightly tested.
- **Possible improvement:** follow the documented four-module, disposable-database, 20-minute experiment when the current tool version can be verified and installed; then expand component, accessibility, contract, or performance suites only where a meaningful risk remains.
- **Worthwhile when:** PyPI access is restored and the remaining delivery time can absorb the bounded run and survivor review.
