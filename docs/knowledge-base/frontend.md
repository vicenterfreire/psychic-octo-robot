# Frontend Knowledge Base

## Current Responsibility

The frontend is a React single-page application built by Vite. It presents role-specific workflows while the backend remains authoritative for identity, inventory, payment, ticket, and validation decisions.

## Current Structure

- `src/App.tsx` composes application-wide providers.
- `src/app/router.tsx` defines navigation.
- `src/app/query-client.ts` configures TanStack Query for remote state.
- `src/lib/api-client.ts` is the credentialed JSON transport boundary.
- `src/features/` groups screens, requests, and tests by product feature.
- `src/test/setup.ts` configures browser-like assertions for Vitest.

This boundary is intentionally light: shared abstractions should appear only after multiple features need them.

## State Ownership

TanStack Query owns server state and future mutation invalidation. React component state will own form values, transient interaction state, and reservation countdown presentation. The server deadline remains authoritative; no general-purpose global store is planned.

## API Communication

The client reads `VITE_API_URL`, defaults to `http://localhost:8000/api`, requests JSON, and always includes browser credentials. This prepares the transport for the accepted HTTP-only opaque session without exposing a session token to React.

Failed non-JSON or JSON responses are normalized at this boundary so feature components do not duplicate transport parsing.

## Quality Boundary

Prettier owns formatting, Oxlint owns static linting, TypeScript runs with strict project settings, and Vitest with Testing Library protects meaningful interaction and integration boundaries. The initial test verifies both visible health feedback and credentialed transport behavior.
