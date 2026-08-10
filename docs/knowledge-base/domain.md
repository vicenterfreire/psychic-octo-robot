# Domain Knowledge

## Core Concepts

### User

An authenticated account with exactly one role in the mandatory scope: Organizer, Customer, or Gate.

### Catalog Item

Normalized Ticketmaster data shown temporarily to an organizer. It is not itself a sellable event.

### Event

A local, organizer-owned event created from a catalog snapshot. It defines local date, location, capacity, price, and publication status.

### Reservation

A customer's request for a quantity of general-admission tickets. A pending reservation temporarily holds inventory until payment, decline, or expiration.

### Ticket

A single admission credential issued only from an approved reservation. It has a signed public token and a one-time usage state.

## Mandatory States

- Event: draft or published.
- Reservation: pending, approved, declined, or expired.
- Ticket: unused or used.

Additional states require a demonstrated current requirement before being introduced.

## Business Invariants

- Only published events are customer-visible and reservable.
- Organizer ownership is enforced for event management.
- Customer ownership is enforced for reservations and private ticket lists.
- Sold quantity plus active pending holds never exceeds event capacity.
- A pending hold is active only while its expiration is later than PostgreSQL's current time.
- An approved reservation cannot be expired or declined later.
- A declined or expired reservation consumes no inventory.
- Exactly one ticket is issued for each approved unit.
- A ticket token is trusted only after its HMAC signature is verified.
- Ticket validation always includes a selected event context.
- A ticket can move from unused to used at most once.

## Time Model

Reservation expiration uses database timestamps. The API returns the authoritative deadline, and the frontend displays a countdown without deciding validity. Stale reservations are marked or ignored lazily during availability, hold, and payment operations; no scheduler is required initially.

## Deliberate Simplifications

- General-admission quantity replaces numbered seats.
- Payment outcomes are deterministic simulations.
- Gate users may validate any published event in the mandatory scope.
- Cancellation, refunds, ticket transfer, and resale are excluded.
- Ticketmaster is used only as source material; local events do not synchronize continuously.

## Validation Outcomes

- **Valid:** authentic, unused ticket for the selected event; it is consumed atomically.
- **Invalid:** malformed, tampered, unknown, or otherwise untrusted credential.
- **Already used:** authentic ticket whose usage was previously recorded.
- **Wrong event:** authentic ticket that belongs to a different event than the gate context.
