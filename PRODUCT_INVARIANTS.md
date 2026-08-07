# Product Invariants

## Strategy

- Main strategy: hedged funding capture on RiseX with hedge venue support, initially Hyperliquid.
- One `Capture` equals one funding settlement opportunity.
- One shared decision pipeline evaluates routes.
- One append-only ledger records decisions and future execution/accounting events.

## PnL constants

The single authoritative code contract for these constants is `ProductRules`.

- Points value is `0`.
- Expected airdrop value is `0`.
- Leaderboard rewards are `0` in base PnL.
- Unreceived rebates are `0`.
- `MIN_LEG_NOTIONAL_USD = 500`.
- `MIN_NET_PROFIT_USD = 1`.

## Live trading

- Live trading is disabled by default.
- RX-000 must not connect to exchanges.
- RX-000 must not place live orders.
- Future live eligibility requires explicit live gates, fresh executable data, reconciled ledger state, and funding settlement verification.
- Offline funding settlement verification evidence is not permission to trade live by itself.
- Offline ledger reconciliation evidence is not permission to trade live by itself.
- A future live path must fail closed with `LEDGER_NOT_RECONCILED` unless ledger reconciliation is explicitly true.

## Route statuses

Allowed statuses:

- `RESEARCH_ONLY`
- `PAPER_ELIGIBLE`
- `LIVE_ELIGIBLE`
- `REJECTED`

Forbidden status:

- `CANARY_ELIGIBLE`

## Rejection rules

A route may be rejected only when:

1. The route is technically impossible to execute.
2. Required data for live calculation is missing.
3. `net_profit_usd < MIN_NET_PROFIT_USD`.
4. An explicit user rule is violated.
5. An exchange, market, or mode is disabled.
6. The ledger is not reconciled.
7. There is no fresh `CapturePlan`.
8. The route does not meet `MIN_LEG_NOTIONAL_USD`.
9. The order book cannot execute the configured minimum notional on a required leg.

Code represents these with the centralized `RejectReason` enum.

## No artificial filters

Do not add arbitrary max spread, arbitrary max price impact, arbitrary max levels consumed, hidden conservative buffers, or hidden safety margins. Spread, price impact, basis, slippage, and fees enter PnL calculations instead of acting as independent arbitrary reject filters.

## Unknown values

Unknown values must not silently become zero. If a fee is unknown, use only a user-configured default fee with source `USER_CONFIGURED`. If exact funding is unknown, a future task may use last observed funding before settlement with source `ESTIMATED_FROM_LAST_VALUE`. If there is no funding estimate, the route cannot be `LIVE_ELIGIBLE`.

Actual settlement funding and actual settlement notional evidence are proof inputs for funding settlement verification. They must be `OBSERVED`; documented, estimated, user-configured, unknown, missing, malformed, or non-positive notional actuals are not proof.

Ledger reconciliation is a replay contract for append-only history consistency. It must not calculate profitability, mutate route decisions, create live plans, place orders, or silently treat missing, duplicated, out-of-order, or contradictory evidence as reconciled.

Allowed value sources are exactly:

- `DOCUMENTED`
- `OBSERVED`
- `ESTIMATED_FROM_ORDERBOOK`
- `ESTIMATED_FROM_LAST_VALUE`
- `USER_CONFIGURED`
- `UNKNOWN`
