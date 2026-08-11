# ADR-009: Frontend Module Organization

## Status

Accepted

## Context

The completed React application grew from one file per feature into features that contain route
pages, reusable UI, hooks, API contracts, and tests. Keeping every file at the feature root makes
larger modules harder to scan, while organizing the entire application into global `Pages`,
`Components`, and `Hooks` directories separates code that changes for the same business flow.

The review also questioned whether interfaces should always live in separate files and whether the
existing custom CSS should be replaced by Tailwind CSS.

## Decision

- Keep product features as the primary frontend boundary.
- Keep route pages, API contracts, feature utilities, and their focused tests at the feature root.
- Put supporting React components in `components/` inside the feature that owns them.
- Put custom React hooks in `hooks/` inside the feature that owns them.
- Create neither directory when a feature has no matching files.
- Move UI used by several flows to the feature that owns its cross-cutting responsibility; the
  shared public/authenticated header belongs to `navigation/components/`.
- Move generic display helpers that accept primitive values to `src/lib/` instead of making one
  feature depend on another feature's presentation module.
- Keep transport interfaces beside the feature API that owns the contract and component props
  beside their single consumer. Extract types only when they gain multiple owners or an independent
  lifecycle.
- Retain the current custom CSS and visual language. Do not add Tailwind CSS solely to replace
  working styles after the mandatory flow is complete.

## Alternatives Considered

### Global `Pages`, `Components`, and `Hooks` directories

This is familiar and gives each technical type one obvious location, but a change to reservations
or tickets would span several distant directory trees. It optimizes lookup by framework construct
rather than by product behavior.

### Keep every file at each feature root

This remains effective for small features, but the larger authentication, event, reservation, and
gate modules now contain enough supporting UI to benefit from one local level of grouping.

### One file per TypeScript interface

It makes interfaces mechanically uniform but adds navigation for small contracts with one owner.
Ownership and reuse are stronger extraction signals than the fact that a declaration is an
interface.

### Migrate to Tailwind CSS

Tailwind can accelerate utility-first composition, but it is not included by React or Vite in this
project. Adding it now would introduce a dependency and rewrite stable visual work without solving
a challenge requirement.

## Consequences

- A feature remains understandable from one directory subtree.
- Larger features gain predictable `components/` and `hooks/` locations without empty ceremony.
- Route imports become slightly longer but communicate whether an element is a page or supporting
  UI.
- Cross-feature dependencies must be reviewed; shared navigation and generic formatting cannot be
  owned accidentally by discovery.
- Existing CSS remains a large shared stylesheet and may be split mechanically later if that
  improves maintenance without changing the styling strategy.

## Revisit When

- Multiple features require the same hooks or components and no existing feature clearly owns
  them.
- A design system or component library becomes a concrete requirement.
- The team deliberately chooses a utility-first styling workflow for future development rather
  than as a post-delivery rewrite.
