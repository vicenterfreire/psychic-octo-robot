# Development Workflow

## Purpose

Development is incremental and human-in-the-loop. AI removes mechanical cost, while the candidate owns architecture, security, domain rules, important dependencies, and trade-offs.

## Commit Cycle

Each planned `TODO.md` entry represents one coherent local commit.

1. The candidate asks: `Pode fazer o próximo commit`.
2. Inspect `AGENTS.md`, the next TODO entry, affected files, Git status, and local history.
3. Classify decisions as GREEN, YELLOW, or RED.
4. Stop and ask the candidate when a RED decision is unresolved.
5. Implement only the planned scope.
6. Validate relevant formatting, linting, types, tests, build, migration, or manual flow.
7. Update documentation and `TODO.md` to match reality.
8. Stage the complete coherent increment.
9. Create one descriptive local commit.
10. Report the result and stop before the next TODO entry.

## Decision Policy

- **GREEN:** low-risk mechanics such as formatting, basic mappings, and boilerplate.
- **YELLOW:** behavior and structure that may be implemented after explaining alternatives, limitations, and what the candidate should understand.
- **RED:** architecture, stack, database, ORM, authentication, authorization, security, domain boundaries, major dependencies, deployment, and major testing strategy. Candidate approval and an ADR are required.

## Validation Policy

- Never report a command as successful unless it actually completed successfully.
- Investigate and fix in-scope failures before committing.
- Document unrelated failures rather than hiding them.
- Use PostgreSQL for tests whose result depends on PostgreSQL transactions or locking.
- Re-run the relevant checks after a meaningful fix.

Frequently repeated commands remain root npm scripts. A checked-in PowerShell hook is used when the command needs platform-specific executable discovery, environment orchestration, or stable machine-readable output. `npm run test:report` writes ignored Vitest JSON, pytest JUnit XML, and a compact summary JSON under `.artifacts/test-results/`; generated reports never enter Git history.

## Dependency Policy

- Frontend dependencies are declared and locked by npm.
- Backend dependencies are declared in `pyproject.toml` and locked in `uv.lock`.
- `requirements.txt` is generated from `uv.lock` for compatibility and must never be edited manually.
- Any change to backend dependencies must refresh and validate both derived files in the same commit.
- Dependencies require a concrete requirement and an explanation the candidate can defend.

## Git Policy

- Use English descriptive commit messages.
- Preserve the existing published history.
- Do not combine unrelated changes.
- Do not rewrite published commits.
- The AI collaborator never pushes, opens remote pull requests, publishes releases, or otherwise changes the remote repository.

## Documentation Policy

- Update the current-state document after meaningful changes.
- Preserve superseded ADRs rather than deleting architectural history.
- Record intentionally deferred work in `docs/future-improvements.md`.
- Keep the final README executable as an evaluator guide, not as aspirational documentation.
