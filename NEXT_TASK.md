# Next Task

## Task ID

RX-055 - Manual Serial Paper Session Runner

## Objective

After RX-054 reviewer acceptance and finalization, create one manual, explicitly invoked serial fake-money paper testing runner or command for a finite operator-supplied list of explicit RiseX plus Hyperliquid routes. The runner must reuse the existing public one-route decision path and existing fake paper lifecycle plus ledger ownership, produce deterministic session summary stdout for strategy testing, and optionally persist fake paper ledger events only through an explicit local SQLite ledger path.

Product Owner plans to test later through a Telegram bot, but Telegram is product direction only for now. RX-055 must not implement Telegram transport, bot tokens, credentials, external Telegram network calls, webhooks, alerts, or messaging behavior. Bot-ready command parsing may be a later non-network task; actual Telegram transport and token handling require an explicit future credentials/network gate.

## Starting baseline

Start from reviewer-accepted `main` after RX-054 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-055-manual-serial-paper-session-runner`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-054 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous fake-money paper-trader work only. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Add one manual, explicitly invoked serial fake-money paper session runner or CLI command for a finite operator-supplied list of explicit routes.
- Reuse the existing public read-only RiseX and Hyperliquid adapter construction boundaries after validation.
- Reuse the existing one-route public real-data decision path, including `run_real_data_research_route_with_snapshot()` and the shared `evaluate_route(route, snapshot, mode)` path in `EvaluationMode.ENTRY`.
- Reuse the existing fake paper lifecycle in `apps/paper_runner/lifecycle.py`.
- Keep fake paper ledger writes behind `core/accounting/ledger.py`.
- If local persistence is implemented, use only the existing `storage/sqlite/ledger.py` contract and an explicit operator-supplied local SQLite path.
- Produce deterministic stdout for per-route outcomes and session-level summary counts suitable for manual strategy testing.
- Update focused tests and source-of-truth docs for exactly this manual serial fake-money paper session scope.

## Forbidden scope

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

- Treat RX-055 as the single next product/runtime task and keep it limited to manual fake-money serial paper testing.
- The operator must supply a finite explicit route list. Missing, empty, malformed, unbounded, discovery-style, ranking-style, watchlist-style, or polling-style inputs must fail closed before adapter construction for the affected run.
- Each route in the session must use the existing public one-route input requirements: route id, capture id, exact RiseX and Hyperliquid venues, symbols, opposing entry sides, positive finite target notional, `ENTRY` mode, and timezone-aware assembly timestamp.
- Each serial route decision must flow through the existing one-route public decision helper and shared `evaluate_route(route, snapshot, mode)` path. RX-055 must not add a second decision, snapshot, EV, VWAP, fee, funding, or route model path.
- Fake paper handling must delegate to the existing `run_paper_lifecycle()` behavior when a public snapshot is available.
- Missing public snapshot, Entry EV, funding, fee, decision net profit, or paper PnL values must remain `None`/unknown in route output and session summaries. Aggregates must not turn unknown values into zero, success, or profitability.
- Non-started decisions must remain explicit fake paper rejections through existing ledger behavior when a snapshot is available.
- Session output must be deterministic and must not mutate route statuses, reject reasons, route eligibility, Capture transitions, economics, replay, ledger reconciliation, execution planning, or live gates.
- Optional local persistence must reuse the existing SQLite ledger contract through an explicit local path only; do not add storage migrations or a second storage layer.
- Telegram must be recorded as later interface direction only. Bot-ready command parsing may be a future non-network task; actual Telegram transport, bot tokens, credentials, webhooks, and external network behavior require an explicit future credentials/network gate and are forbidden in RX-055.
- Preserve reviewer-only acceptance; implementation-complete branch work is not accepted until an explicit reviewer accepts it.
- Preserve RX-054 as pending or accepted according to explicit reviewer evidence.
- Control Tower autonomous selection is allowed only because this is non-dangerous fake-money paper-trader work grounded in source-of-truth repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker required.
- The worker is required for design support before implementation edits because this task touches manual runtime, app/CLI ownership, fake paper lifecycle integration, and ledger ownership boundaries.
- At DESIGN CHECKPOINT, the worker must answer whether the manual serial runner design is source-grounded, non-dangerous, one-task/one-branch compliant, preserves accepted baseline versus pending review state, reuses the existing one-route public decision path, reuses the existing fake paper lifecycle, keeps ledger writes inside accounting ownership, keeps optional persistence inside the existing SQLite ledger contract, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer-only acceptance, excludes hard-stop categories including Telegram token/network credentials, avoids discovery/ranking/watchlists/polling/background loops/scheduling/alerts, preserves unknown-as-missing behavior, avoids new statuses/reasons and second owner paths, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Likely `apps/cli/main.py`
- Likely `tests/unit/test_cli_main.py`
- Likely `README.md`
- Likely `ARCHITECTURE.md`
- Likely `PRODUCT_INVARIANTS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `STATUS.md`
- Likely `DECISIONS.md`
- `NEXT_TASK.md`
- Other files only if strictly necessary for the manual serial runner and its focused tests

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused tests for the serial paper session runner covering at least: a started route, a non-started route, deterministic session summary output, finite explicit route list handling, optional explicit SQLite ledger path behavior if implemented, malformed route/operator input fail-closed before adapter construction, preservation of unknown economics as missing rather than zero, and absence of live/order/private/account/Telegram behavior.
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
