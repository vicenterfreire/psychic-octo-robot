# AI Collaboration Disclosure

## Tool Used

OpenAI Codex in the desktop application was used as a pair programmer throughout the challenge.
Its repository, terminal, browser-testing, and PDF-inspection capabilities supported local work.
No AI collaborator pushed commits, created a remote pull request, deployed the application, or
submitted the challenge.

## Collaboration Model

This project was not produced from one prompt followed by an unreviewed generated application. The
challenge was developed through a human-in-the-loop sequence of small, candidate-authorized local
commits. Before implementation, the challenge PDF and repository were inspected, requirements were
written down, and architecture choices were classified by impact. Stack, persistence,
authentication, password hashing, external integration, reservation behavior, ticket authenticity,
testing strategy, and deployment boundaries required an explicit candidate decision before work
continued.

The phrase `Pode fazer o próximo commit` appears in the versioned development policy because it was
occasionally the candidate's concise authorization to execute the next already planned and
discussed increment. It was not the prompt that specified or generated each feature. Requirements,
alternatives, decisions, code-review questions, requested refinements, validation results, and
learning checkpoints were exchanged around those authorizations throughout the development.

The candidate repeatedly paused implementation to inspect the Git history and code, question the
reasoning, and request changes. Examples include reviewing cache behavior and seed generation,
challenging the backend and frontend folder structures, requesting feature-local components and
hooks, selecting CSS Modules, preserving support for PostgreSQL outside Podman, choosing temporary
inventory holds from a customer perspective, asking for focused machine-readable test hooks, and
requesting Dockerfiles, Compose execution, and interactive API documentation. These interventions
changed or refined the delivered repository; they were not post-hoc approval of a finished system.

Codex performed substantial implementation and validation work, but it operated under the
versioned `AGENTS.md` policy: inspect before changing, explain behavior-affecting choices, stop for
candidate-owned decisions, implement one coherent increment, report what the candidate should
understand, and wait for authorization before continuing. The candidate remains the technical
owner because the direction, accepted trade-offs, review checkpoints, local runtime preparation,
credentials, publication, and final defense stayed under candidate control—not because AI
involvement was hidden or reduced to wording.

## AI-Assisted Work

Codex accelerated:

- extraction and cross-checking of requirements from the challenge PDF;
- repository navigation, boilerplate, repetitive mappings, and implementation drafts;
- focused backend, frontend, PostgreSQL integration, and browser-test creation;
- local command execution, failure investigation, and machine-readable test reporting;
- documentation, ADR, TODO, and knowledge-base maintenance;
- review of the final evaluator instructions against the implemented repository.

Generated work was accepted incrementally only after the relevant local checks. The Git history is
not intended to disguise AI involvement; it records the actual reviewed development sequence. The
implementation commits are therefore evidence of collaboration checkpoints, not a claim that every
line was typed manually by the candidate.

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
planned commit. The candidate also performed a later commit-by-commit code review, challenged
choices that were not convincing, and requested documented counterarguments before accepting the
result. Remote publication and challenge submission remain candidate-only actions.

## Shared Review Boundary

Codex could implement YELLOW behavior after explaining its structure, alternatives, limitations,
and interview relevance. RED decisions required the candidate's response before implementation.
The candidate remains responsible for understanding, modifying, demonstrating, and defending the
final solution; local validation is evidence, not a substitute for that ownership.

## Versioned Intermediate Artifacts

The repository preserves the useful collaboration trail:

- `AGENTS.md` defines the human-in-the-loop development policy.
- `TODO.md` records the ordered commit plan, validation performed, and completed increments.
- `docs/requirements/` records the interpreted requirements and constraints.
- `docs/architecture/decisions/` records accepted choices and rejected alternatives.
- `docs/knowledge-base/` explains the domain and implementation boundaries.
- `docs/development/` records workflow, database operations, current state, mutation evaluation,
  and this disclosure.
- `docs/future-improvements.md` separates deliberate simplifications from unfinished mandatory
  behavior.

Secrets, generated test reports, local environments, and private interview notes are intentionally
not versioned.
