# ADR-007: Ticket Authenticity, Sharing, and Validation

## Status

Accepted

## Context

Tickets must be represented as QR codes, shared by link, resistant to fabrication, and accepted at most once. Validation still requires database state, so fully offline verification is not a goal.

## Decision

- Use a compact, versioned token containing a public ticket identifier and an HMAC-SHA-256 signature.
- Sign a canonical payload with a dedicated secret configured outside source control.
- Encode the token in a URL-safe representation.
- Include no customer personal data in the token.
- Compare signatures using a constant-time operation.
- Use the same token for the QR payload and bearer sharing link.
- Load ticket event and usage state from PostgreSQL after signature verification.
- Atomically set the usage timestamp only when the ticket is unused and belongs to the selected event.
- Keep validation outcomes explicit: valid, invalid, already used, and wrong event.

## Alternatives Considered

### Sequential or plain ticket identifiers

They are predictable and do not prove that the application issued the credential.

### Random bearer token stored in plaintext

It is difficult to guess and easy to revoke, but a database read leak would directly reveal valid credentials.

### JWT

It provides a standardized claims container, but the project needs only a version, identifier, and signature. JWT adds unnecessary claims and library behavior.

### Offline-only validation

It cannot reliably enforce one-time use across multiple gate devices without later conflict resolution.

## Consequences

- Tokens remain stable across page reloads and sharing.
- A copied valid link can be used by its bearer; that is the intended sharing model and must be explained to users.
- Database state still controls revocation and one-time usage.
- HMAC key rotation requires versioned verification support for already issued tickets.

## Revisit When

- Tickets require ownership transfer rather than bearer sharing.
- Offline gate operation becomes mandatory.
- Key rotation or hardware-backed signing becomes a production requirement.
