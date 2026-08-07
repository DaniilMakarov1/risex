## Task ID

RX-007 — Paper Runner Lifecycle and Append-only Ledger Persistence

## Objective

Add a deterministic fake paper-runner lifecycle over existing route decisions and introduce append-only persistent ledger scaffolding without enabling live trading, real adapters, or order placement.

## Allowed scope

- Consume `DecisionResult` values produced by the existing `evaluate_route(route, snapshot, mode)` path.
- Model a fake paper lifecycle for one Capture per funding settlement opportunity.
- Persist append-only fake ledger records through the existing accounting boundary.
- Keep all behavior deterministic, offline, and non-trading.
- Add tests for lifecycle transitions, ledger append-only behavior, replayability, and live safety gates.

## Forbidden scope

- Do not implement real RiseX, Hyperliquid, network calls, API clients, authentication, or production adapters.
- Do not place live orders or enable live trading.
- Do not add canary architecture, `CANARY_ELIGIBLE`, or `canary_runner`.
- Do not add hold-next-cycle logic.
- Do not add artificial filters or hidden buffers.
- Do not create live `CapturePlan` objects until fresh plan checks, reconciled ledger state, live gates, funding settlement verification, and execution capability are implemented.
- Do not add a second route model, EV path, route decision function, or snapshot assembly function.

## Required report format

- Task ID
- Repository path
- Branch
- Starting HEAD
- Final HEAD
- Changed files
- What was implemented
- Tests run
- Exact test results
- Working-tree status
- Known limitations
- Risk impact
- Next suggested task
