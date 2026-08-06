# RX-004 — Broad Scan and Focused Refresh Over Shared `evaluate_route()`

## Task ID

RX-004 — Broad Scan and Focused Refresh Over Shared `evaluate_route()`

## Objective

Implement the first offline scanning orchestration that feeds candidate routes into the single shared `evaluate_route(route, snapshot, mode)` pipeline without adding a second decision path or real exchange connectivity.

## Scope

- Add fake-data-compatible Broad Scan code that identifies potential routes and records watchlist candidates only.
- Add fake-data-compatible Focused Refresh code that refreshes a watched route snapshot and calls the same `evaluate_route()` function.
- Keep Broad Scan and Focused Refresh rule-equivalent; the only intended difference is `EvaluationMode.DISCOVERY` versus `EvaluationMode.ENTRY`.
- Keep all behavior deterministic, offline, non-trading, and tested.
- Keep live trading disabled by default and do not place orders.

## Out of scope

- Real RiseX, Hyperliquid, or other venue adapters.
- API keys, secrets, credentials, production configuration, or network exchange calls.
- Live order placement or real paper execution.
- Dashboard work, database migrations, or persistent ledger storage.
- A second EV path, second route decision pipeline, canary architecture, or hold-to-next-cycle logic.
