# ADR-006: Temporary Reservation Lifecycle

## Status

Accepted

## Context

The customer should not lose selected inventory while moving through simulated payment. A simple checkout-only allocation would allow another customer to take the final units before payment completes.

The implementation must still avoid queues and scheduled infrastructure unless they are necessary for correctness.

## Decision

- Create pending reservations that hold a selected quantity for ten minutes by default.
- Make the lifetime configurable while keeping the documented default stable.
- Use PostgreSQL time as the authority for creation and expiration.
- Treat a reservation as active only when its status is pending and `expires_at` is later than database current time.
- Lock the event inventory decision inside a short transaction when creating or finalizing a hold.
- Lazily mark or ignore stale holds during availability, reservation, and payment operations.
- Do not introduce a background worker, scheduler, cache, or queue initially.
- Return the authoritative expiration timestamp and show a frontend countdown.
- On approval, atomically approve the reservation and issue tickets.
- On decline, mark it declined and release the quantity immediately.
- Reject approval after expiration and make repeated payment attempts idempotent.

## Alternatives Considered

### Allocate only during payment

This is simpler and removes expiration, but it does not protect the customer between quantity selection and payment.

### Scheduled expiration worker

It can clean rows promptly but introduces another process and failure mode. Correct availability can be calculated without immediate physical cleanup.

### Redis expiring keys

Redis offers natural TTLs but creates a second inventory source and distributed consistency problem that the challenge does not need.

### Longer or sliding holds

They improve customer time but increase inventory starvation. Ten minutes is a configurable, bounded starting point.

## Consequences

- Reservation and payment logic is more complex than an atomic checkout.
- Customers receive a protected payment window.
- Expired rows may remain until a relevant operation observes them, but they no longer consume availability.
- Concurrency tests against PostgreSQL are mandatory for confidence.
- The browser clock never decides whether payment is allowed.

## Revisit When

- Abandoned reservation volume creates cleanup or query-performance problems.
- Payment processing requires a longer external authorization window.
- Multiple inventory pools or numbered seats are introduced.
