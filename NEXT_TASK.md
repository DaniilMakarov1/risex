## Task ID

RX-012 — Offline Live Gate Evidence Bundle Design and Fake Replay Coverage

## Objective

Add a deterministic fake offline contract that bundles the already-implemented future live-gate inputs for one Capture route evaluation so callers cannot accidentally mix ledger reconciliation, CapturePlan freshness, and execution-capability evidence from different captures, routes, or funding settlement opportunities.

## Allowed scope

- Use fake deterministic inputs only.
- Keep the bundle downstream of route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, and execution-capability evidence.
- Reuse existing `RouteCandidate`, `VenueSnapshot`, `CapturePlanFreshnessEvidence`, `ExecutionCapabilityEvidence`, and `evaluate_route()` contracts.
- Prove cross-capture, cross-route, cross-settlement, missing-component, and stale-component bundles fail closed before any future live path can proceed.
- Keep live trading disabled.

## Forbidden scope

- Do not implement real RiseX, Hyperliquid, network calls, API clients, authentication, or production adapters.
- Do not place orders or enable live trading.
- Do not implement live runner behavior.
- Do not create executable live order plans.
- Do not add canary architecture, `CANARY_ELIGIBLE`, or `canary_runner`.
- Do not add hold-next-cycle logic.
- Do not add artificial filters or hidden buffers.
- Do not add a second route model, EV path, route decision function, snapshot assembly function, or VWAP/liquidity path.
