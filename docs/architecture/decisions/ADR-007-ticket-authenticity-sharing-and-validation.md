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
- Read QR camera frames through `@zxing/browser` 0.1.x and its QR-only `BrowserQRCodeReader`.
- Load the scanner dependency only after the Gate user explicitly starts the camera.
- Prefer the environment-facing camera, stop on the first decoded value, and submit that value through the same server-authoritative validation mutation as manual input.
- Stop the camera when the user cancels, changes event context, leaves the screen, or begins validation.
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

### Native `BarcodeDetector`

It would avoid a decoding dependency, but the API remains experimental and is unavailable in some widely used browsers. It cannot be the only implementation for the required desktop/mobile flow.

### `qr-scanner`

It is a focused, lightweight camera scanner with a Web Worker fallback, but its npm package has not been published since version 1.4.2 four years ago. The selected ZXing browser package has a current upstream and a smaller API surface than a complete scanner UI.

### `html5-qrcode`

It provides camera selection and a ready-made interface, but that duplicates the project's own Gate interaction and brings multi-format/file-scanning behavior that the challenge does not require.

### `@zxing/browser` 0.2.x

It retains the selected API, but its `@zxing/library` 0.23 peer requires Node.js 24. The project is validated on Node.js 22, so the lockfile retains `@zxing/browser` 0.1.5 with `@zxing/library` 0.21.3 until the project runtime is upgraded.

## Consequences

- Tokens remain stable across page reloads and sharing.
- Stability depends on retaining the same signing secret; the first version has no key identifier or verification key ring.
- A copied valid link can be used by its bearer; that is the intended sharing model and must be explained to users.
- Database state still controls revocation and one-time usage.
- Concurrent validation attempts serialize on one ticket row, so at most one can return valid.
- The browser necessarily receives the bearer token to render and share it, while the signing secret remains backend-only.
- HMAC key rotation requires versioned verification support for already issued tickets.
- Camera access requires browser permission, an available device, and a secure context; local `http://localhost` development is treated as trustworthy by modern browsers, while remote devices require HTTPS.
- The decoder is absent from the initial application chunk and is downloaded only when camera scanning is requested.
- A camera decode has no authority by itself; only the existing backend outcome may admit or deny a ticket.

## Revisit When

- Tickets require ownership transfer rather than bearer sharing.
- Offline gate operation becomes mandatory.
- Key rotation or hardware-backed signing becomes a production requirement.
- Node.js 24 becomes the accepted project runtime or the 0.1.x scanner line no longer receives necessary compatibility fixes.
