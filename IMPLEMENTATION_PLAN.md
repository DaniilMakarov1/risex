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
- RX-024 added the real market-data route snapshot assembly handoff from read-only per-venue observations into the existing `assemble_route_snapshot()` path.
- RX-025 added the one-route real-data research runner that uses the existing adapter handoff and `evaluate_route()` path.
- RX-026 added approval-gated funding settlement verification for explicit caller-supplied observed evidence.
- RX-027 added non-sending execution planning for already-verified prerequisite evidence.
- RX-028 added a guarded no-order live runner for already-verified prerequisite evidence and existing non-sending execution-plan evidence.
- RX-029 added an explicit approval-gated order placement boundary downstream of guarded no-order readiness and non-sending execution planning.
- RX-030 added a read-only monitoring dashboard renderer for already-derived deterministic fixture evidence without adding decisions, polling, network I/O, or orders.
- RX-031 recorded the review-directed no-additional-fix disposition after RX-030 and prepared a Product Owner roadmap authorization gate without changing product behavior.
- RX-032 recorded the narrowed Product Owner authorization for exactly one next governance/docs task without changing product behavior or removing hard approval gates.
- RX-033 defined Control Tower autonomous task selection for future non-dangerous RX tasks from source-of-truth repository docs without changing product behavior or removing hard approval gates.
- RX-Q001 and RX-Q002 added repository workflow, handoff validation, and supervised-worker governance.

## Accepted Offline Safety-Hardening Detour

RX-008 through RX-016 are accepted as fail-closed safety hardening only. They do not change the product strategy, do not make fake evidence executable, do not create a live runner, do not create live `CapturePlan` objects, do not connect to venues, do not place orders, and do not authorize more offline scaffolding unless a future task explicitly requires it.

The detour's purpose is to keep future live-adjacent work honest: funding settlement evidence, ledger history, fake plan freshness, fake execution capability, fake bundle checks, and SQLite replay must fail closed when evidence is missing, stale, duplicated, malformed, contradictory, or not current for the exact Capture, route, and funding settlement opportunity.

## Latest Accepted Product Task

RX-030 — Read-Only Monitoring Dashboard Without Decisions Or Orders is reviewer-accepted and finalized on `main`. It adds one read-only monitoring dashboard renderer for one existing Capture, one existing RouteCandidate, one explicit settlement timestamp, and already-derived caller-supplied deterministic evidence. It does not call `evaluate_route()`, assemble snapshots, calculate profitability, verify funding, reconcile ledgers, check live-gate bundles, plan execution, run guarded live readiness, call approval-boundary execution, write ledger events, call adapters, use credentials, perform network I/O, place orders, or enable live trading by default.

## Current Product Branch Progress

No product branch is active after RX-033 finalization. RX-034 is a governance/docs-only roadmap selection audit branch. It found that the source-of-truth docs list only RX-034 after RX-030 and do not clearly ground a concrete post-RX-034 product/runtime task, so it uses the RX-034 fallback path to prepare a metadata-only RX-035 handoff cleanup.

## Current Product Handoff

`NEXT_TASK.md` is prepared for RX-035, a metadata-only post-RX-034 roadmap handoff cleanup that records the audit outcome and preserves exactly one next task without inventing product scope.

## Remaining Gated Roadmap After RX-030

Future stages must be promoted through `NEXT_TASK.md` one at a time and accepted before any later stage starts. No additional trading, execution automation, polling, ranking, or live-order roadmap stage is authorized by RX-030, by the RX-031 no-additional-fix disposition, by the RX-032 Product Owner authorization record, or by RX-033 governance autonomy.

1. RX-035 — Post-RX-034 Roadmap Handoff Cleanup.

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

## RX-025 — Real-Data Research Runner

Add the smallest non-trading one-route real-data research runner that consumes one existing `RouteCandidate`, existing read-only venue adapters, the existing real market-data snapshot handoff, and the existing `evaluate_route(route, snapshot, mode)` path.

RX-025 implementation notes:

- `apps/research_runner/real_data.py` owns `run_real_data_research_route()`.
- The runner accepts one existing `RouteCandidate`, one RiseX `VenueAdapter`, one hedge `VenueAdapter`, an explicit timezone-aware assembly timestamp, and one `EvaluationMode`.
- Snapshot creation flows through `assemble_route_snapshot_from_adapters()` and then the existing `assemble_route_snapshot()` path.
- Route decisions flow through `evaluate_route(route, snapshot, mode)` only after successful snapshot assembly.
- Adapter or snapshot handoff failures return a deterministic `REJECTED` decision with `RejectReason.REQUIRED_LIVE_DATA_MISSING` and do not call `evaluate_route()`.
- RX-025 does not discover routes, rank routes, change fake runner behavior, write ledger events, start paper lifecycle, verify funding settlement, create plans, place orders, add private endpoints, add credentials, add live runner behavior, or create a second snapshot or decision path.

## RX-026 — Approval-Gated Real Funding Settlement Verification

Add the smallest approval-gated funding settlement verification path for one existing `Capture`, one existing `RouteCandidate`, and one explicit funding settlement timestamp.

RX-026 implementation notes:

- `core/monitoring/funding_settlement.py` owns `verify_approval_gated_funding_settlement()`.
- The workflow validates exact `Capture`/`RouteCandidate`/settlement timestamp identity before evidence is appended.
- Settlement evidence is recorded through the existing `append_funding_settlement_evidence_event()` helper and existing `funding_settlement_evidence_recorded` event type.
- Canonical funding settlement replay requires `approval_granted=True`, `observed_at == settlement_time`, and actual funding/notional values with `ValueSource.OBSERVED`.
- Missing approval, false approval, stale observation time, unknown values, unobserved sources, malformed payloads, cross-capture, cross-route, cross-settlement, or contradictory evidence fails closed.
- RX-026 does not call `evaluate_route()`, assemble snapshots, calculate profitability, mutate route eligibility, start paper lifecycle, reconcile ledgers, plan execution, place orders, add private endpoints, add credentials, add live runner behavior, or create a second funding verifier, ledger-write path, replay path, snapshot path, or decision path.

## RX-027 — Execution Planning Without Orders

Add the smallest non-sending execution planning workflow for one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, and already-derived prerequisite evidence.

RX-027 implementation notes:

- `core/execution/planning.py` owns `plan_execution_without_orders()` and `NonSendingExecutionPlan`.
- The workflow accepts exact Capture/route/settlement inputs plus an existing ENTRY `PAPER_ELIGIBLE` `DecisionResult`, verified `FundingSettlementVerificationResult`, reconciled `LedgerReconciliationResult`, one fresh `CapturePlanFreshnessEvidence`, one fresh `ExecutionCapabilityEvidence`, and an explicit timezone-aware planning timestamp.
- Missing, stale, malformed, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale plan prerequisites, or non-executable execution capability evidence fails closed through existing centralized reject reasons.
- The returned plan describes intended venues, symbols, entry and unwind sides, target notional, settlement timestamp, validity, and prerequisite event-sequence references only.
- RX-027 does not call `evaluate_route()`, assemble snapshots, calculate profitability, write ledger events, replay ledgers, call adapters, import live runner behavior, create live `CapturePlan` objects, place orders, include credentials or sendable API requests, enable live trading, add route statuses, add reject reasons, or create a second decision, snapshot, verifier, ledger-write, replay, economics, or live execution path.

## RX-028 — Guarded Live Runner Without Orders

Add the smallest guarded live runner workflow for one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one existing non-sending execution plan, and already-derived prerequisite evidence.

RX-028 implementation notes:

- `apps/live_runner/guarded.py` owns `run_guarded_live_without_orders()` and `GuardedLiveRunnerResult`.
- The workflow requires explicit `ProductRules(live_trading_enabled=True)` before any no-order ready state. Missing rules, default rules, or non-bool truthy switch values fail closed with `LIVE_TRADING_DISABLED`.
- The workflow accepts exact Capture/route/settlement inputs plus existing verified funding settlement evidence, current ledger reconciliation evidence, a passing `LiveGateEvidenceBundle`, one fresh `NonSendingExecutionPlan`, and an explicit timezone-aware evaluation timestamp.
- Missing, stale, malformed, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale plan prerequisites, non-executable execution capability evidence, missing non-sending plan, stale non-sending plan, live switch disabled, or sendable order material fails closed through existing centralized reject reasons.
- A successful result is no-order readiness only. RX-028 does not call `evaluate_route()`, assemble snapshots, calculate profitability, replay funding or ledger history, write ledger events, call adapters, import order placement behavior, create live `CapturePlan` objects, construct sendable exchange requests, place orders, enable live trading by default, add route statuses, add reject reasons, or create a second decision, snapshot, verifier, ledger-write, replay, economics, execution-planning, or order path.

## RX-029 — Explicit Approval-Gated Order Placement Boundary

Add the smallest explicit approval-gated order placement boundary for one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one existing no-order ready guarded live runner result, one existing non-sending execution plan, and one caller-supplied approval.

RX-029 implementation notes:

- `core/execution/orders.py` owns `OrderPlacementApproval`, `ApprovalGatedOrderPlacementResult`, and `run_approval_gated_order_boundary()`.
- `apps/live_runner/order_placement.py` owns `run_approval_gated_live_order_placement()` as a thin app wrapper that consumes exact `GuardedLiveRunnerResult` values without making `core/execution` import app-layer code.
- The workflow requires explicit `ProductRules(live_trading_enabled=True)`, exact Capture/route/settlement identity, no-order ready guarded result identity, a fresh existing `NonSendingExecutionPlan`, and approval evidence tied to the guarded result timestamp plus plan prerequisite references.
- Missing, stale, malformed, cross-capture, cross-route, cross-settlement, failed existing live prerequisites, non-ready guarded result, disabled live switch, missing/stale non-sending plan, missing approval, false approval, stale approval, or cross-identity approval fails closed before the injected deterministic boundary is invoked.
- RX-029 does not call `evaluate_route()`, assemble snapshots, calculate profitability, replay funding or ledger history, write ledger events, call adapters, use credentials, create exchange request payloads, place real orders, enable live trading by default, add route statuses, add reject reasons, or create a second decision, snapshot, verifier, ledger-write, replay, economics, live-runner, execution-planning, or order path.

## RX-030 — Read-Only Monitoring Dashboard Without Decisions Or Orders

Add the smallest read-only monitoring/dashboard surface for one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, and already-derived caller-supplied deterministic evidence.

RX-030 implementation notes:

- `apps/dashboard/read_only.py` owns `render_capture_monitor_view()`.
- The renderer displays exact identity, existing route decision status, funding verification state, ledger reconciliation state, live-gate bundle state, non-sending execution plan state, guarded no-order readiness state, approval evidence state, approval-boundary result state, and copied economics values.
- Missing, malformed, stale, cross-capture, cross-route, cross-settlement, unverified, unreconciled, non-ready, false approval, stale approval, or boundary-blocked inputs render as missing or blocked display state.
- Missing economics remain missing display values instead of zero.
- RX-030 does not call `evaluate_route()`, assemble snapshots, calculate profitability, verify funding, reconcile ledgers, check live-gate bundles, plan execution, run guarded live readiness, call approval-boundary execution, write ledger events, call adapters, use credentials, perform network I/O, place orders, enable live trading, add route statuses, add reject reasons, or create a second decision, snapshot, verifier, ledger-write, replay, economics, live-runner, execution-planning, or order path.

## RX-031 — Review-Directed Follow-up After RX-030

Apply only explicit reviewer-directed dashboard fixes or repository handoff metadata updates after RX-030 acceptance. In the absence of discoverable actionable reviewer feedback in local repo/git evidence or GitHub connector context, RX-031 remains metadata-only: it records the no-additional-fix disposition, leaves dashboard/product code unchanged, and prepares a Product Owner authorization gate for the next single handoff.

## RX-032 — Product Owner Roadmap Authorization Gate

Record the Product Owner authorization supplied through Control Tower as authorization for exactly one next governance/docs task. The authorization permits preparing a workflow change so Control Tower may autonomously select, create, run, review, fix, and finalize future non-dangerous RX tasks from source-of-truth repository docs without asking the user to name each next task.

RX-032 does not itself change Control Tower autonomy rules. It does not authorize live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions without explicit user approval.

## RX-033 — Control Tower Autonomous Task Selection Governance

Define the repository workflow rule that, after RX-033 reviewer acceptance, Control Tower may autonomously select, create, run, coordinate review/fixes for, and finalize future non-dangerous RX tasks from source-of-truth repository docs without asking the user to name each next task.

RX-033 preserves one RX task at a time, one clean executor task, one task branch, exactly-one-task `NEXT_TASK.md`, source-of-truth repository docs, Parent ownership, worker checkpoint requirements, and explicit reviewer acceptance. It does not authorize live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions without explicit user approval.

## RX-034 — Control Tower Roadmap Selection Audit Gate

Autonomously inspect the source-of-truth repository docs after RX-033 reviewer acceptance and prepare exactly one next RX handoff. The audit found that `IMPLEMENTATION_PLAN.md`, `STATUS.md`, and `NEXT_TASK.md` clearly identify RX-034 as the current handoff but do not clearly ground a concrete post-RX-034 product/runtime task. Under the RX-034 fallback rule, prepare RX-035 as one metadata-only post-audit handoff cleanup rather than inventing product scope or requiring Product Owner approval for ordinary safe governance work.

RX-034 preserves one RX task at a time, one clean executor task, one task branch, exactly-one-task `NEXT_TASK.md`, Parent ownership, worker checkpoint requirements, and explicit reviewer acceptance. It does not change product behavior, dashboard behavior, route discovery, ranking, polling, adapters, market-data calls, private endpoints, credentials, account state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate checks, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, replay behavior, route statuses, reject reasons, live trading by default, or any product/runtime abstraction.

## Next Sequence

1. RX-035 — Post-RX-034 Roadmap Handoff Cleanup.

Do not promote execution automation, background loops, ranking, order placement, polling, alerts, auto-refresh, private endpoints, credentials, account-state access, destructive reset, financially dangerous actions, or later roadmap stages into the current handoff unless that exact future task is explicitly user-approved for hard-stop scope or autonomously selected by Control Tower under RX-033 for non-dangerous scope and passes the repository's hard approval gates.
