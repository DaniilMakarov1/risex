# RX-001 — Domain Contracts and State Machine

## Goal

Formalize the domain contracts and state machine for the capture-centric lifecycle.

## Scope

- Refine `Capture`, `RouteCandidate`, `VenueSnapshot`, `ExecutableQuote`, `DecisionResult`, and related value objects.
- Add explicit capture lifecycle states without introducing hold or canary architecture.
- Define how decision history connects to append-only ledger events.
- Define future `CapturePlan` freshness rules without enabling live trading.
- Add invariant tests for the state machine and forbidden transitions.

## Non-goals

- Do not connect to RiseX or Hyperliquid.
- Do not place live orders.
- Do not add real API keys or production credentials.
- Do not add `CANARY_ELIGIBLE` or `canary_runner`.
- Do not use `expected_basis_change` as a future basis prediction.
