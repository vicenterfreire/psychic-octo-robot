# ADR-004: Session Authentication and Authorization

## Status

Accepted

## Context

The application has three roles and must restore authentication when a user reopens the browser. It is a single first-party web application, not a distributed API ecosystem.

## Decision

- Use cryptographically random opaque session tokens.
- Send the raw token only in a persistent HTTP-only cookie.
- Store a cryptographic digest of the token in PostgreSQL together with user, creation, expiration, and revocation data.
- Use a fixed seven-day lifetime with no sliding renewal.
- Revoke the server-side session immediately on logout.
- Ignore and lazily clean expired sessions.
- Use secure cookie attributes appropriate to the environment; production requires HTTPS.
- Enforce Organizer, Customer, and Gate roles in backend dependencies and service rules.
- Enforce organizer and customer resource ownership.
- Allow Gate users to validate any published event in the mandatory scope.

## Alternatives Considered

### JWT access tokens

They avoid a session lookup but make revocation and logout more complex. Ticket and session state already require PostgreSQL, so stateless authentication brings no current benefit.

### In-memory sessions

They are simple but disappear on restart and do not support multiple backend instances.

### Sliding sessions

They keep active users logged in indefinitely but require renewal writes or a more complex renewal threshold. A fixed seven-day session satisfies the challenge experience.

### Gate assignment per event

It provides narrower authorization but adds assignment management not required by the challenge. It remains a documented future improvement.

## Consequences

- Users stay logged in across browser restarts until logout or expiration.
- Every authenticated request performs a session lookup.
- Server-side revocation is immediate.
- Cross-origin cookie and CSRF behavior must be revisited for the selected production topology.
- A Gate account is intentionally broad in the mandatory implementation.

## Revisit When

- Third-party API consumers or mobile clients require token-based authentication.
- Production security requires session rotation, device management, or shorter lifetimes.
- Gate users must be assigned to specific organizers or events.
