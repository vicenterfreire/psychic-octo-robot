# Frontend Knowledge Base

## Current Responsibility

The frontend is a React single-page application built by Vite. It presents role-specific workflows while the backend remains authoritative for identity, inventory, hold expiration, payment, ticket, and validation decisions.

## Current Structure

- `src/App.tsx` composes application-wide providers.
- `src/app/router.tsx` defines navigation.
- `src/app/query-client.ts` configures TanStack Query for remote state.
- `src/lib/api-client.ts` is the credentialed JSON transport boundary.
- `src/features/auth/` contains session requests, login/logout interactions, and route guards.
- `src/features/catalog/` contains the Organizer search, normalized result cards, and transient selection.
- `src/features/events/` contains event transport types, local-detail forms, owned-event listing, editing, and publication interactions.
- `src/features/gate/` contains Gate event selection, manual validation transport, and authoritative result presentation.
- `src/features/discovery/` contains public/customer event queries, search, result cards, detail presentation, and session-aware navigation.
- `src/features/reservations/` contains hold transport, quantity submission, server-offset countdown, simulated checkout, and reload/terminal-state recovery.
- `src/features/tickets/` contains private/public ticket queries, Customer presentation, bearer sharing, and SVG QR rendering.
- `src/features/` groups screens, requests, and tests by product feature.
- `src/test/setup.ts` configures browser-like assertions for Vitest.

This boundary is intentionally light: shared abstractions should appear only after multiple features need them.

## State Ownership

TanStack Query owns server state and mutation invalidation. React component state owns form values, transient interaction state, and reservation countdown presentation. The server deadline remains authoritative; no general-purpose global store is planned.

## API Communication

The client reads `VITE_API_URL`, defaults to `http://localhost:8000/api`, requests JSON, and always includes browser credentials. This prepares the transport for the accepted HTTP-only opaque session without exposing a session token to React.

Failed non-JSON or JSON responses are normalized at this boundary so feature components do not duplicate transport parsing.

## Session Flow

TanStack Query calls `GET /auth/me` when a session-aware route renders. A `401` means there is no active session; transport or server errors remain distinguishable and do not silently redirect the user. An unexpired cookie therefore restores the user after a refresh or browser restart without exposing the credential to JavaScript.

Login writes the returned user into the shared session query and redirects to the role workspace. Logout revokes the backend session first, then clears that query. `RequireSession` handles authentication and `RequireRole` prevents cross-role navigation, but both are user-experience boundaries only: the backend must authorize every protected operation.

## Organizer Catalog Flow

The Organizer submits a complete query before the frontend calls `/catalog/events`; typing does not consume provider quota. The browser receives only the small internal event contract and never receives or knows the Ticketmaster API key.

Search is a TanStack Query mutation because it is an explicit user action rather than continuously loaded server state. The selected source item remains local component state until creation. Selecting it opens the local event form, and the browser submits only the provider identifier plus Organizer-managed fields. A refresh clears an unsubmitted selection but does not affect any created event.

The interface provides loading, empty, provider-error, missing-image, external-source, selected, draft, editing, and publication states. External links are opened with a separate browsing context and no referrer relationship.

## Organizer Event Flow

The event collection is a TanStack Query resource enabled after the Organizer session resolves. Creation, full-detail editing, and explicit publication are mutations that invalidate that collection. This keeps server responses authoritative without introducing a client-side global event store.

The form converts the displayed BRL decimal into integer minor units and the browser's local date-time into an ISO timestamp with an offset before submission. Backend validation remains authoritative. Drafts remain visible only to their Organizer, while public/Customer discovery selects published upcoming events.

## Published Discovery Flow

The public `/events` route and protected `/customer` route render the same discovery component with different header and detail-link boundaries. Public reads do not restore a session; authenticated Customer pages reuse the existing session query and logout behavior. Event details follow the same split at `/events/:id` and `/customer/events/:id`.

TanStack Query keys include the applied search term, so default discovery, filtered results, and individual event details remain distinct server-state entries. Search executes only on form submission. Empty, loading, error, missing-image, sold-out, and result states are explicit.

Cards and details format the backend's ISO timestamp and integer-minor-unit price, then display local venue/address and calculated availability. The UI states that availability is current rather than guaranteed. An authenticated Customer can choose quantity from the detail, while the backend recalculates inventory transactionally.

## Temporary Reservation Flow

Submitting quantity creates a hold and invalidates all published-event query keys before navigating to `/customer/reservations/:id`. A `409` remains on the event screen with the quantity observed by the backend so the Customer can adjust rather than receiving a false confirmation.

The hold route fetches its private reservation by identifier and separately reuses the published event query for a friendly title. Reloading therefore restores the server state instead of depending on navigation memory. An expired response presents a direct link back to quantity selection.

The API returns `server_time` beside `expires_at`. The countdown records the browser receipt time, derives the offset between browser and server clocks, and advances that estimated server time for display. When it reaches zero, the screen refetches the reservation; the browser never changes status or authorizes payment. Network delay may make the display slightly optimistic, but the next backend command remains authoritative.

## Simulated Checkout Flow

The pending-hold screen exposes explicit approval and decline buttons and states that no real charge occurs. Both call the same payment endpoint with a deterministic outcome. On success, the mutation replaces the reservation query with the returned terminal state and invalidates published-event availability.

Approval shows the persisted ticket count. Decline and expiration explain that inventory was released and link back to a new hold. Reload uses the same reservation GET, so confirmation and failure states do not depend on in-memory mutation state.

## Signed Ticket Flow

The protected `/customer/tickets` route loads only the authenticated Customer's approved tickets. Each card presents event context, current use/revocation state, and the HMAC token as an SVG QR through `qrcode.react`. The focused QR dependency is localized to one presentational component; the backend remains responsible for token creation and validity.

The copy action uses the generated absolute sharing URL and handles unavailable or rejected clipboard access. The public `/tickets/share/:token` route deliberately avoids session restoration, loads the minimized bearer response, and renders the same token from the URL as the QR payload. Both views warn that possession grants presentation ability. Neither view treats frontend state or QR decoding as authorization.

## Gate Validation Flow

The protected `/gate` route loads the Gate-specific published event collection rather than public upcoming discovery. Its native event selector and adjacent date/location context make the current validation scope explicit. The code textarea supports paste or manual typing, trims surrounding whitespace at submission, disables duplicate clicks while pending, and clears only after an authoritative result is received.

The backend outcome controls one of four large, color-distinct panels: entry approved, invalid, already used, or wrong event. Color is reinforced by headings and explanatory text. A transport failure never claims acceptance or rejection because the server may have committed even when its response was lost; the operator is told not to admit yet and to retry the same credential.

The form does not decode or trust the token locally. Camera support will be a second input mechanism for the same mutation, while manual entry remains immediately available as required.

## Quality Boundary

Prettier owns formatting, Oxlint owns static linting, TypeScript runs with strict project settings, and Vitest with Testing Library protects meaningful interaction and integration boundaries. Tests cover health transport, login, session restoration, cross-role redirection, catalog search/selection, stable errors, provider-secret absence, event management, published discovery, quantity submission, server-clock correction, payment approval, issued quantity, expired-hold recovery, private QR presentation, unauthenticated bearer sharing, and all four manual Gate outcomes. The root test-report hook also writes a Vitest JSON result for automated inspection.
