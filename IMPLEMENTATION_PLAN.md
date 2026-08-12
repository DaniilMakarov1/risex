# Implementation Plan

## Roadmap Source Of Truth

This file records the consolidated implementation roadmap. `NEXT_TASK.md` remains the only handoff contract for the next Codex session and must contain exactly one task. Later roadmap stages listed here are gated future work, not permission to implement them early or combine them with the current task.

The original product direction remains hedged funding capture on RiseX with hedge venue support inside a modular monolith:

- one `Capture` equals one funding settlement opportunity;
- one `evaluate_route(route, snapshot, mode)` route decision path;
- one `assemble_route_snapshot()` route snapshot assembly path;
- one append-only ledger;
- one owner module per business logic area;
- no canary architecture, hold-next-cycle logic, artificial filters, hidden buffers, or speculative live architecture.

## Completed Accepted Work

- RX-000 through RX-007 established the project constitution, domain contracts, product rules, economics, per-venue observations, offline scan/refresh orchestration, fake paper lifecycle, and append-only ledger persistence scaffolding.
- RX-008 through RX-016 are an accepted offline safety-hardening detour. They added deterministic fail-closed replay coverage for funding settlement verification, ledger reconciliation, fake CapturePlan freshness, fake execution capability, fake live-gate evidence bundles, bundle ledger recording, SQLite bundle replay, SQLite reopen append continuity, and SQLite reopen fail-closed behavior.
- RX-018 tightened settlement timestamp alignment so one eligible route snapshot represents exactly one funding settlement opportunity.
- RX-019 updated repository handoff metadata after RX-018 review without changing product behavior.
- RX-020 hardened the existing `RouteCandidate` identity and selected-notional construction contract.
- RX-021 added deterministic fake paper-result attribution and PnL explanation downstream of existing route decisions and fake paper lifecycle events.
- RX-022 added the read-only RiseX public market-data observation adapter.
- RX-023 added the read-only Hyperliquid public market-data observation adapter.
- RX-Q001 and RX-Q002 added repository workflow, handoff validation, and supervised-worker governance.

## Accepted Offline Safety-Hardening Detour

RX-008 through RX-016 are accepted as fail-closed safety hardening only. They do not change the product strategy, do not make fake evidence executable, do not create a live runner, do not create live `CapturePlan` objects, do not connect to venues, do not place orders, and do not authorize more offline scaffolding unless a future task explicitly requires it.

The detour's purpose is to keep future live-adjacent work honest: funding settlement evidence, ledger history, fake plan freshness, fake execution capability, fake bundle checks, and SQLite replay must fail closed when evidence is missing, stale, duplicated, malformed, contradictory, or not current for the exact Capture, route, and funding settlement opportunity.

## Latest Accepted Product Task

RX-023 — Read-only Hyperliquid Observation Adapter is reviewer-accepted and finalized on `main`. It adds a read-only Hyperliquid public market-data adapter only, preserves per-venue observation normalization, and does not assemble route snapshots, evaluate routes, rank routes, write ledger events, create plans, place orders, or add live runner behavior.

## Current Product Branch Progress

RX-024 — Real Market-Data Route Snapshot Assembly is implemented on the current task branch and pending review. It adds a one-route handoff from existing read-only RiseX and Hyperliquid `VenueAdapter.fetch_observation(symbol)` calls into the existing `assemble_route_snapshot()` path. It does not evaluate routes, rank routes, mutate eligibility, write ledger events, start paper lifecycle, create plans, place orders, or add live runner behavior.

## Current Product Handoff

RX-025 — Real-Data Research Runner is the immediate next task in `NEXT_TASK.md`.

## Remaining Gated Roadmap After RX-024

Future stages must be promoted through `NEXT_TASK.md` one at a time and accepted before any later stage starts:

1. Add a real-data research runner that still uses the existing scan/refresh and `evaluate_route()` paths.
2. Verify funding settlement on real or explicitly approved observed evidence, with approval gates documented in the task prompt.
3. Add execution planning without orders; plans must remain non-sending until a later explicit task.
4. Add a guarded live runner only after explicit acceptance gates prove data, ledger, settlement verification, plan freshness, execution capability, and live switch behavior.
5. Add order placement only in a future explicitly approved task.
6. Add read-only monitoring/dashboard work later, without turning it into a decision, execution, or ledger-write path.

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

## RX-018 — Settlement Timestamp Alignment Contract

Tighten route/snapshot alignment so RiseX and hedge funding settlement timestamps must match before a route can pass into executability, Entry EV, and paper eligibility. Preserve per-leg settlement timestamps in `assemble_route_snapshot()`, fail mismatches through existing `RejectReason.TECHNICALLY_NOT_EXECUTABLE`, and avoid changing economics, VWAP/liquidity, adapters, orders, live behavior, route statuses, reject reasons, or second decision paths.

## RX-019 — Reviewer-Directed Follow-up After RX-018

Apply reviewer-directed repository handoff metadata fixes after RX-018 acceptance. Keep RX-018 as the latest accepted product baseline, record RX-019 as metadata-only follow-up, and prepare the next task prompt without changing product behavior.

## RX-020 — RouteCandidate Identity And Notional Contract Hardening

Harden the existing `RouteCandidate` construction contract so malformed capture id, route id, venues, symbols, entry sides, or target notional fail before snapshot assembly, route evaluation, paper lifecycle, ledger evidence, or future live-gate evidence can consume the route. Preserve `assemble_route_snapshot()` and `evaluate_route(route, snapshot, mode)` as the single snapshot and decision paths, keep positive below-minimum notionals in the existing minimum-notional risk gate, and avoid real adapters, market-data assembly, paper-result attribution, execution planning, live behavior, orders, route statuses, reject reasons, or later roadmap stages.

## RX-021 — Paper Result Attribution And PnL Explanation

Add deterministic paper-result attribution and PnL explanation downstream of existing route decisions and fake paper lifecycle events. Preserve fake paper start eligibility exactly as ENTRY `PAPER_ELIGIBLE`, explain non-started decisions through deterministic mode/status blockers, copy existing `DecisionResult` economics into inspectable paper results and optional paper ledger payloads, and keep missing economics as missing instead of zero.

RX-021 must not recalculate EV, fees, funding, VWAP, liquidity, basis, spread, slippage, or profitability; mutate route eligibility; add route statuses or reject reasons; create adapters, orders, live runner behavior, executable `CapturePlan`, or a second ledger/replay path.

## RX-022 — Read-only RiseX Observation Adapter

Add a read-only RiseX adapter that fetches and normalizes per-venue `VenueObservation` inputs only. Keep route snapshot assembly in `assemble_route_snapshot()`, route decisions in `evaluate_route()`, and all trading/execution behavior out of scope.

RX-022 implementation notes:

- `core/venues/risex.py` fetches public `GET /v1/markets` and `GET /v1/orderbook` data and returns one normalized `VenueObservation`.
- RiseX funding rates and fee bps are not converted into USD cash flow inside the adapter because `VenueObservation` requires source-aware cash values and `fetch_observation(symbol)` has no selected notional or account fee tier.
- Missing or malformed markets, settlement timestamps, orderbook sides, prices, quantities, or observation timestamps fail closed before a `VenueObservation` is returned.
- RX-022 does not assemble route snapshots, evaluate routes, rank routes, write ledger events, create plans, use private endpoints, place orders, add live runner behavior, or add a Hyperliquid adapter.

## RX-023 — Read-only Hyperliquid Observation Adapter

Add a read-only Hyperliquid adapter that fetches and normalizes per-venue `VenueObservation` inputs only. Keep route snapshot assembly in `assemble_route_snapshot()`, route decisions in `evaluate_route()`, and all trading/execution behavior out of scope.

RX-023 implementation notes:

- `core/venues/hyperliquid.py` posts only public `type=metaAndAssetCtxs`, `type=l2Book`, and `type=predictedFundings` requests to Hyperliquid `/info` and returns one normalized `VenueObservation`.
- Hyperliquid funding rates and fee schedules are not converted into USD cash flow inside the adapter because `VenueObservation` requires source-aware cash values and `fetch_observation(symbol)` has no selected notional, side, or account fee tier.
- Missing or malformed market metadata, asset contexts, orderbook sides, prices, sizes, observation timestamps, or predicted `HlPerp.nextFundingTime` values fail closed before a `VenueObservation` is returned.
- RX-023 does not assemble route snapshots, evaluate routes, rank routes, write ledger events, create plans, use private account endpoints, place orders, add live runner behavior, or change the RiseX adapter.

## RX-024 — Real Market-Data Route Snapshot Assembly

Add the smallest real market-data route snapshot assembly handoff that consumes existing read-only per-venue observations and calls the existing `assemble_route_snapshot()` path for one `RouteCandidate` at a time.

RX-024 implementation notes:

- `core/pipeline/snapshot.py` owns `assemble_route_snapshot_from_adapters()`.
- The handoff calls `fetch_observation(route.risex_symbol)` once on the RiseX adapter and `fetch_observation(route.hedge_symbol)` once on the hedge adapter.
- The handoff passes the two returned `VenueObservation` values into the existing `assemble_route_snapshot()` function and relies on that path for route-aligned snapshot construction and metadata validation.
- Non-observation adapter returns and contradictory route/observation metadata fail before any route decision can run.
- RX-024 does not call `evaluate_route()`, calculate EV, rank routes, mutate eligibility, write ledger events, start paper lifecycle, create plans, place orders, add private endpoints, add credentials, add live runner behavior, or create a second snapshot assembly path.

## Next Sequence

1. RX-025 — Real-Data Research Runner.

Do not promote any later roadmap stage into the current handoff until RX-025 is reviewed and accepted.
