## Task ID

RX-011 — Offline Execution Capability Gate Design and Fake Replay Coverage

## Objective

Add deterministic fake execution-capability gate contracts that can later block any live Capture path unless the current route can still execute its full selected target notional on every required entry and unwind side.

## Allowed scope

- Use fake deterministic inputs only.
- Keep the gate downstream of route decisions, ledger reconciliation, funding settlement verification, and CapturePlan freshness evidence.
- Reuse the single `RouteCandidate`, `VenueSnapshot`, `assemble_route_snapshot()`, and `evaluate_route()` contracts.
- Prove missing, stale, cross-route, partial-fill, or contradictory execution-capability evidence fails closed.
- Keep live trading disabled.

## Forbidden scope

- Do not implement real RiseX, Hyperliquid, network calls, API clients, authentication, or production adapters.
- Do not place orders or enable live trading.
- Do not implement live runner behavior.
- Do not create executable live order plans.
- Do not add canary architecture, `CANARY_ELIGIBLE`, or `canary_runner`.
- Do not add hold-next-cycle logic.
- Do not add artificial filters or hidden buffers.
- Do not add a second route model, EV path, route decision function, or snapshot assembly function.
