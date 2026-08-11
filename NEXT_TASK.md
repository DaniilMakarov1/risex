# Next Task

## Task ID

RX-020 — RouteCandidate Identity And Notional Contract Hardening

## Objective

Harden the existing `RouteCandidate` identity and target-notional contracts so malformed route identity or notional inputs fail closed before they can enter snapshot assembly, route evaluation, paper lifecycle, ledger evidence, or future live-gate evidence. Keep the work inside the existing modular-monolith owner boundaries and preserve RX-018 as the latest accepted product baseline.

## Starting baseline

Start from the reviewer-accepted `main` baseline after RX-019 metadata follow-up. Before edits, verify the exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-020-routecandidate-identity-notional-contract-hardening`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, or unrelated branch work would be mixed into this task.

Read:

- AGENTS.md
- README.md
- ARCHITECTURE.md
- PRODUCT_INVARIANTS.md
- IMPLEMENTATION_PLAN.md
- STATUS.md
- DECISIONS.md
- NEXT_TASK.md

## Allowed scope

- Existing `RouteCandidate` construction and validation contracts.
- Existing route identity fields: capture id, route id, venues, symbols, entry sides, and target notional.
- Existing route/snapshot alignment and route evaluation tests that prove malformed identity or notional inputs fail closed through current owner modules.
- Repository metadata updates required by `AGENTS.md` after implementation.

## Forbidden scope

- No product strategy changes.
- No new route statuses.
- No new `RejectReason` values.
- No standalone spread, price-impact, basis, slippage, max-level, hidden-buffer, or safety-margin filters.
- No EV, fee, funding, VWAP/liquidity, basis, ledger-write, replay, or snapshot second path.
- No adapters, network calls, API clients, credentials, secrets, orders, live runner behavior, live trading, executable `CapturePlan`, or executable order plan.
- No canary architecture.
- No hold-next-cycle logic.
- No speculative helpers, wrappers, unused abstractions, or future hooks.
- Do not implement any task beyond this contract-hardening scope.

## Implementation requirements

- Preserve `RouteCandidate` as the authoritative route identity and notional contract.
- Preserve `assemble_route_snapshot()` as the single route snapshot assembly path.
- Preserve `evaluate_route(route, snapshot, mode)` as the single route decision path.
- Keep identity and notional validation deterministic and fail-closed.
- Unknown or malformed values must not silently become empty strings, zero, or default notional.
- Use existing owner modules and existing centralized rejection behavior wherever possible.
- Add or adjust only focused tests that prove valid route candidates still pass and malformed identity/notional candidates fail closed.
- Worker policy: this is broad contract hardening, so one supervised worker/subagent is required before implementation edits. If worker tooling is unavailable, stop before edits and report the blocker. The worker must stop at DESIGN CHECKPOINT before edits and at CODE, TEST, and VALIDATION checkpoints if it continues.
- Parent owns steering, final diff review, validation, commit, push, and final report.

## Required files

- Likely `core/domain/contracts.py`
- Likely focused unit or invariant tests under `tests/`
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside the owner modules required by the final design checkpoint.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused tests for route candidate identity and notional contract behavior
- `python3 -m pytest`
- `python3 -m compileall apps core storage tests scripts`
- `python3 -m apps.cli.main`
- `git diff --check`
- `git diff --cached --check`
- `git status --short`

## Required report format

Return one fenced Markdown code block with no prose outside.

Include:

- Task ID
- Repository path
- Branch
- Starting HEAD
- Final HEAD
- Changed files
- What was implemented
- New functions/classes/contracts added and why each was necessary
- Tests run
- Exact test results
- Working-tree status
- Known limitations
- Risk impact
- Orchestration log
- Next suggested task
