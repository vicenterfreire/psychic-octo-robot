# ADR-003: External Catalog and Inventory Model

## Status

Accepted

## Context

The challenge permits Ticketmaster, TMDb, or both and requires either a seat map or quantity selection. Implementing every option would compete with completion of the mandatory end-to-end flow.

## Decision

- Integrate only the Ticketmaster Discovery API in the mandatory scope.
- Call Ticketmaster exclusively from the backend.
- Normalize external results into a small internal catalog contract.
- Store a snapshot of the selected external item when an organizer creates an event.
- Treat date, location, capacity, price, ownership, and publication as local event data.
- Use quantity-based general admission with one inventory pool per event.
- Implement public search against published local events, not live Ticketmaster data.

## Alternatives Considered

### TMDb with a seat map

Movie data and numbered cinema seats fit naturally, but the seat-map model and interface create substantially more work than quantity inventory.

### Ticketmaster and TMDb

Supporting both adds provider abstraction and divergent metadata without improving the mandatory purchase and validation flow.

### Numbered seats

Unique seat constraints are demonstrable, but seat layout, selection, accessibility, and real-time conflict feedback create a larger frontend and domain scope.

### Continuous synchronization

Keeping local events synchronized with Ticketmaster could unexpectedly change organizer-owned date or venue data and make the demo depend on provider availability.

## Consequences

- The mandatory flow remains small enough to complete and explain.
- The double-sale rule is interpreted as never selling or actively holding more units than capacity.
- Local events remain available if Ticketmaster is unavailable.
- Snapshot data may become stale, which is intentional for this challenge.

## Revisit When

- Numbered seating becomes a product requirement.
- Multiple providers are needed by real organizers.
- External licensing or synchronization requirements change.
