# Product Invariants

## Strategy

- Main strategy: hedged funding capture on RiseX with hedge venue support, initially Hyperliquid.
- One `Capture` equals one funding settlement opportunity.
- One shared decision pipeline evaluates routes.
- One append-only ledger records decisions and future execution/accounting events.

## Roadmap gates

- RX-008 through RX-016 are accepted fail-closed offline safety hardening, not a product strategy change.
- Offline safety scaffolding must not become an open-ended detour. Future work must return to the intended product path one `NEXT_TASK.md` handoff at a time.
- Future roadmap stages are gated and scoped. A roadmap mention is not permission to implement real adapters, network calls, execution planning, live runner behavior, monitoring/dashboard behavior, or order placement before an explicit task authorizes that exact stage.
- Do not add speculative helpers, wrappers, future hooks, duplicate owner modules, second decision paths, second snapshot paths, second VWAP paths, second ledger-write paths, or second live execution paths.

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
- A future live path must fail closed with `LEDGER_NOT_RECONCILED` unless ledger reconciliation is explicitly true for the current append-only ledger history.
- Offline CapturePlan freshness evidence is not permission to trade live by itself.
- A future live path must fail closed with `CAPTURE_PLAN_NOT_FRESH` unless exactly one fake freshness evidence record matches the current `capture_id`, `route_id`, and funding settlement timestamp and is still inside its explicit validity window.
- Offline execution-capability evidence is not permission to trade live by itself.
- A future live path must fail closed unless exactly one fake execution-capability evidence record matches the current `capture_id`, `route_id`, funding settlement timestamp, and validity window, and proves all four current entry/unwind `ExecutableQuote` values fully fill `RouteCandidate.target_notional_usd` from order-book source.
- Offline live gate evidence bundles are not permission to trade live by themselves.
- A future live path that uses a fake evidence bundle must fail closed unless the bundle matches the current `capture_id`, `route_id`, and funding settlement timestamp, carries verified funding-settlement and helper-derived ledger reconciliation outputs, and reuses fresh CapturePlan and execution-capability evidence.
- Recorded fake live gate evidence bundle checks are not permission to trade live by themselves.
- A future live path that uses recorded fake bundle-check evidence must fail closed unless one current append-only ledger event replays against the current Capture, route, funding settlement timestamp, referenced route-decision, funding-verification, and ledger-reconciliation history, and its recorded bundle gate result matches `core/risk/gates.py`.
- Read-only venue adapters, real market-data snapshot assembly, and real-data research runners are data-ingestion and research stages only. They are not permission to place orders, enable live trading, or create executable order plans.
- The real market-data snapshot handoff may fetch one RiseX observation and one Hyperliquid observation for one existing route, then must delegate to `assemble_route_snapshot()` without route decisions, profitability calculations, ledger writes, paper lifecycle, execution planning, or live runner behavior.
- The real-data research runner may evaluate one explicit existing route only by calling the existing adapter handoff and then `evaluate_route(route, snapshot, mode)`. It must fail closed before evaluation on adapter or snapshot handoff failures and must not write ledger events, start paper lifecycle, verify funding settlement, plan execution, place orders, or add live runner behavior.
- Approval-gated funding settlement verification may record only explicit caller-supplied observed settlement evidence for one existing `Capture`, one existing `RouteCandidate`, and one explicit settlement timestamp. It is not permission to trade live by itself.
- Approval-gated settlement evidence must carry `approval_granted=True`, an observation timestamp equal to the explicit settlement timestamp, and actual funding/notional values with `ValueSource.OBSERVED`; missing approval, false approval, stale observations, unknown values, unobserved sources, malformed payloads, cross-capture, cross-route, cross-settlement, or contradictory evidence fails closed.
- Non-sending execution plans are evidence only. They may describe intended venues, symbols, entry/unwind sides, target notional, settlement timestamp, validity, and prerequisite evidence references, but they must not contain credentials, account state, private endpoint payloads, sendable API requests, or order placement permission.
- A guarded live runner may consume one existing non-sending execution plan only after exact prerequisite evidence is supplied. Missing, stale, malformed, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale plan prerequisites, non-executable execution evidence, disabled live switch, missing non-sending plan, stale non-sending plan, or sendable order material must fail closed.
- A successful guarded live runner result is no-order readiness only. It is not `LIVE_ELIGIBLE`, not ledger evidence, not order placement permission, and not permission to construct sendable exchange requests.
- An explicit approval-gated order placement boundary may consume a successful guarded live runner result only with the exact current `Capture`, `RouteCandidate`, funding settlement timestamp, existing non-sending plan, explicit request timestamp, and caller-supplied approval evidence. Missing, false, stale, malformed, cross-capture, cross-route, cross-settlement, disabled live switch, non-ready guarded result, missing approval, false approval, stale approval, cross-identity approval, missing non-sending plan, stale non-sending plan, stale plan prerequisites, or failed prerequisite evidence must fail closed before any injected deterministic order boundary is invoked.
- Execution planning without orders, a guarded live runner, and order placement must remain separate tasks with explicit acceptance gates.

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

`RouteCandidate.target_notional_usd` must be an explicit positive finite `Decimal`. Unknown, missing, non-numeric, non-finite, zero, or negative target notionals must fail at construction instead of becoming zero or a default notional. Positive target notionals below `MIN_LEG_NOTIONAL_USD` fail through the centralized minimum-notional route evaluation gate.

Actual settlement funding and actual settlement notional evidence are proof inputs for funding settlement verification. They must be explicitly approved, observed at the settlement timestamp, and `OBSERVED`; documented, estimated, user-configured, unknown, missing, malformed, stale, or non-positive notional actuals are not proof. Ledger reconciliation must verify any recorded funding settlement result against the canonical funding verifier replay from raw checkpoint and settlement evidence.

Ledger reconciliation is a replay contract for append-only history consistency. It must not calculate profitability, mutate route decisions, create live plans, place orders, or silently treat missing, duplicated, non-contiguous, out-of-order, unknown, malformed, stale, or contradictory evidence as reconciled.

Paper result attribution must remain downstream of `DecisionResult` and the fake paper lifecycle. It may explain why paper started or did not start, and may copy existing `DecisionResult` PnL components for inspection, but it must not recalculate route profitability, mutate eligibility, or turn missing economics into zero.

SQLite ledger persistence must preserve append-only sequence continuity across close/reopen boundaries. A persisted append after successful reconciliation must make the prior reconciliation stale until a later reconciliation result covers the current persisted history.

Malformed, stale, or contradictory evidence persisted after reopening a SQLite ledger must remain unreconciled after SQLite round-trip. The helper-derived explicit reconciliation flag must remain false for those histories, and the explicit reconciliation gate must fail closed.

Execution capability is a fake live-gate evidence contract over existing order-book quotes. It must not recalculate VWAP, decide profitability, replace ledger reconciliation, replace funding settlement verification, replace CapturePlan freshness, create live plans, or place orders.

Live gate evidence bundles are fake aggregate evidence only. They must not replay ledger history, replay funding settlement verification, recalculate VWAP/EV/profitability, replace the existing plan freshness or execution-capability gates, create live plans, or place orders.

Live gate evidence bundle ledger records are fake accounting evidence only. They must not recalculate VWAP/EV/profitability, replace ledger reconciliation, replace funding settlement verification, create live plans, place orders, or turn a recorded successful fake bundle check into live eligibility. Ledger reconciliation must fail closed over any malformed, stale, duplicated, missing-reference, or contradictory live gate bundle record. SQLite-persisted live gate bundle records must replay with the same deterministic outcomes as in-memory ledger records.

Execution planning without orders must remain downstream of existing route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, and execution capability evidence. It must not call route evaluation, assemble snapshots, calculate profitability, write ledger events, call adapters, import live runner behavior, create executable `CapturePlan` objects, place orders, or enable live trading.

Guarded live runner readiness without orders must remain downstream of existing route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, execution capability evidence, live-gate bundle checks, and non-sending execution planning. It must not call route evaluation, assemble snapshots, calculate profitability, replay funding or ledger history, write ledger events, call adapters, import order placement behavior, construct sendable exchange requests, place orders, mutate route eligibility, or enable live trading by default.

Explicit approval-gated order placement boundaries must remain downstream of guarded no-order readiness and non-sending execution planning. They must not call route evaluation, assemble snapshots, calculate profitability, replay funding or ledger history, write ledger events, call adapters, use credentials, create exchange request payloads before exact approval, place real orders by default, mutate route eligibility, add route statuses or reject reasons, or enable live trading by default. The default product rules must still fail closed.

Allowed value sources are exactly:

- `DOCUMENTED`
- `OBSERVED`
- `ESTIMATED_FROM_ORDERBOOK`
- `ESTIMATED_FROM_LAST_VALUE`
- `USER_CONFIGURED`
- `UNKNOWN`
