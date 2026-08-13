# Next Task

## Task ID

RX-051 - Product Owner Concrete Post-RX-048 Public Runtime Handoff Clarification

## Objective

After RX-050 reviewer acceptance, inspect the accepted RX-050 no-clarified-runtime-handoff conclusion, current source-of-truth docs, and any explicit Product Owner or Control Tower clarification supplied for exactly one concrete safe public/read-only/non-trading runtime handoff after the accepted RX-048 structured JSON stdout public readiness report. If explicit clarification clearly identifies one concrete safe task, prepare exactly that one later task in `NEXT_TASK.md`. If clarification is absent, ambiguous, unsafe, or reaches a hard-stop category, record the no-clarified-runtime-handoff conclusion and prepare one narrow Product Owner or Control Tower clarification handoff rather than inventing route discovery, ranking, polling, private endpoint, account-state, order, execution automation, execution planning, ledger/storage/replay, or live-trading scope.

## Starting baseline

Start from reviewer-accepted `main` after RX-050 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-051-product-owner-concrete-post-rx-048-public-runtime-handoff-clarification`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-050 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous: governance/source-of-truth clarification only unless one exact safe public/read-only/non-trading runtime handoff is explicitly clarified, with no live trading, private/account endpoints, credentials, orders, sendable exchange request construction, execution automation, execution planning, account-state access, ledger/storage/replay changes, destructive reset, unsafe scope, or financially dangerous action. Stop before edits unless explicit user approval exists for any hard-stop category.

Read:

- AGENTS.md
- README.md
- ARCHITECTURE.md
- PRODUCT_INVARIANTS.md
- IMPLEMENTATION_PLAN.md
- STATUS.md
- DECISIONS.md
- NEXT_TASK.md
- docs/WORKFLOW.md
- Relevant templates in `docs/templates/`

## Allowed scope

- Inspect accepted RX-050 Product Owner direction-gate outcome, accepted RX-049 governance/source-of-truth clarification outcome, accepted RX-048 structured JSON stdout public readiness report outcome, current source-of-truth docs, and any explicit Product Owner or Control Tower clarification supplied for the next public/read-only/non-trading handoff.
- Update source-of-truth docs to record whether explicit clarification clearly identifies one concrete safe next public/read-only/non-trading runtime task after RX-048.
- If one concrete safe next task is grounded, prepare exactly that one later task in `NEXT_TASK.md`.
- If no concrete safe task is grounded, prepare exactly one narrow Product Owner or Control Tower clarification handoff in `NEXT_TASK.md`.
- Preserve the latest accepted product/reporting baseline and latest accepted governance/source-of-truth task separately from current branch work.
- Preserve reviewer-only acceptance and do not mark RX-051 or any later task accepted without explicit reviewer acceptance.

## Forbidden scope

- No product/runtime behavior changes. Explicit clarification may select one later task, but RX-051 must not implement runtime behavior.
- No route discovery.
- No route ranking.
- No watchlists.
- No background loops.
- No polling.
- No scheduling.
- No alerts.
- No automatic refresh.
- No adapters or adapter endpoint changes.
- No private endpoints.
- No credentials.
- No API keys or secrets.
- No account balances.
- No exchange account state.
- No account-tier assumptions.
- No fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin rule changes.
- No order placement.
- No order cancellation.
- No order status fetching.
- No sendable exchange request construction.
- No order payload construction.
- No execution automation.
- No execution planning.
- No guarded live runner execution.
- No approval-boundary execution.
- No ledger writes.
- No storage migrations.
- No replay changes.
- No paper lifecycle changes.
- No funding settlement verification.
- No ledger reconciliation.
- No route eligibility mutation.
- No Capture state transitions.
- No route statuses.
- No reject reasons.
- No canary architecture.
- No hold-next-cycle logic.
- No live trading.
- No live trading by default.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second decision path, second snapshot assembly path, second EV path, second VWAP path, second ledger-write path, second replay path, second execution-planning path, or second live execution path.

## Implementation requirements

- Treat this as a narrow governance/source-of-truth concrete clarification gate. Explicit Product Owner or Control Tower clarification may ground one exact safe later runtime handoff, but RX-051 must only record and prepare that later task.
- Use repository docs, accepted code paths, and explicit Product Owner or reviewer evidence only; do not rely on chat memory or broad roadmap implication.
- Keep `NEXT_TASK.md` as exactly one next task and require the handoff validator to pass.
- Preserve Control Tower autonomy for ordinary non-dangerous tasks grounded in source-of-truth repository docs.
- Preserve one RX task equals one clean executor task and one task branch.
- Preserve Parent ownership of branch discipline, final diff review, validation, commit, push, and final report.
- Preserve RX-048 as the latest accepted product/reporting baseline unless a later reviewer-accepted product task exists.
- Preserve RX-050 as pending or accepted according to explicit reviewer evidence.
- Worker policy: one supervised worker required because this task is repository-governance/source-of-truth work.
- The worker is required for design support before implementation edits and may continue only if Parent explicitly asks for implementation support.
- At DESIGN CHECKPOINT, the worker must answer whether the planned handoff is source-grounded, non-dangerous, one-task/one-branch compliant, preserves accepted baseline versus pending review state, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer-only acceptance, excludes all hard-stop categories, avoids invented runtime scope, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Likely README.md
- Likely ARCHITECTURE.md
- Likely PRODUCT_INVARIANTS.md
- Likely IMPLEMENTATION_PLAN.md
- Likely STATUS.md
- Likely DECISIONS.md
- Likely NEXT_TASK.md

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
