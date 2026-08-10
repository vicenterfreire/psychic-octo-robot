# Frontend Knowledge Base

## Current Responsibility

The frontend is a React single-page application built by Vite. It presents role-specific workflows while the backend remains authoritative for identity, inventory, payment, ticket, and validation decisions.

## Current Structure

- `src/App.tsx` composes application-wide providers.
- `src/app/router.tsx` defines navigation.
- `src/app/query-client.ts` configures TanStack Query for remote state.
- `src/lib/api-client.ts` is the credentialed JSON transport boundary.
- `src/features/auth/` contains session requests, login/logout interactions, and route guards.
- `src/features/catalog/` contains the Organizer search, normalized result cards, and transient selection.
- `src/features/events/` contains event transport types, local-detail forms, owned-event listing, editing, and publication interactions.
- `src/features/discovery/` contains public/customer event queries, search, result cards, detail presentation, and session-aware navigation.
- `src/features/` groups screens, requests, and tests by product feature.
- `src/test/setup.ts` configures browser-like assertions for Vitest.

This boundary is intentionally light: shared abstractions should appear only after multiple features need them.

## State Ownership

TanStack Query owns server state and future mutation invalidation. React component state will own form values, transient interaction state, and reservation countdown presentation. The server deadline remains authoritative; no general-purpose global store is planned.

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

The form converts the displayed BRL decimal into integer minor units and the browser's local date-time into an ISO timestamp with an offset before submission. Backend validation remains authoritative. Drafts remain visible to their Organizer, while the public/customer query introduced in the next increment will select only published events.

## Published Discovery Flow

The public `/events` route and protected `/customer` route render the same discovery component with different header and detail-link boundaries. Public reads do not restore a session; authenticated Customer pages reuse the existing session query and logout behavior. Event details follow the same split at `/events/:id` and `/customer/events/:id`.

TanStack Query keys include the applied search term, so default discovery, filtered results, and individual event details remain distinct server-state entries. Search executes only on form submission. Empty, loading, error, missing-image, sold-out, and result states are explicit.

Cards and details format the backend's ISO timestamp and integer-minor-unit price, then display local venue/address and calculated availability. The UI states that availability is current rather than guaranteed. Quantity selection is intentionally left to the next reservation increment, where the backend will recalculate inventory transactionally.

## Quality Boundary

Prettier owns formatting, Oxlint owns static linting, TypeScript runs with strict project settings, and Vitest with Testing Library protects meaningful interaction and integration boundaries. Tests cover health transport, login, session restoration, cross-role redirection, catalog search/selection, stable errors, provider-secret absence, event management, published discovery, basic search, empty results, event details, and availability presentation. The root test-report hook also writes a Vitest JSON result for automated inspection.
