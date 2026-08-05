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
