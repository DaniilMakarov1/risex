# Status

- Last accepted task: RX-003 — Economics Engine: Fees, Funding, VWAP Liquidity, Basis, and Entry EV
- Accepted baseline RX-003 HEAD: `a53100fc4f45540ccd31769bc867e81d3cc5aa94`
- Current completed candidate task: RX-004 — Broad Scan and Focused Refresh Over Shared `evaluate_route()`
- Current branch: task/rx-004-scan-refresh
- Starting HEAD for RX-004: `a53100fc4f45540ccd31769bc867e81d3cc5aa94`
- Repository state at task start: clean checkout at accepted baseline RX-003 HEAD

## Completed work summary

- Added deterministic offline Broad Scan orchestration for fake `RouteCandidate` + `VenueSnapshot` inputs.
- Added an in-memory watchlist that admits only non-rejected `EvaluationMode.DISCOVERY` decisions and rejects capture-plan-bearing candidates.
- Added deterministic Focused Refresh orchestration that refreshes a watched route snapshot and calls the same shared `evaluate_route()` path with `EvaluationMode.ENTRY`.
- Kept scanning modules orchestration-only: no direct economics, risk, execution, adapter, order, dashboard, database, persistence, or network exchange code was introduced.
- Added unit and invariant coverage for scanner mode wiring, watchlist admission, Focused Refresh evaluator usage, rejected-route exclusion, shared economics behavior, and no execution-module imports.

## Tests run

- `python -m pytest` attempted, but the local shell has no `python` command.
- `python -m compileall apps core storage tests` attempted, but the local shell has no `python` command.
- `python3 -m pytest`
- `python3 -m compileall apps core storage tests`
- `git diff --check`
- `python3 -m apps.cli.main`

## Known limitations

- Only fake offline data is available.
- No real RiseX or Hyperliquid adapters exist.
- No live order placement exists.
- No persistent SQLite ledger exists yet.
- Funding settlement verification is not implemented.
- Broad Scan and Focused Refresh remain fake-data-compatible and in-memory only.
- Broad Scan does not rank, persist, or schedule routes beyond in-memory watchlist admission.
- Focused Refresh supports one watched route at a time and depends on an injected offline snapshot refresher.
- Live eligibility remains blocked by intentionally unimplemented live gates, even if the live trading switch is manually enabled.
- Fee rebates and negative fee modeling are not implemented yet.
- Current unwind PnL is quote-based and deterministic; it does not persist capture lifecycle or accounting events.

## Next recommended task

RX-005 — Paper Runner Lifecycle Over In-Memory Decisions
