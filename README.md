# RiseX Points Farmer

RiseX Points Farmer is a modular-monolith research system for capture-centric hedged funding opportunities on RiseX with hedge venue support, initially Hyperliquid.

The current branch remains a non-trading research, fake paper-lifecycle, funding-verification, ledger-reconciliation, and non-sending execution-planning skeleton. Offline runners still use fake data and do not place orders. RX-022 adds one read-only RiseX public market-data adapter, RX-023 adds one read-only Hyperliquid public market-data adapter, RX-024 adds one narrow real market-data route snapshot assembly handoff, RX-025 adds one-route real-data research runner behavior, RX-026 adds one approval-gated funding settlement verification path for explicit caller-supplied observed evidence, and RX-027 adds one non-sending execution planning workflow for already-verified prerequisite evidence. These pieces do not use credentials, private account endpoints, live runner behavior, order placement, or real API keys.

## Product baseline

- Main strategy: hedged funding capture on RiseX with hedge venue support.
- One `Capture` equals one funding settlement opportunity.
- Points value, expected airdrop value, leaderboard rewards in base PnL, and unreceived rebates are all explicitly zero.
- `MIN_LEG_NOTIONAL_USD = 500`.
- `MIN_NET_PROFIT_USD = 1`.
- Live trading is disabled by default.
- Future live gate evidence is fail-closed and currently requires verified funding settlement evidence from canonical replay, explicit ledger reconciliation derived from current append-only ledger history, exactly one fresh fake CapturePlan evidence record, and exactly one fresh fake execution-capability evidence record for the current Capture, route, and funding settlement opportunity.
- Where the fake live gate evidence bundle path is used, the bundle must match the current Capture, route, and funding settlement opportunity and carry the already-derived funding verification, explicit ledger reconciliation, CapturePlan freshness, and execution-capability evidence.
- Missing, stale, duplicated, cross-capture, cross-route, cross-settlement, unverified funding, false reconciliation, or non-executable execution evidence fails closed. Exact gate evidence still does not permit `LIVE_ELIGIBLE`; live trading remains disabled by default and current route decisions stop at `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED`.
- Non-sending execution plans are evidence only. They describe intended venues, symbols, sides, target notional, settlement timestamp, and prerequisite evidence references, but they contain no credentials, account state, private endpoint payloads, sendable order requests, or order placement permission.
- Route statuses are `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `LIVE_ELIGIBLE`, and `REJECTED`.
- `CANARY_ELIGIBLE` and a separate canary runner are forbidden.
- `RouteCandidate` is the authoritative route identity and selected-notional contract. Empty or malformed capture/route identity, venues, symbols, entry sides, or target notional fail at construction; positive notionals below the product minimum still fail through the existing route-evaluation minimum-notional gate.

## Roadmap posture

RX-008 through RX-016 are accepted fail-closed offline safety hardening. They prove funding verification, ledger reconciliation, fake CapturePlan freshness, fake execution capability, fake live-gate bundle checks, and SQLite replay behavior from deterministic evidence. They are not a product strategy change, not executable live architecture, and not permission to keep adding offline scaffolding ahead of the current task.

RX-022 adds a read-only RiseX observation adapter only. RX-023 adds a read-only Hyperliquid observation adapter only. RX-024 adds a one-route real market-data snapshot handoff only. RX-025 adds a one-route real-data research runner only. RX-026 adds approval-gated funding settlement verification only. RX-027 adds non-sending execution planning only. Later roadmap stages must be promoted through `NEXT_TASK.md` one at a time and remain gated: guarded live runner work only after accepted gates, future order placement only after explicit approval, and read-only monitoring/dashboard work later.

## Offline research runner

The fake runner builds multiple `RouteCandidate` values and normalized `VenueObservation` inputs. It runs deterministic Broad Scan followed by Focused Refresh. Both stages reuse the RX-005 offline orchestration path: each successful candidate assembles a route snapshot through the single `assemble_route_snapshot()` path and evaluates through the single `evaluate_route()` decision pipeline.

```bash
python -m apps.cli.main
pytest
```

## Real market-data snapshot handoff

RX-024 adds `assemble_route_snapshot_from_adapters()` in `core/pipeline/snapshot.py`. It accepts one existing `RouteCandidate`, one RiseX `VenueAdapter`, one Hyperliquid `VenueAdapter`, and an explicit timezone-aware assembly timestamp. The handoff fetches exactly the route's RiseX symbol and hedge symbol through `fetch_observation(symbol)`, then delegates construction to the existing `assemble_route_snapshot()` path.

The handoff does not call `evaluate_route()`, calculate profitability, rank routes, mutate eligibility, write ledger events, start paper lifecycle, create plans, place orders, or add live runner behavior. Adapter tests and handoff tests use injected deterministic adapters or fixtures.

## Real-data research runner

RX-025 adds `run_real_data_research_route()` in `apps/research_runner/real_data.py`. It accepts one existing `RouteCandidate`, one RiseX `VenueAdapter`, one hedge `VenueAdapter`, one explicit timezone-aware assembly timestamp, and one `EvaluationMode`.

The runner delegates snapshot creation to `assemble_route_snapshot_from_adapters()` and delegates route decisions to `evaluate_route(route, snapshot, mode)`. Adapter or snapshot handoff failures fail closed as `REJECTED` with `RejectReason.REQUIRED_LIVE_DATA_MISSING` before any route evaluation. The runner does not discover routes, rank routes, write ledger events, start paper lifecycle, verify settlement, plan execution, place orders, add CLI behavior, or enable live trading.

## Offline paper runner

The fake paper runner is downstream of route decisions. It consumes existing `DecisionResult` values, starts fake capture execution only for `PAPER_ELIGIBLE` decisions, and records non-started decisions as paper rejections. It does not recalculate profitability, assemble snapshots, place orders, import the live runner, or create `CapturePlan` objects.

Paper results include deterministic start attribution and PnL explanation copied from the input `DecisionResult`. Started runs are attributed to an ENTRY `PAPER_ELIGIBLE` decision; non-started runs identify the mode/status blocker and preserve any available expected funding, total fees, simulated roundtrip cost, and net profit already produced by `evaluate_route()`. Missing economics remain missing and do not become zero.

Paper history is written through `core/accounting/ledger.py` as append-only events. `storage/sqlite/ledger.py` is a minimal deterministic SQLite implementation of the same ledger contract for offline persistence and replay tests.

## Offline funding settlement verifier

The deterministic funding settlement verifier is downstream of paper lifecycle and ledger evidence. It models required pre-settlement checkpoints at T-20 minutes, T-60 seconds, T-10 seconds, and T-5 seconds, then replays append-only ledger events to compare checkpoint expected funding/notional inputs with observed settlement evidence.

The verifier records evidence and verification results only through `core/accounting/ledger.py`. Missing, unknown, or inconsistent settlement evidence fails closed as not verified. It does not evaluate route profitability, assemble snapshots, calculate EV, place orders, create `CapturePlan` objects, or enable live trading.

## Approval-gated funding settlement verification

RX-026 keeps settlement verification in `core/monitoring/funding_settlement.py` and ledger writes in `core/accounting/ledger.py`. `verify_approval_gated_funding_settlement()` accepts one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one explicit approval flag, and caller-supplied observed settlement funding/notional evidence.

The workflow records settlement evidence through the existing `funding_settlement_evidence_recorded` event and then calls the canonical verifier replay. Settlement evidence must carry `approval_granted=True`, `observed_at` equal to the settlement timestamp, and actual funding/notional values with `ValueSource.OBSERVED`; missing approval, false approval, stale observation time, unknown values, unobserved sources, malformed payloads, cross-capture, cross-route, cross-settlement, or contradictory evidence fails closed. The workflow does not call `evaluate_route()`, assemble snapshots, calculate profitability, reconcile ledgers, mutate eligibility, plan execution, place orders, or enable live trading.

## Execution planning without orders

RX-027 adds `plan_execution_without_orders()` in `core/execution/planning.py`. It accepts one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one existing route decision, one funding verification result, one ledger reconciliation result, one fresh CapturePlan freshness evidence record, one execution-capability evidence record, and one explicit planning timestamp.

The workflow validates exact Capture, route, settlement, ENTRY `PAPER_ELIGIBLE` decision, verified funding settlement, reconciled ledger result, fresh plan evidence, and executable capability evidence before returning a `NonSendingExecutionPlan`. The plan records intended venues, symbols, entry/unwind sides, target notional, settlement timestamp, planning validity, and prerequisite event-sequence references. It does not call `evaluate_route()`, assemble snapshots, calculate profitability, write ledger events, call adapters, import live runner behavior, create live `CapturePlan` objects, include credentials or sendable API requests, place orders, or enable live trading.

## Offline ledger reconciliation

The deterministic fake ledger reconciliation layer is downstream of route decisions, fake paper lifecycle history, and funding settlement verification. It replays append-only ledger evidence for one Capture, recomputes recorded funding settlement verification results from raw evidence through the canonical funding verifier replay, and records an explicit reconciliation result through `core/accounting/ledger.py`.

Missing, duplicated, non-contiguous, out-of-order, unknown, malformed, stale, forged, or contradictory ledger evidence fails closed as unreconciled. A reconciliation result records the checked `event_count` and `last_sequence`, and `is_ledger_explicitly_reconciled()` returns true only when the latest ledger event reconciles the exact current history. Reconciliation does not evaluate profitability, assemble snapshots, calculate EV, place orders, create `CapturePlan` objects, mutate route decisions, or enable live trading.

SQLite reopen coverage proves that `SQLiteLedger` keeps append-only sequence continuity across close/reopen boundaries. A later persisted append after successful reconciliation makes the prior explicit reconciliation stale until a new reconciliation result covers the current persisted history, and replay from reopened SQLite records remains deterministic.

SQLite reopen fail-closed coverage proves that malformed, stale, or contradictory appends persisted after reopening an existing `SQLiteLedger` remain unreconciled after SQLite round-trip. The helper-derived explicit reconciliation flag remains false for those histories, and replay from reopened records remains deterministic.

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

The recorded event stores the current route, fake `LiveGateEvidenceBundle`, evaluated timestamp, referenced route-decision, funding-verification, and ledger-reconciliation event sequences, plus the already-computed RX-012 bundle gate result. Replay reconstructs the same fake evidence and reruns the existing bundle gate without recalculating EV, fees, funding, VWAP, basis, or profitability. Missing, duplicated, stale, malformed, or contradictory bundle ledger evidence fails closed, and ledger reconciliation cannot pass over a contradictory bundle record. SQLite persistence coverage proves that valid, malformed, and contradictory bundle records round-trip through `storage/sqlite/ledger.py` with the same replay outcomes as in-memory ledger records.

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
- execution planning and orders: `core/execution/`
- ledger writes: `core/accounting/ledger.py`
- ledger reconciliation: `core/accounting/reconciliation.py`
- funding settlement verification: `core/monitoring/funding_settlement.py`
- execution capability gating: `core/risk/gates.py`
- live gate evidence bundling: `core/risk/gates.py`

Venue adapters may fetch and normalize data only. They must not calculate EV, make route decisions, send orders, or write ledger events.
