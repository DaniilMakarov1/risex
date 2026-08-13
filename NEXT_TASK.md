# Next Task

## Task ID

RX-057 - Product Owner Post-RX-055 Fake-Money Paper Trader Handoff Direction Gate

## Objective

After RX-056 reviewer acceptance and finalization, record explicit Product Owner direction, supplied through Control Tower or source-of-truth docs, for exactly one next non-dangerous fake-money paper-trader handoff after the accepted RX-055 manual serial paper session runner.

If explicit Product Owner direction clearly identifies one concrete safe fake-money paper-trader task, prepare exactly that one later task in `NEXT_TASK.md`. If Product Owner direction is absent, ambiguous, unsafe, or reaches a hard-stop category, record that no clarified handoff is available and do not invent product/runtime scope.

The accepted RX-055 baseline includes a manual `paper-trade-session` command that consumes one explicit local JSON route-list file capped at 25 exact ENTRY routes, preserves Entry EV, paper expected funding, paper total fees, decision net profit, and paper net profit as count-only known/unknown fields, and does not aggregate paper PnL. A local paper session report/history artifact layer may be considered only if explicit Product Owner direction clearly grounds it as exactly one manual, explicit-local-path, deterministic, non-network, non-Telegram, non-live, non-order, non-private/account, no-migration, no-replay-change handoff.

RX-057 is governance/source-of-truth only. It must not implement product/runtime behavior, CLI output behavior, local report/history exports, Telegram transport, credentials, route discovery, polling, execution automation, live trading, orders, private/account endpoints, account-state behavior, ledger replay/reconciliation changes, storage migrations, or later roadmap stages.

## Starting baseline

Start from reviewer-accepted `main` after RX-056 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-057-product-owner-post-rx-055-fake-money-paper-trader-handoff-direction-gate`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-056 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

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

- Inspect the accepted RX-056 outcome, accepted RX-055 serial session baseline, current source-of-truth docs, and explicit Product Owner or Control Tower direction for exactly one next fake-money paper-trader handoff.
- Record whether exactly one concrete safe fake-money paper-trader handoff is clarified after RX-056.
- If one concrete safe handoff is clarified, prepare exactly that one later task in `NEXT_TASK.md`.
- If no concrete safe handoff is clarified, record the no-clarified-handoff conclusion and prepare one narrow follow-up clarification gate in `NEXT_TASK.md`.
- Update source-of-truth docs only as needed for this clarification: likely `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.

## Forbidden scope

- No product/runtime code changes.
- No CLI behavior changes.
- No local report/history artifact export implementation.
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
- No Telegram bot tokens.
- No Telegram transport, webhooks, external Telegram network calls, alerts, or messaging behavior.
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

- Treat RX-057 as the single next governance/source-of-truth task.
- Preserve reviewer-only acceptance: RX-056 branch work is not accepted until explicit reviewer acceptance and finalization on `main`.
- Preserve RX-056 as pending or accepted according to explicit reviewer evidence found in the repository/git state.
- Use the accepted RX-056 outcome, accepted RX-055 baseline, current source-of-truth docs, and explicit Product Owner direction rather than chat memory to decide whether one concrete next non-dangerous handoff is clarified.
- If a next handoff is prepared, keep `NEXT_TASK.md` to exactly one task and make the handoff fail closed around all hard-stop categories.
- A local paper session report/history artifact layer may be prepared as a later task only if explicit Product Owner direction clearly grounds that exact manual, explicit-local-path, deterministic, non-network, non-Telegram, non-live, non-order, non-private/account, no-migration, no-replay-change scope.
- Telegram remains later interface direction only unless an explicit future credentials/network gate authorizes transport and token handling. RX-057 must not add or prepare actual Telegram network, bot-token, webhook, alert, or messaging behavior.
- Control Tower autonomous selection is allowed only because this is non-dangerous governance/source-of-truth work grounded in repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker required.
- The worker is required for design support before implementation edits because this task touches repository governance, accepted baseline versus pending review state, and future handoff scope.
- At DESIGN CHECKPOINT, the worker must answer whether the RX-057 clarification direction is source-grounded, non-dangerous, one-task/one-branch compliant, preserves accepted baseline versus pending review state, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer-only acceptance, excludes all hard-stop categories including Telegram token/network credentials, avoids invented runtime scope, avoids discovery/ranking/watchlists/polling/background loops/scheduling/alerts, avoids new statuses/reasons and second owner paths, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Likely `README.md`
- Likely `ARCHITECTURE.md`
- Likely `PRODUCT_INVARIANTS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `STATUS.md`
- Likely `DECISIONS.md`
- `NEXT_TASK.md`
- Other docs/templates only if strictly necessary for the RX-057 clarification

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused doc/search checks proving no new runtime files were changed and no Telegram/live/order/private/account hard-stop scope was introduced.
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
