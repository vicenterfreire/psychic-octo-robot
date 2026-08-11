# Bounded Mutation Testing Evaluation

## Outcome

The initial automated mutation-testing experiment is deferred. `mutmut` remains the selected tool under ADR-008, but it was not added to the project because neither approved package-resolution route could reach PyPI on 2026-08-11:

- `uv add --dev mutmut` exhausted its retries while resolving the package index.
- `python -m pip index versions mutmut` exhausted its retries through the same unavailable local proxy.

Both attempts left `pyproject.toml`, `uv.lock`, and the virtual environment unchanged. The repository does not declare an unavailable dependency, contain guessed tool configuration, or require mutation testing for normal validation.

Building a project-specific mutation runner was rejected. It would add unproven test infrastructure, create more code to validate, and conflict with the candidate's condition that mutation testing must not threaten the delivery deadline.

## Selected Tool

`mutmut` remains the recommendation because ADR-008 already accepts it for a bounded Python experiment. Its exact version and current Python 3.14 compatibility must be resolved from PyPI and locked by `uv` when network access is restored; no version is asserted from memory.

## Planned Scope

The first run must mutate only these business-critical modules:

- `src/backend/auth/authorization.py`
- `src/backend/reservations/service.py`
- `src/backend/tickets/signing.py`
- `src/backend/gate/service.py`

The matching test selection is deliberately small:

- `tests/test_authorization.py`
- `tests/test_ticket_signing.py`
- `tests/integration/test_reservations.py`
- `tests/integration/test_gate.py`

The experiment must use a disposable `elite_dev_mutation` PostgreSQL database prepared through the same migration and seed boundary as the critical suite. It must never target `elite_dev`.

## Exclusions

The first experiment excludes routers, schemas, provider transport, SQLAlchemy models, migrations, seed code, frontend code, generated artifacts, and low-risk framework glue. These areas either have a lower business risk, are already protected indirectly, or would expand runtime without improving the first decision.

Concurrency tests remain in the selected test files because overselling and duplicate admission are critical. If the tool cannot execute them reliably in its worker model, that incompatibility must be recorded rather than silently dropping the tests.

## Time and Stop Limits

- Resolve and inspect the current tool interface before writing configuration.
- Establish a passing selected-test baseline against the disposable database.
- Limit the entire first mutation run and survivor review to 20 minutes.
- Limit an individual mutant's selected tests to 30 seconds where the current tool supports that control.
- Start with authorization and signing; continue to reservation and gate services only while the total timebox remains safe.
- Stop on repeated infrastructure failures, database-state leakage, or any threat to final evaluator documentation.
- Do not make zero surviving mutants a delivery gate.

## Survivor Review Policy

Review a survivor only when it changes an observable authorization, inventory, payment, signature, or one-time admission rule. Add a test when the mutant exposes a meaningful missing assertion. Record equivalent or unreachable mutants instead of distorting production code merely to kill them.

The manual sensitivity check from commit `1216a36` already showed that removing HMAC comparison makes the tampering test fail. That is useful evidence, but it is not presented as an automated `mutmut` result.

## Resume Procedure

When PyPI access is restored:

1. Confirm the current `mutmut` release metadata and Python 3.14 support.
2. Add it to the backend development group through `uv` and commit the resolved lock change.
3. Inspect the installed command help and official configuration reference.
4. Configure only the scope and tests listed above.
5. Add an isolated `elite_dev_mutation` hook with guaranteed cleanup.
6. Run the timeboxed experiment and record killed, survived, timeout, and suspicious results.
7. Keep or remove the dependency based on whether the evidence justifies its maintenance cost.
