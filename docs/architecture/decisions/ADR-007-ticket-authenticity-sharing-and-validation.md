# ADR-007: Ticket Authenticity, Sharing, and Validation

## Status

Accepted

## Context

Tickets must be represented as QR codes, shared by link, resistant to fabrication, and accepted at most once. Validation still requires database state, so fully offline verification is not a goal.

## Decision

- Use the compact token `v1.<32-lowercase-hex-UUID>.<base64url-HMAC-SHA-256>`.
- Sign the canonical UTF-8 payload `v1:<32-lowercase-hex-UUID>` with a dedicated secret configured outside source control.
- Require at least 32 bytes in the configured secret and fail ticket endpoints closed when it is absent or too short.
- Encode the signature as unpadded URL-safe Base64.
- Include no customer personal data in the token.
- Compare signatures using a constant-time operation.
- Use the same token for the QR payload and bearer sharing link.
- Load ticket event and usage state from PostgreSQL after signature verification.
- Render the QR locally in the React application as SVG through the focused `qrcode.react` dependency.
- Lock the authentic ticket row with `SELECT FOR UPDATE` during Gate validation.
- Atomically set the usage timestamp and Gate user only when the ticket is unused, unrevoked, approved, and belongs to the selected event.
- Keep validation outcomes explicit: valid, invalid, already used, and wrong event.
- Treat revoked or non-approved credentials as invalid, and check event mismatch before exposing prior usage state.

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
- Stability depends on retaining the same signing secret; the first version has no key identifier or verification key ring.
- A copied valid link can be used by its bearer; that is the intended sharing model and must be explained to users.
- Database state still controls revocation and one-time usage.
- Concurrent validation attempts serialize on one ticket row, so at most one can return valid.
- The browser necessarily receives the bearer token to render and share it, while the signing secret remains backend-only.
- HMAC key rotation requires versioned verification support for already issued tickets.

## Revisit When

- Tickets require ownership transfer rather than bearer sharing.
- Offline gate operation becomes mandatory.
- Key rotation or hardware-backed signing becomes a production requirement.
