# Next Task

## Task ID

RX-026 — Approval-Gated Real Funding Settlement Verification

## Objective

Add the smallest approval-gated funding settlement verification path for one existing Capture, one existing `RouteCandidate`, and one explicit funding settlement timestamp. It must reuse the existing funding settlement verification and append-only ledger boundaries, consume only explicitly approved observed settlement evidence, and remain non-trading.

## Starting baseline

Start from reviewer-accepted `main` after the one-route real-data research runner is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-026-approval-gated-funding-verification`. Do not implement on `main`.

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

- One funding settlement verification workflow for one explicit existing Capture, route, and settlement timestamp.
- Reuse existing funding settlement verification owner logic in `core/monitoring/funding_settlement.py`.
- Reuse existing append-only ledger event helpers in `core/accounting/ledger.py` when evidence or verification results must be recorded.
- Accept only explicit observed settlement evidence supplied by the caller or deterministic tests.
- Deterministic tests with injected fixtures only.
- Minimal app wiring only if needed.
- Required repository metadata updates after implementation.

## Forbidden scope

- No route ranking, broad discovery, watchlists, background loops, paper lifecycle changes, real-data route runner changes, execution planning, orders, live runner behavior, credentials, private endpoints, or live trading.
- No automatic venue polling or private account balance fetching.
- No second funding verifier, second ledger-write path, second replay path, second route decision path, or second snapshot assembly path.
- No EV, fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin filters.
- No canary architecture.
- No hold-next-cycle logic.
- No speculative helpers, wrappers, unused abstractions, or future hooks.
- Do not implement execution planning, guarded live runner behavior, order placement, monitoring, or dashboards.

## Implementation requirements

- Require explicit approval/evidence inputs before treating settlement data as observed.
- Unknown, missing, stale, malformed, cross-capture, cross-route, cross-settlement, unobserved, or contradictory evidence must fail closed.
- Verification must remain downstream of existing route decisions and snapshots and must not mutate route eligibility.
- Any ledger writes must use existing append-only ledger helpers; do not add update/delete behavior.
- Do not call `evaluate_route()`, assemble snapshots, calculate profitability, create plans, import execution/live runner modules, or place orders.
- Tests must inject observed evidence fixtures and avoid live network dependency.
- Worker policy: this task touches funding settlement and ledger boundaries, so one supervised worker/subagent is required before implementation edits. If worker tooling is unavailable, stop before edits and report the blocker. The worker must stop at DESIGN CHECKPOINT before edits and at CODE, TEST, and VALIDATION checkpoints if it continues.
- Parent owns steering, final diff review, validation, commit, push, and final report.

## Required files

- Likely `core/monitoring/funding_settlement.py`
- Likely `core/accounting/ledger.py`
- Likely focused tests under `tests/unit/` or `tests/replay/`
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside the owner modules required by the final design checkpoint.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused funding settlement verification tests for explicit observed evidence and fail-closed missing/malformed/contradictory evidence
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
