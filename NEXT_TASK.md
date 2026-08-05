# RX-002 — Product Rules, Config Contracts, and No-Artificial-Filters Enforcement

## Goal

Define product rule/config contracts that make the no-artificial-filters invariant enforceable by tests.

## Scope

- Keep configured constants explicit: `MIN_LEG_NOTIONAL_USD = 500`, `MIN_NET_PROFIT_USD = 1`, points value `0`, expected airdrop value `0`, leaderboard rewards `0` in base PnL, and unreceived rebates `0`.
- Ensure unknown values cannot silently become zero in config-facing contracts.
- Add invariant tests that reject arbitrary spread, price impact, basis, slippage, or hidden buffer filters outside PnL calculations.
- Keep all work offline and non-trading.

## Non-goals

- Do not connect to RiseX or Hyperliquid.
- Do not place live orders.
- Do not add real API keys or production credentials.
- Do not add `CANARY_ELIGIBLE` or `canary_runner`.
- Do not add `HOLD`, `HOLDING_NEXT_CYCLE`, or multi-cycle capture states.
- Do not use `expected_basis_change` as a future basis prediction.
