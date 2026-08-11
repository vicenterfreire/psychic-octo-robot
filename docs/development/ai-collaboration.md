# AI Collaboration Disclosure

## Tool Used

OpenAI Codex in the desktop application was used as a pair programmer throughout the challenge.
Its repository, terminal, browser-testing, and PDF-inspection capabilities supported local work.
No AI collaborator pushed commits, created a remote pull request, deployed the application, or
submitted the challenge.

## AI-Assisted Work

Codex accelerated:

- extraction and cross-checking of requirements from the challenge PDF;
- repository navigation, boilerplate, repetitive mappings, and implementation drafts;
- focused backend, frontend, PostgreSQL integration, and browser-test creation;
- local command execution, failure investigation, and machine-readable test reporting;
- documentation, ADR, TODO, and knowledge-base maintenance;
- review of the final evaluator instructions against the implemented repository.

Generated work was accepted incrementally only after the relevant local checks. The Git history is
not intended to disguise AI involvement; it records the actual reviewed development sequence.

## Candidate-Owned Work

The candidate made and approved the architectural, security, domain, dependency, and testing
decisions that define the solution, including:

- React, Vite, and TypeScript with Python and FastAPI;
- PostgreSQL through Podman and a Compose-compatible workflow;
- Ticketmaster as the only external catalog;
- opaque, persistent database sessions;
- Argon2id password hashing;
- temporary expiring inventory holds;
- HMAC-signed persistent ticket credentials;
- risk-focused tests and a bounded mutation-testing experiment.

The candidate also installed and started Python, `uv`, and Podman locally, supplied the untracked
Ticketmaster credential, reviewed the explanations and trade-offs, and explicitly authorized each
planned commit. Remote publication and challenge submission remain candidate-only actions.

## Shared Review Boundary

Codex could implement YELLOW behavior after explaining its structure, alternatives, limitations,
and interview relevance. RED decisions required the candidate's response before implementation.
The candidate remains responsible for understanding, modifying, demonstrating, and defending the
final solution; local validation is evidence, not a substitute for that ownership.

## Versioned Intermediate Artifacts

The repository preserves the useful collaboration trail:

- `AGENTS.md` defines the human-in-the-loop development policy.
- `TODO.md` records the ordered commit plan and completed increments.
- `docs/requirements/` records the interpreted requirements and constraints.
- `docs/architecture/decisions/` records accepted choices and rejected alternatives.
- `docs/knowledge-base/` explains the domain and implementation boundaries.
- `docs/development/` records workflow, database operations, current state, mutation evaluation,
  and this disclosure.
- `docs/future-improvements.md` separates deliberate simplifications from unfinished mandatory
  behavior.

Secrets, generated test reports, local environments, and private interview notes are intentionally
not versioned.
