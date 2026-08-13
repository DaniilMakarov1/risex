# Next Task

## Task ID

RX-044 - Product Owner Concrete Public Runtime Handoff Clarification

## Objective

After RX-043 is reviewer-accepted, inspect the source-of-truth repository docs, the accepted RX-043 conclusion, and any explicit Product Owner clarification supplied through Control Tower to prepare exactly one next handoff. Prefer a concrete narrow public/read-only/non-trading runtime live-readiness task only if it is clearly grounded in the docs and explicit Product Owner clarification. If no such safe runtime task is clearly grounded, record that conclusion and prepare one narrow clarification handoff instead of inventing product/runtime scope.

## Starting baseline

Start from reviewer-accepted `main` after RX-043 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-044-product-owner-concrete-public-runtime-handoff-clarification`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-043 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous: source-of-truth clarification and next-handoff preparation only, with no live trading, private/account endpoints, credentials, orders, sendable exchange request construction, automation, account-state access, destructive reset, unsafe scope, or financially dangerous action. Stop before edits unless explicit user approval exists for any hard-stop category.

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

- Inspect the accepted RX-043 conclusion and current source-of-truth docs.
- Inspect only explicit Product Owner clarification supplied through Control Tower or recorded in source-of-truth docs.
- Decide whether exactly one safe, concrete, public/read-only, non-trading next runtime handoff is clearly grounded by the docs and explicit Product Owner clarification.
- If a safe runtime handoff is clearly grounded, write exactly that one future task into `NEXT_TASK.md`.
- If no safe runtime handoff is clearly grounded, record the no-clarified-runtime-handoff conclusion and prepare one narrow clarification handoff.
- Update only governance/source-of-truth docs needed to record the outcome and next handoff.
- Preserve accepted baseline and current task review state accurately.

## Forbidden scope

- No product/runtime behavior changes.
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
- No speculative product hooks, runtime hooks, placeholder live paths, broad refactors, second route model, second decision path, second snapshot assembly path, second EV path, second VWAP path, second ledger-write path, second replay path, second execution-planning path, or second live execution path.

## Implementation requirements

- Treat this as an ordinary non-dangerous governance/source-of-truth task unless the docs and explicit Product Owner clarification clearly ground a later safe runtime handoff for a future task.
- Do not implement any product/runtime behavior.
- Use only repository source-of-truth docs and explicit reviewer/Product Owner evidence; do not rely on chat memory or broad roadmap implication.
- Preserve the latest accepted product baseline separately from any current task branch or pending review state.
- Do not mark any task accepted unless explicit reviewer acceptance exists.
- Keep `NEXT_TASK.md` as exactly one next task and require the handoff validator to pass.
- Preserve Control Tower autonomy for ordinary non-dangerous tasks grounded in source-of-truth repository docs.
- Preserve one RX task equals one clean executor task and one task branch.
- Preserve Parent ownership of branch discipline, final diff review, validation, commit, push, and final report.
- Worker policy: one supervised worker required because this is repository-governance/source-of-truth work.
- The worker is required for design support before implementation edits and may continue only if Parent explicitly asks for implementation support.
- At DESIGN CHECKPOINT, the worker must answer whether the planned Product Owner clarification outcome is docs/governance-only, non-dangerous, source-grounded, one-task/one-branch compliant, preserves accepted baseline versus pending review state, avoids inventing product/runtime scope, excludes all hard-stop categories, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer acceptance, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Likely `STATUS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `DECISIONS.md`
- Likely `NEXT_TASK.md`
- Other source-of-truth docs only if strictly necessary.

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused validation only if docs tooling changes; otherwise no focused product tests are required for docs-only work.
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
