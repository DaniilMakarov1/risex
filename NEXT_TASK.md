# Next Task

## Task ID

RX-054 - Post-Manual Paper Bridge Handoff Clarification

## Objective

After the manual public paper-trader bridge is reviewer-accepted and finalized on `main`, inspect the accepted branch outcome and current source-of-truth docs to identify exactly one next non-dangerous fake-money paper-trader handoff if one is clearly grounded. If no such task is grounded, record the no-grounded-handoff conclusion and prepare one narrow Product Owner clarification gate instead of inventing route discovery, ranking, polling, execution automation, live trading, order placement, private/account endpoint, credential, account-state, ledger replay, reconciliation, or storage-migration scope.

## Starting baseline

Start from reviewer-accepted `main` after the manual public paper-trader bridge is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-054-post-manual-paper-bridge-handoff-clarification`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, the manual public paper-trader bridge is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous governance/source-of-truth work only. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Inspect the accepted manual paper bridge outcome and current source-of-truth docs.
- Record whether one concrete next non-dangerous fake-money paper-trader handoff is clearly grounded.
- Prepare exactly one next task in `NEXT_TASK.md`.
- Update source-of-truth metadata/docs only as needed to record the handoff clarification.
- Preserve accepted baseline versus current pending/review state.

## Forbidden scope

- No product/runtime code changes.
- No CLI behavior changes.
- No route discovery.
- No route ranking.
- No watchlists.
- No polling.
- No background loops.
- No scheduling.
- No alerts.
- No automatic refresh.
- No live trading.
- No live trading by default.
- No real exchange order placement.
- No order cancellation.
- No order status fetching.
- No private endpoints.
- No account endpoints.
- No credentials.
- No API keys or secrets.
- No exchange account state.
- No account balances.
- No account-tier assumptions.
- No sendable exchange request construction.
- No order payload construction.
- No execution automation.
- No execution planning.
- No guarded live runner execution.
- No approval-boundary execution.
- No adapter endpoint changes.
- No fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin rule changes.
- No funding settlement verification changes.
- No ledger reconciliation changes.
- No replay changes.
- No storage migrations.
- No route eligibility mutation.
- No Capture state transition changes.
- No route statuses.
- No reject reasons.
- No canary architecture.
- No hold-next-cycle logic.
- No unknown-to-zero behavior.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second decision path, second snapshot assembly path, second EV path, second VWAP path, second ledger-write path, second replay path, second execution-planning path, or second live execution path.

## Implementation requirements

- Treat this as governance/source-of-truth clarification only.
- Use the repository docs and accepted branch evidence as the source of truth; do not rely on chat memory or broad roadmap implication.
- If one concrete safe next fake-money paper-trader task is grounded, prepare exactly that one later task in `NEXT_TASK.md`.
- If clarification is absent, ambiguous, unsafe, or reaches a hard-stop category, record that no clarified runtime handoff is available and do not invent product/runtime scope.
- Preserve reviewer-only acceptance; implementation-complete branch work is not accepted until an explicit reviewer accepts it.
- Preserve the manual paper bridge as pending or accepted according to explicit reviewer evidence.
- Control Tower autonomous selection is allowed only because this is non-dangerous governance/source-of-truth work grounded in source-of-truth repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker required.
- The worker is required for design support before implementation edits because this is repository-governance/source-of-truth work.
- At DESIGN CHECKPOINT, the worker must answer whether the clarification is source-grounded, non-dangerous, one-task/one-branch compliant, preserves accepted baseline versus pending review state, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer-only acceptance, excludes all hard-stop categories, avoids invented runtime/live/order/private scope, avoids discovery/ranking/polling, preserves unknown-as-missing behavior, avoids new statuses/reasons and second owner paths, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Likely `STATUS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `DECISIONS.md`
- `NEXT_TASK.md`
- Other source-of-truth docs only if needed to keep the handoff consistent

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
