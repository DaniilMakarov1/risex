# RX-003 — Economics Engine: Fees, Funding, VWAP Liquidity, Basis, and Entry EV

## Goal

Implement the first real pure economics contracts for fees, funding estimates, VWAP liquidity, basis/unwind tracking, and entry EV while keeping the system offline and non-trading.

## Scope

- Keep all economics logic inside the established single-owner modules.
- Use `ValueSource` and `EstimatedValue` for fee, funding, and liquidity inputs where appropriate.
- Require user-configured default fees to use `USER_CONFIGURED`.
- Require last-observed funding fallbacks to use `ESTIMATED_FROM_LAST_VALUE`.
- Calculate VWAP executability for the configured `MIN_LEG_NOTIONAL_USD = 500` without arbitrary spread, price impact, levels-consumed, buffer, or safety-margin filters.
- Keep `evaluate_route()` as the only decision pipeline.
- Keep live trading disabled and do not place orders.
