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

## Next Sequence

1. RX-006 — Broad Scan and Focused Refresh orchestration over the same offline observation, snapshot assembly, and `evaluate_route()` path.
2. Paper runner lifecycle and append-only ledger persistence.
3. Funding settlement verifier design and fake replay coverage.
4. Real venue adapters only after contracts, fake observation, paper paths, and settlement verification are stable.
