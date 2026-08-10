# ADR-005: Password Hashing

## Status

Accepted

## Context

Seeded users must authenticate with passwords, and stored credentials must remain resistant to offline guessing if the database is exposed. Implementing a custom password-storage format would add security-sensitive code.

## Decision

- Use Argon2id through `pwdlib[argon2]`.
- Use `PasswordHash.recommended()` as the initial configuration and record the resulting parameters in implementation documentation.
- Store the self-describing password hash string in PostgreSQL.
- Run a dummy verification when the submitted identity does not exist to reduce username-enumeration timing differences.
- Never log, return, or seed plaintext passwords outside the documented local evaluator credentials.

## Alternatives Considered

### Python `hashlib.scrypt`

It is memory-hard and requires no dependency, but the project would need to define and maintain its own encoded hash format, parameter upgrades, and verification utilities.

### bcrypt

It is established and widely supported, but Argon2id is the recommended algorithm in the current FastAPI password-hashing guidance.

### Reversible encryption

It is inappropriate because authentication requires verification, not password recovery.

## Consequences

- A focused security dependency is added and must support Python 3.14.
- Hashing is deliberately expensive and must not run on the event loop.
- Stored hashes carry their parameters and can support future rehash decisions.
- Seed scripts must generate hashes through the same application utility used by authentication.

## Revisit When

- Security guidance or organizational policy changes.
- Measured login performance requires parameter tuning.
- Existing user hashes from another system must be migrated.
