# Next Task

## Task ID

RX-017 - Reviewer-Directed Follow-up After RX-016

## Objective

Handle only explicit reviewer direction after the RX-016 task branch is reviewed. If fixes are requested, apply the requested corrections in the existing RX-016 branch and keep them inside the original RX-016 scope. If RX-016 is accepted with no fixes, wait for the user to provide the accepted `main` baseline and the next concrete RX task prompt before changing files.

## Starting baseline

Start from the reviewer-designated state after RX-016 review. For same-branch fixes, use the existing RX-016 task branch. For any new product task, stop unless the user provides the accepted `main` baseline and a concrete task prompt.

## Branch

For RX-016 review fixes, continue on `task/rx-016-sqlite-ledger-reopen-fail-closed-replay`. Do not create a new branch unless the user provides a new concrete RX task.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, or HEAD does not match the reviewer-designated starting state.

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

- Files explicitly named by reviewer feedback.
- For same-branch RX-016 fixes, stay inside the original RX-016 allowed scope unless the reviewer explicitly expands it.
- If there is no reviewer-requested fix and no new concrete task prompt, no files may be changed.

## Forbidden scope

- No product behavior changes beyond explicit reviewer-requested RX-016 fixes.
- No route evaluation changes.
- No risk gate behavior changes unless reviewer feedback identifies a persistence/replay bug that makes existing replay impossible, and then keep the change narrowly scoped.
- No economics changes.
- No VWAP/liquidity recalculation changes.
- No standalone spread, price-impact, basis, slippage, max-level, hidden-buffer, or safety-margin filters.
- No live runner behavior.
- No adapters, orders, network calls, API clients, credentials, secrets, or trading logic.
- No executable `CapturePlan` or executable order plan.
- No live trading enablement.
- No new route statuses.
- No new `RejectReason` values.
- No canary architecture.
- No hold-next-cycle logic.
- No second route model, EV path, decision path, snapshot assembly path, VWAP path, ledger-write path, replay module, or live execution path.
- No broad refactors.
- No speculative helpers or future hooks.

## Implementation requirements

- Treat reviewer feedback as the only source of scope for this follow-up.
- Preserve `SQLiteLedger` as the existing minimal append-only persistence contract unless reviewer feedback identifies a narrow storage bug.
- Do not introduce migrations or a second storage layer.
- Do not recalculate EV, fees, funding, VWAP, basis, or profitability in SQLite replay tests.
- Do not call adapters, call execution modules, place orders, create live plans, mutate route eligibility decisions, or return `LIVE_ELIGIBLE`.
- Worker policy: one supervised worker is required for any non-trivial architecture-sensitive fix; otherwise workers are optional for tiny reviewer-requested fixes.
- A required worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- A required worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Reviewer-requested files only.
- If no fixes are requested, no files are required.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
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
