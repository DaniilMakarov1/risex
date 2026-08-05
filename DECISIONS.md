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
