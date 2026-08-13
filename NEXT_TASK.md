# Next Task

## Task ID

RX-069 - Post-RX-068 Fake-Money Paper Trader Handoff Clarification

## Objective

After RX-068 reviewer acceptance and finalization, inspect the accepted package-to-runtime smoke coverage outcome plus the current source-of-truth docs and record exactly one safe next handoff for the fake-money paper trader path.

This is a governance/source-of-truth clarification task only. It should determine whether the accepted docs and explicit Product Owner/Control Tower direction clearly ground one concrete non-dangerous local/manual/fake-money next step after package-to-runtime coverage. If a concrete safe next step is grounded, prepare that single next handoff. If not, record the no-grounded-handoff conclusion and prepare a narrow follow-up clarification handoff. Do not implement product/runtime behavior in this task.

## Starting baseline

Start from reviewer-accepted `main` after RX-068 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-069-post-rx-068-fake-money-paper-trader-handoff-clarification`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-068 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, governance/source-of-truth only, and grounded in the accepted fake-money paper trader docs. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Update source-of-truth docs to record the post-RX-068 handoff analysis and outcome.
- Prepare `NEXT_TASK.md` with exactly one next task.
- If a concrete safe next handoff is clearly grounded, describe it as local/manual/fake-money only and keep all hard-stop categories excluded.
- If no concrete safe next handoff is clearly grounded, prepare a narrow clarification handoff rather than inventing runtime scope.
- Documentation-only changes are expected.

## Forbidden scope

- No product/runtime code changes.
- No tests except documentation/governance validation if strictly needed.
- No new user-facing CLI command.
- No behavior changes to existing CLI output.
- No parser changes or parser weakening.
- No real Telegram transport.
- No Telegram bot tokens.
- No webhooks.
- No external network calls.
- No alerts or messaging behavior.
- No credentials.
- No API keys or secrets.
- No live trading.
- No live trading by default.
- No real exchange order placement.
- No order cancellation.
- No order status fetching.
- No private endpoints.
- No account endpoints.
- No exchange account state.
- No account balances.
- No account-tier assumptions.
- No sendable exchange request construction.
- No order payload construction.
- No execution automation.
- No execution planning.
- No guarded live runner execution.
- No approval-boundary execution.
- No route discovery.
- No route ranking.
- No watchlists.
- No polling.
- No background loops.
- No scheduling.
- No automatic refresh.
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
- No aggregate PnL invention or calculation.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second session runner, second decision path, second snapshot assembly path, second EV path, second VWAP path, second fee/funding path, second paper lifecycle path, second ledger-write path, second report path, second display path, second replay path, second reconciliation path, second execution-planning path, or second live execution path.

## Implementation requirements

- Keep the task documentation/governance only.
- Inspect the accepted RX-068 outcome and the current source-of-truth docs before deciding the next handoff.
- Preserve the distinction between latest accepted baseline, current task branch state, and reviewer acceptance.
- Do not describe RX-069 implementation-complete work as reviewer-accepted.
- Keep `NEXT_TASK.md` to exactly one task and require `python3 scripts/validate_next_task.py` to pass.
- Use `docs/WORKFLOW.md` and `docs/templates/` for the handoff and final report.
- Control Tower autonomous selection is allowed only because this is non-dangerous governance/source-of-truth work grounded in repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker required for design support only because this is a repository-governance task.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and answer whether a concrete safe post-RX-068 handoff is source-grounded or whether the branch should record a no-grounded-handoff clarification outcome.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- `README.md`
- `ARCHITECTURE.md`
- `PRODUCT_INVARIANTS.md`
- `IMPLEMENTATION_PLAN.md`
- `STATUS.md`
- `DECISIONS.md`
- `NEXT_TASK.md`

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused docs/search checks proving the handoff remains governance/source-of-truth only and `NEXT_TASK.md` contains exactly one task.
- Focused search checks proving no product/runtime code, CLI command, Telegram, network, credential, live/order/private/account, discovery/ranking/polling/scheduling, aggregate-PnL, unknown-to-zero, or second-owner-path scope was introduced.
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
