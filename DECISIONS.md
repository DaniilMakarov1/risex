# Decisions

## RX-000

- Adopted a modular-monolith structure with explicit single-owner modules for economics, risk, evaluation, execution, accounting, configuration, and venue normalization.
- Established capture-centric domain language: one `Capture` is one funding settlement opportunity.
- Established allowed route statuses: `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `LIVE_ELIGIBLE`, `REJECTED`.
- Explicitly excluded `CANARY_ELIGIBLE` and separate canary architecture.
- Set product constants: `MIN_LEG_NOTIONAL_USD = 500`, `MIN_NET_PROFIT_USD = 1`, live trading disabled by default, and points/airdrop/leaderboard/unreceived rebates set to zero in base PnL.
- Entry EV uses current executable VWAP and simulated immediate roundtrip cost. It does not use `expected_basis_change` as a future basis prediction.

## RX-001

- Added explicit `CaptureState` lifecycle states for one `Capture`, separate from `RouteStatus` eligibility decisions.
- Made `core/domain/state_machine.py` the single authoritative Capture lifecycle transition table and validator.
- Terminal Capture states are `REJECTED`, `CLOSED`, `FAILED`, and `EMERGENCY_FLATTENED`.
- Any non-terminal Capture may transition to `FAILED`; exposure states may transition to `EMERGENCY_FLATTENED`.
- State transitions are pure domain operations: they do not send orders, call execution modules, connect to venues, or write ledger events.

## RX-002

- Made `ProductRules` the authoritative product-level config contract for minimum notional, minimum net profit, live trading switch, points value, expected airdrop value, leaderboard rewards in base PnL, and unreceived rebates.
- Added `ValueSource` as the explicit source contract for future documented, observed, order-book-estimated, last-value-estimated, user-configured, and unknown values.
- Added `EstimatedValue` as a small source-aware value object. `UNKNOWN` values cannot carry or return a numeric zero fallback.
- Added centralized `RejectReason` values and moved current route/risk gate reasons away from ad hoc strings.
- Enforced the no-artificial-filters rule in code shape and invariant tests: no arbitrary max spread, max price impact, max levels consumed, hidden conservative buffers, or safety margins in `ProductRules`.
- Kept live trading offline: even when the live switch is manually enabled, RX-002 still returns paper eligibility because live gates are not implemented.

## RX-002A

- Added minimal GitHub CI for pushes and pull requests that installs dev dependencies, runs `python -m pytest`, and runs `python -m compileall apps core storage tests`.
- Kept CI infrastructure-only: no linting, formatting, type checking, coverage, secrets, deployment, Docker, exchange connectivity, or live trading.

## RX-003

- Introduced source-aware offline economics contracts for order books, executable VWAP quotes, fee components, fee models, and funding snapshots.
- Made VWAP-from-orderbook the required path for entry and immediate-unwind economics in fake data and `evaluate_route()`.
- Kept unknown values fail-closed: `ValueSource.UNKNOWN` cannot carry or return a numeric value, and fee/funding/EV calculations reject missing economics instead of using zero.
- Limited RX-003 fee sources to documented, observed, and user-configured values; user-configured defaults are valid only with `ValueSource.USER_CONFIGURED`.
- Limited RX-003 funding sources to documented, observed, and last-observed estimates; last-observed fallback is represented only by `ValueSource.ESTIMATED_FROM_LAST_VALUE`.
- Preserved the no-artificial-filters rule: insufficient order-book depth for the configured minimum notional is a technical rejection, while poor executable liquidity changes roundtrip cost and net PnL instead of becoming a standalone reject filter.
- Kept basis logic as current unwind PnL from executable quotes only; RX-003 does not forecast future basis or introduce `expected_basis_change`.
- Kept live trading blocked by `LIVE_TRADING_DISABLED` / `LIVE_GATES_NOT_IMPLEMENTED`; RX-003 does not create orders, real adapters, or live capture plans by default.

## RX-004

- Placed offline Broad Scan and Focused Refresh orchestration in `apps/research_runner/scanning.py`, keeping scanning at the research-app layer instead of adding a second core decision pipeline.
- Broad Scan and Focused Refresh both call the shared `evaluate_route(route, snapshot, mode)` path; the orchestration-level mode difference is `EvaluationMode.DISCOVERY` versus `EvaluationMode.ENTRY`.
- Kept scanner code out of economics, risk, venue-adapter, execution, order, dashboard, database, and persistence ownership.
- Added an in-memory watchlist that admits only non-rejected discovery decisions and rejects candidates with capture plans.
- Focused Refresh must obtain a fresh `VenueSnapshot` through an injected offline refresher before evaluating a watched route.
- RX-004 does not introduce real exchange connectivity, live order placement, real paper execution, secrets, migrations, or persistent ledger storage.
