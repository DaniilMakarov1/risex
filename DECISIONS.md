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

## 2026-08-06 — RX-003 FIX

- Date: 2026-08-06
- Decision: `RouteCandidate` is the authoritative route contract for RiseX venue/symbol, hedge venue/symbol, target notional, and intended opposing entry sides; `core/risk/gates.py` owns centralized route/snapshot alignment before Entry EV.
- Reason: RX-003 review found that executable quotes could be mismatched by venue, symbol, side, source, or notional and still enter EV/roundtrip math. Alignment must fail closed before economics calculations.
- Affected files/modules: `core/domain/contracts.py`, `core/risk/gates.py`, `core/pipeline/evaluate.py`, `core/economics/liquidity.py`, `core/economics/fees.py`, `core/economics/funding.py`, `core/economics/errors.py`, `core/venues/base.py`, `apps/research_runner/fake_data.py`, tests, and governance docs.
- Superseded decision: the previous `VenueAdapter.fetch_snapshot() -> VenueSnapshot` boundary is superseded. Adapters are now per-venue and expose only `fetch_order_book(symbol: str) -> OrderBook`; cross-venue route snapshot assembly is reserved for future observation/orchestration contracts.
- Decision: RX-003 `evaluate_route()` does not construct `CapturePlan`, does not invent settlement timestamps, and does not bypass the Capture state machine. Even with `ProductRules(live_trading_enabled=True)`, profitable ENTRY evaluations remain `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED`.
- Reason: RX-003 has no implemented live gates, funding settlement timestamp contract, fresh CapturePlan contract, or live execution boundary.
