# RX-005 — Paper Runner Lifecycle Over In-Memory Decisions

## Task ID

RX-005 — Paper Runner Lifecycle Over In-Memory Decisions

## Objective

Implement the first deterministic offline paper-runner lifecycle that consumes `EvaluationMode.ENTRY` decisions from the shared `evaluate_route()` path and records in-memory lifecycle events without real execution, adapters, orders, database persistence, or live trading.

## Scope

- Add fake-data-compatible paper-runner orchestration under `apps/paper_runner/`.
- Consume `DecisionResult` objects produced by Focused Refresh / `evaluate_route()` instead of recalculating EV or route eligibility.
- Use the existing `Capture` state machine for paper lifecycle transitions.
- Record only in-memory ledger events through `core/accounting/ledger.py`.
- Keep behavior deterministic, offline, non-trading, and tested.
- Keep live trading disabled by default and do not place orders.

## Out of scope

- Real RiseX, Hyperliquid, or other venue adapters.
- API keys, secrets, credentials, production configuration, or network exchange calls.
- Live order placement, real paper exchange execution, or real fills.
- Dashboard work, database migrations, or persistent ledger storage.
- A second EV path, second route decision pipeline, canary architecture, or hold-to-next-cycle logic.
