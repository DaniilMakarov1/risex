# Next Task

## Task ID

RX-071 - Post-Local Operator Display Fail-Closed Handoff Clarification

## Objective

After RX-070 reviewer acceptance and finalization, inspect the accepted fake-money paper-session operator/display chain, the RX-070 fail-closed smoke coverage outcome, current source-of-truth docs, and Product Owner direction to determine the next safe handoff.

This is governance/source-of-truth only unless the accepted docs clearly ground exactly one non-dangerous local/manual/fake-money runtime or testability task. Do not infer Telegram transport, credentials, messaging/network behavior, execution automation, live/order/private/account scope, aggregate PnL calculation, unknown-to-zero behavior, or second owner paths from the local smoke coverage.

## Starting baseline

Start from reviewer-accepted `main` after RX-070 finalization. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-071-post-local-operator-display-fail-closed-handoff-clarification`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-070 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, governance/source-of-truth only by default, and grounded in the accepted fake-money paper trader artifact chain. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Source-of-truth inspection and documentation updates only by default.
- Record whether a concrete safe next local/manual/fake-money runtime or testability handoff is clearly grounded after accepted RX-070 coverage.
- If no concrete safe handoff is grounded, record that conclusion and prepare exactly one next clarification task.
- If exactly one safe handoff is clearly grounded, prepare `NEXT_TASK.md` for that one task without implementing runtime or test code in RX-071.
- Preserve the accepted baseline versus current task branch review-state distinction.
- Keep `NEXT_TASK.md` to exactly one next task and keep `python3 scripts/validate_next_task.py` passing.

## Forbidden scope

- No product/runtime implementation unless a tiny docs-consistency fix strictly requires touching wording only.
- No new user-facing CLI command.
- No production route, session, decision, snapshot, economics, paper lifecycle, ledger, report, display, parser, or command path changes.
- No parser weakening.
- No test expansion unless needed only to validate documentation tooling.
- No real Telegram transport.
- No Telegram bot tokens.
- No webhooks.
- No alerts or messaging behavior.
- No external network calls.
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

- Inspect accepted RX-070 outcome from git and docs after finalization, not from chat memory.
- Inspect current source-of-truth docs for whether one concrete safe post-coverage handoff is grounded.
- Treat Telegram as later interface direction only unless an exact future task is explicitly authorized; do not introduce Telegram transport, credentials, messaging/network behavior, webhooks, alerts, or bot tokens.
- Do not implement any runtime, parser, display, session, adapter, ledger, or test behavior in this task.
- Update `STATUS.md` so the latest accepted baseline remains separate from the current task branch and current task review state.
- Update `DECISIONS.md` only for actual governance/source-of-truth decisions made by this task.
- Prepare `NEXT_TASK.md` with exactly one next task.
- Use `docs/WORKFLOW.md` and `docs/templates/` for the handoff and final report.
- Control Tower autonomous selection is allowed only because this is non-dangerous governance/source-of-truth work grounded in repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker/subagent required for design support because this is a repository-governance/source-of-truth handoff clarification task.
- The worker must answer whether exactly one safe next handoff is grounded, whether the fallback should be another clarification task, and whether any hard-stop category would require explicit user approval.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- If the worker continues beyond design support, it must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT before continuing to the next phase.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- README.md
- ARCHITECTURE.md
- PRODUCT_INVARIANTS.md
- IMPLEMENTATION_PLAN.md
- STATUS.md
- DECISIONS.md
- NEXT_TASK.md

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant -q`
- `python3 -m pytest -q`
- `python3 -m compileall apps core storage tests scripts`
- `python3 -m apps.cli.main`
- `git diff --check`
- `git diff --cached --check`
- Focused stale cross-project instruction search
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
