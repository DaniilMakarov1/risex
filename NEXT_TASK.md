# Next Task

## Task ID

RX-060 - Local Paper Session Operator Package Builder

## Objective

After RX-059 reviewer acceptance and finalization, add one local-only, manually invoked operator-package/preview builder for serial fake-money paper sessions.

The builder must consume explicit local command payload fixtures through the accepted RX-058 parser and validation boundary, then produce deterministic local operator artifacts suitable for manual serial paper-trader testing and later Telegram display adaptation: a validated route-list JSON file plus a preview/manifest JSON describing route count, route ids, intended local input/report paths, and the exact manual `paper-trade-session --routes-json-path ... --session-report-json-path ...` command plan.

The builder must not execute the session, construct adapters, write ledger events, write session report/history results, send messages, call networks, add Telegram transport, or add live/order/private/account scope.

## Starting baseline

Start from reviewer-accepted `main` after RX-059 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-060-local-paper-session-operator-package-builder`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-059 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, product/runtime testing-support only, local/manual/fake-money only, and grounded in the accepted RX-055/RX-057/RX-058 trail plus explicit Product Owner direction. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Add one explicit local/manual operator-package builder entry point in the CLI app layer.
- Consume explicit local command payload fixture text from an operator-supplied local file path through the accepted RX-058 parser/validation boundary.
- Write a deterministic validated route-list JSON artifact suitable for `paper-trade-session --routes-json-path`.
- Write a deterministic preview/manifest JSON artifact describing route count, route ids, intended local route-list and session-report paths, and the exact manual `paper-trade-session --routes-json-path ... --session-report-json-path ...` command plan.
- Require explicit local output paths for every artifact the builder writes.
- Preserve RX-055 route-list validation semantics, including the 25-route explicit ENTRY cap, exact route fields, required RiseX/Hyperliquid venues, opposing sides, positive finite string notional, and timezone-aware `assembled_at`.
- Preserve RX-057 report/history semantics by planning an intended session report path only; do not write a session report/history result artifact.
- Add focused tests for accepted package generation, malformed payload rejection before any side-effectful runtime path, deterministic artifact content, explicit output paths, no session execution, no adapter construction, no ledger writes, no session report/history writes, no Telegram/network/credential/live/order/private/account behavior, no discovery/ranking/watchlist/polling/background loop/scheduling/alert behavior, no aggregate PnL, and no unknown-to-zero behavior.
- Update source-of-truth docs for the RX-060 outcome and next handoff.

## Forbidden scope

- No session execution.
- No adapter construction.
- No ledger event writes.
- No session report/history result writes.
- No product behavior outside the explicit local operator-package builder.
- No existing CLI output behavior changes except the new explicitly invoked builder command.
- No parser behavior weakening.
- No Telegram transport.
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
- No aggregate PnL invention.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second session runner, second decision path, second snapshot assembly path, second EV path, second VWAP path, second fee/funding path, second paper lifecycle path, second ledger-write path, second replay path, second reconciliation path, second execution-planning path, or second live execution path.

## Implementation requirements

- Keep the builder local-only, manually invoked, deterministic, and fake-money paper testing-support only.
- Keep ownership in the CLI app layer. Reuse `apps/cli/paper_session_payloads.py` for payload parsing and route-list validation instead of duplicating the boundary.
- The builder may add a new explicit CLI command or narrowly scoped CLI helper only for the operator package.
- The command must read the command payload fixture from an explicit local file path and validate the entire command payload before writing any artifact.
- The command must write no files unless explicit local output paths are supplied.
- The route-list artifact must contain only exact route-list dictionaries accepted by `paper-trade-session --routes-json-path`; it must not add economics, decision, paper, summary, report, ledger, aggregate PnL, transport, unknown placeholder, or unknown-to-zero fields.
- The preview/manifest artifact must be descriptive only. It may include route count, route ids, route-list artifact path, intended session report path, and a string/list representation of the exact manual `paper-trade-session` command plan.
- The preview/manifest artifact must not contain credentials, secrets, bot tokens, private/account data, sendable exchange requests, order payloads, live execution material, realized session results, ledger events, report/history results, aggregate PnL, or invented economics.
- The builder must not call `run_real_data_research_route()`, `run_real_data_research_route_with_snapshot()`, `run_paper_lifecycle()`, `InMemoryLedger`, `SQLiteLedger`, adapters, live runner modules, execution modules, replay, reconciliation, or network clients.
- Keep Telegram as later interface/display direction only. RX-060 may produce deterministic local artifacts suitable for later Telegram display adaptation, but it must not add real Telegram transport, bot tokens, credentials, webhooks, alerts, messaging behavior, or external network calls.
- Keep `NEXT_TASK.md` to exactly one task and require `python3 scripts/validate_next_task.py` to pass.
- Control Tower autonomous selection is allowed only because this is non-dangerous local/manual/fake-money testing-support work grounded in repository docs plus explicit Product Owner direction.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker required.
- The worker is required for design support before implementation edits because this task adds a new local artifact-writing boundary adjacent to paper-session command preparation.
- At DESIGN CHECKPOINT, the worker must answer whether the proposed builder is source-grounded, non-dangerous, one-task/one-branch compliant, preserves accepted baseline versus pending review state, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer-only acceptance, consumes the RX-058 parser/validation boundary, avoids session execution, avoids adapter construction, avoids ledger writes, avoids session report/history result writes, requires explicit local output paths, excludes Telegram token/network credentials and all hard-stop categories, avoids discovery/ranking/watchlists/polling/background loops/scheduling/alerts, avoids execution automation/planning, avoids live/order/private/account scope, avoids ledger replay/reconciliation/storage migration, avoids new statuses/reasons and second owner paths, preserves unknown-as-missing/no-aggregate-PnL behavior, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Likely `apps/cli/main.py`
- Likely `apps/cli/paper_session_payloads.py`
- Likely `tests/unit/test_cli_main.py`
- Likely `tests/unit/test_paper_session_payloads.py`
- Likely `README.md`
- Likely `ARCHITECTURE.md`
- Likely `PRODUCT_INVARIANTS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `STATUS.md`
- Likely `DECISIONS.md`
- `NEXT_TASK.md`
- Other source-of-truth docs only if strictly necessary

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused unit tests for the local operator-package builder.
- Focused docs/search checks proving RX-060 Local Paper Session Operator Package Builder is the current next task and not a clarification-gate handoff.
- Focused docs/search checks proving no Telegram/live/order/private/account hard-stop scope was introduced.
- Focused search checks proving no route discovery, ranking, watchlists, polling, background loops, scheduling, alerts, storage migration, replay, reconciliation, or second owner path was introduced.
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
