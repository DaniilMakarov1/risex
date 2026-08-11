# Implementation Plan

## RX-000 — Project Constitution and Walking Skeleton Foundation

Create repository docs, structure, Python test setup, minimal domain contracts, fake route evaluation, and append-only ledger tests. No real adapters, no live orders, and no external exchange connectivity.

## RX-001 — Domain Contracts and State Machine

Strengthen domain contracts and introduce the formal state machine for `Capture`, route lifecycle, decision history, and future `CapturePlan` freshness rules.

## RX-002 — Product Rules, Value Sources, and Central Reject Reasons

Make `ProductRules`, `ValueSource`, `EstimatedValue`, and `RejectReason` authoritative. Keep live trading disabled by default and enforce no-artificial-filter invariants.

## RX-002A — GitHub CI Workflow

Add minimal CI for pytest and compileall without secrets, deployment, linting, coverage, exchange connectivity, or live trading.

## RX-003 — Economics Engine Candidate

Add source-aware offline economics for fees, funding, order-book VWAP liquidity, immediate roundtrip cost, basis/unwind PnL, and Entry EV through the single `evaluate_route()` pipeline.

RX-003 FIX repairs the candidate contract before review acceptance:

- Route/snapshot alignment is centralized in `core/risk/gates.py`.
- `RouteCandidate` explicitly owns route venues, symbols, target notional, and intended opposing entry sides.
- Roundtrip quote pairing rejects venue, symbol, side, target-notional, executability, and VWAP mismatches.
- Expected missing economics input failures use a scoped exception contract.
- RX-003 never constructs `CapturePlan` or `LIVE_ELIGIBLE` decisions.
- `VenueAdapter` is read-only and per-venue; RX-004 supersedes the order-book primitive with `fetch_observation()`.

## RX-004 — Per-Venue Observation and Route Snapshot Contracts

Add normalized per-venue `VenueObservation` inputs and the single `assemble_route_snapshot()` path that converts route-aligned observations into `VenueSnapshot` values for `evaluate_route()`.

## RX-005 — Offline Scan Orchestration over Per-Venue Observations

Add deterministic fake offline orchestration over multiple `RouteCandidate` values and normalized observation mappings. Every successful candidate uses `assemble_route_snapshot()` and then `evaluate_route()`. Missing or contradictory observations fail closed before evaluation without trades, orders, ledger writes, paper lifecycle, live trading, or `CapturePlan` creation.

## RX-006 — Broad Scan and Focused Refresh orchestration

Add deterministic fake Broad Scan and Focused Refresh over the same offline observation, snapshot assembly, and `evaluate_route()` path. Keep the scan/refresh layer fake-data-only, read-only, non-trading, and free of paper execution, ledger writes, real adapters, live trading, or `CapturePlan` creation.

## RX-007 — Paper Runner Lifecycle and Append-only Ledger Persistence

Add deterministic fake paper lifecycle downstream of existing `DecisionResult` values and append-only ledger persistence scaffolding. Start paper capture execution only for `PAPER_ELIGIBLE` decisions, use the single Capture state machine, write all fake paper history through `core/accounting/ledger.py`, and keep real adapters, orders, live trading, live runner behavior, `CapturePlan` creation, second decision paths, second EV paths, and second snapshot assembly paths out of scope.

## RX-008 — Funding Settlement Verifier Design and Fake Replay Coverage

Add deterministic offline funding settlement verifier contracts and fake replay coverage. Model required pre-settlement checkpoints at T-20 minutes, T-60 seconds, T-10 seconds, and T-5 seconds. Write checkpoint evidence, observed settlement evidence, and verification results through append-only ledger helpers. Replay ledger events to compare fake expected funding/notional inputs against fake observed settlement records, failing closed on missing, unknown, or inconsistent evidence. Keep the verifier downstream of existing route decisions, snapshots, Capture lifecycle, and ledger boundaries without real adapters, order placement, live `CapturePlan` creation, route eligibility mutation, or live trading.

## RX-009 — Ledger Reconciliation Gate Design and Fake Replay Coverage

Add deterministic offline ledger reconciliation contracts and fake replay coverage. Reconcile one Capture ledger history from append-only route decision, fake paper lifecycle, funding evidence, and funding settlement verification events. Record reconciliation results through ledger helpers, fail closed on missing, duplicated, out-of-order, or contradictory evidence, and require explicit reconciliation before any future live path can pass the ledger reconciliation gate. Keep live trading disabled and do not create live `CapturePlan` objects.

## RX-010 — Fresh CapturePlan Gate Design and Fake Replay Coverage

Add deterministic offline CapturePlan freshness gate contracts and fake replay coverage. Require exactly one fake non-executable freshness evidence record for the current Capture, route, and funding settlement opportunity before any future live path can pass the plan freshness gate. Keep the gate downstream of route decisions, ledger reconciliation, funding settlement verification, and append-only ledger boundaries without creating live `CapturePlan` objects, executable order plans, adapters, orders, or live trading.

## RX-011 — Offline Execution Capability Gate Design and Fake Replay Coverage

Add deterministic offline execution-capability gate contracts and fake replay coverage. Require exactly one fake non-executable evidence record with current order-book `ExecutableQuote` values proving that the current route can still execute its full selected target notional on RiseX entry, hedge entry, RiseX unwind, and hedge unwind sides before any future live path can pass the execution-capability gate. Keep the gate downstream of route decisions, ledger reconciliation, funding settlement verification, and CapturePlan freshness without recalculating VWAP/EV, creating order plans, adapters, orders, or live trading.

## RX-012 — Offline Live Gate Evidence Bundle Design and Fake Replay Coverage

Add deterministic offline live-gate evidence bundle contracts and fake replay coverage. Require one fake non-executable aggregate bundle for the current Capture, route, and funding settlement opportunity before any future live path can consider the full live gate sequence. Keep the bundle downstream of route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, and execution capability without replaying ledger/funding evidence, recalculating VWAP/EV, creating order plans, adapters, orders, or live trading.

## RX-013 — Offline Live Gate Evidence Bundle Ledger Recording and Replay Coverage

Add deterministic append-only ledger recording and replay coverage for fake live gate evidence bundle check results. Keep recording in `core/accounting/ledger.py`, replay validation in `core/accounting/reconciliation.py`, bundle checking in `core/risk/gates.py`, and live eligibility still blocked by `LIVE_GATES_NOT_IMPLEMENTED`.

## RX-014 — Offline Live Gate Evidence Bundle SQLite Persistence Replay Coverage

Add deterministic SQLite persistence replay coverage for fake live gate evidence bundle ledger records. Prove that valid, malformed, and contradictory `live_gate_evidence_bundle_recorded` payloads round-trip through `storage/sqlite/ledger.py` and replay with the same outcomes as in-memory ledger records, without changing storage architecture, route decisions, economics, risk gates, adapters, orders, or live trading.

## RX-015 — Offline SQLite Ledger Reopen Append Continuity Replay Coverage

Add deterministic SQLite reopen coverage for append-only sequence continuity and reconciliation freshness. Prove that appending after reopening an existing `SQLiteLedger` continues from the last persisted sequence, that a later persisted append makes prior reconciliation stale, and that a later reconciliation over reopened records replays deterministically without changing storage architecture, route decisions, economics, risk gates, adapters, orders, or live trading.

## RX-016 — Offline SQLite Ledger Reopen Fail-Closed Replay Coverage

Add deterministic SQLite reopen coverage proving that malformed, stale, or contradictory append-only evidence persisted after reopening an existing `SQLiteLedger` remains unreconciled after SQLite round-trip. Prove deterministic reconciliation replay from reopened SQLite records and the helper-derived explicit reconciliation gate remains false without changing storage architecture, route decisions, economics, risk gates, adapters, orders, or live trading.

## Next Sequence

1. RX-017 — Reviewer-Directed Follow-up After RX-016.
