# RiseX Points Farmer

RiseX Points Farmer is a modular-monolith research system for capture-centric hedged funding opportunities on RiseX with hedge venue support, initially Hyperliquid.

The current baseline is a non-trading research, fake paper-lifecycle, funding-verification, and ledger-reconciliation skeleton. It uses fake data, does not connect to exchanges, does not place orders, and does not contain real API keys.

## Product baseline

- Main strategy: hedged funding capture on RiseX with hedge venue support.
- One `Capture` equals one funding settlement opportunity.
- Points value, expected airdrop value, leaderboard rewards in base PnL, and unreceived rebates are all explicitly zero.
- `MIN_LEG_NOTIONAL_USD = 500`.
- `MIN_NET_PROFIT_USD = 1`.
- Live trading is disabled by default.
- Future live gate evidence is fail-closed and currently requires verified fake funding settlement evidence, explicit ledger reconciliation derived from current append-only ledger history, exactly one fresh fake CapturePlan evidence record, and exactly one fresh fake execution-capability evidence record for the current Capture, route, and funding settlement opportunity.
- Where the fake live gate evidence bundle path is used, the bundle must match the current Capture, route, and funding settlement opportunity and carry the already-derived funding verification, explicit ledger reconciliation, CapturePlan freshness, and execution-capability evidence.
- Missing, stale, duplicated, cross-capture, cross-route, cross-settlement, unverified funding, false reconciliation, or non-executable execution evidence fails closed. Exact fake evidence still does not permit `LIVE_ELIGIBLE`; live trading remains disabled by default and current route decisions stop at `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED`.
- Route statuses are `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `LIVE_ELIGIBLE`, and `REJECTED`.
- `CANARY_ELIGIBLE` and a separate canary runner are forbidden.

## Offline research runner

The fake runner builds multiple `RouteCandidate` values and normalized `VenueObservation` inputs. It runs deterministic Broad Scan followed by Focused Refresh. Both stages reuse the RX-005 offline orchestration path: each successful candidate assembles a route snapshot through the single `assemble_route_snapshot()` path and evaluates through the single `evaluate_route()` decision pipeline.

```bash
python -m apps.cli.main
pytest
```

## Offline paper runner

The fake paper runner is downstream of route decisions. It consumes existing `DecisionResult` values, starts fake capture execution only for `PAPER_ELIGIBLE` decisions, and records non-started decisions as paper rejections. It does not recalculate profitability, assemble snapshots, place orders, import the live runner, or create `CapturePlan` objects.

Paper history is written through `core/accounting/ledger.py` as append-only events. `storage/sqlite/ledger.py` is a minimal deterministic SQLite implementation of the same ledger contract for offline persistence and replay tests.

## Offline funding settlement verifier

The deterministic fake funding settlement verifier is downstream of paper lifecycle and ledger evidence. It models required pre-settlement checkpoints at T-20 minutes, T-60 seconds, T-10 seconds, and T-5 seconds, then replays append-only ledger events to compare fake expected funding/notional inputs with observed fake settlement evidence.

The verifier records evidence and verification results only through `core/accounting/ledger.py`. Missing, unknown, or inconsistent settlement evidence fails closed as not verified. It does not evaluate route profitability, assemble snapshots, calculate EV, place orders, create `CapturePlan` objects, or enable live trading.

## Offline ledger reconciliation

The deterministic fake ledger reconciliation layer is downstream of route decisions, fake paper lifecycle history, and funding settlement verification. It replays append-only ledger evidence for one Capture, recomputes recorded funding settlement verification results from raw evidence through the canonical funding verifier replay, and records an explicit reconciliation result through `core/accounting/ledger.py`.

Missing, duplicated, non-contiguous, out-of-order, unknown, malformed, stale, forged, or contradictory ledger evidence fails closed as unreconciled. A reconciliation result records the checked `event_count` and `last_sequence`, and `is_ledger_explicitly_reconciled()` returns true only when the latest ledger event reconciles the exact current history. Reconciliation does not evaluate profitability, assemble snapshots, calculate EV, place orders, create `CapturePlan` objects, mutate route decisions, or enable live trading.

## Offline CapturePlan freshness gate

The deterministic fake CapturePlan freshness gate is downstream of route decisions, funding settlement verification, and ledger reconciliation. It consumes fake `CapturePlanFreshnessEvidence` values only; these are not executable order plans and do not contain exchange instructions.

Missing, stale, duplicated, cross-capture, cross-route, or cross-settlement plan evidence fails closed through `RejectReason.CAPTURE_PLAN_NOT_FRESH`. Fresh evidence alone is not permission to trade live: live trading remains disabled by default, and even with helper-derived reconciliation plus fresh evidence, `evaluate_route()` still returns `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED` and no live `CapturePlan`.

## Offline execution capability gate

The deterministic fake execution capability gate is downstream of route decisions, funding settlement verification, ledger reconciliation, and CapturePlan freshness. It consumes fake `ExecutionCapabilityEvidence` values that reference the existing four current `ExecutableQuote` contracts only.

Missing, stale, cross-route, wrong-side, wrong-target, partial-fill, contradictory, unknown-source, or non-orderbook-source execution evidence fails closed through existing centralized reject reasons. Fresh execution evidence alone is not permission to trade live: live trading remains disabled by default, and even with helper-derived reconciliation plus fresh CapturePlan and execution-capability evidence, `evaluate_route()` still returns `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED` and no live `CapturePlan`.

## Offline live gate evidence bundle

The deterministic fake live gate evidence bundle is downstream of route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, and execution capability. It aggregates already-derived fake evidence into one `LiveGateEvidenceBundle` for the future live gate sequence.

The bundle records the current `capture_id`, `route_id`, funding settlement timestamp, funding-settlement verified flag, helper-derived ledger reconciliation flag, fake `CapturePlanFreshnessEvidence`, and fake `ExecutionCapabilityEvidence`. Bundle checking lives in `core/risk/gates.py` and reuses the existing plan freshness and execution-capability gates. It does not replay ledger history, recalculate funding, recalculate VWAP, evaluate profitability, create order plans, or enable live trading.

Missing, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale/missing plan evidence, or stale/missing/non-executable execution evidence fails closed through existing centralized reject reasons. Even with live trading manually enabled and exact fake bundle evidence, `evaluate_route()` still returns `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED` and no live `CapturePlan`.

## Offline live gate evidence bundle ledger recording

The fake bundle-check result can be recorded as append-only offline ledger evidence through `core/accounting/ledger.py` and replayed through `core/accounting/reconciliation.py`.

The recorded event stores the current route, fake `LiveGateEvidenceBundle`, evaluated timestamp, referenced route-decision, funding-verification, and ledger-reconciliation event sequences, plus the already-computed RX-012 bundle gate result. Replay reconstructs the same fake evidence and reruns the existing bundle gate without recalculating EV, fees, funding, VWAP, basis, or profitability. Missing, duplicated, stale, malformed, or contradictory bundle ledger evidence fails closed.

A recorded successful fake bundle check still does not permit `LIVE_ELIGIBLE`: live trading remains disabled by default, and current route decisions stop at `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED`.

## Boundaries

Business logic has single-owner modules:

- fees: `core/economics/fees.py`
- funding: `core/economics/funding.py`
- liquidity/VWAP: `core/economics/liquidity.py`
- basis/unwind tracking: `core/economics/basis.py`
- EV: `core/economics/ev.py`
- risk gates: `core/risk/gates.py`
- route decision: `core/pipeline/evaluate.py`
- orders: `core/execution/`
- ledger writes: `core/accounting/ledger.py`
- ledger reconciliation: `core/accounting/reconciliation.py`
- funding settlement verification: `core/monitoring/funding_settlement.py`
- execution capability gating: `core/risk/gates.py`
- live gate evidence bundling: `core/risk/gates.py`

Venue adapters may fetch and normalize data only. They must not calculate EV, make route decisions, send orders, or write ledger events.
