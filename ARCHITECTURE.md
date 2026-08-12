# Architecture

RiseX Points Farmer is a modular monolith. The repository is organized around a single capture-centric decision pipeline and explicit ownership of business logic.

## Top-level layout

```text
apps/
  research_runner/
  paper_runner/
  live_runner/
  dashboard/
  cli/
core/
  domain/
  venues/
  pipeline/
  economics/
  risk/
  execution/
  accounting/
  monitoring/
  config/
storage/
  sqlite/
  migrations/
tests/
  unit/
  integration/
  invariant/
  replay/
```

## Core domain

- `Capture`: one funding settlement opportunity.
- `CaptureState`: lifecycle state for a `Capture`, separate from route eligibility.
- `RouteCandidate`: a potential RiseX + hedge route with authoritative capture id, route id, venues, symbols, target notional, and intended opposing entry sides.
- `VenueObservation`: normalized read-only data for one venue and one symbol: timezone-aware observation timestamp, order book, expected funding cash flow, funding settlement timestamp, and per-venue fee model.
- `VenueSnapshot`: one route-aligned normalized snapshot assembled from a RiseX observation and a hedge observation for the shared decision pipeline.
- `OrderBookLevel`: one normalized price level where size is base asset quantity.
- `OrderBook`: normalized current bids and asks used for offline VWAP calculations.
- `ExecutableQuote`: current executable VWAP quote for a target notional; `executable=True` means the full quote target notional is filled.
- `EstimatedValue`: numeric value plus explicit source, with `UNKNOWN` carrying no numeric fallback.
- `FeeModel`: source-aware fee components for entry and immediate unwind economics.
- `FundingSnapshot`: source-aware expected funding cash flows for one capture opportunity.
- `DecisionResult`: result of the shared decision pipeline.
- `CapturePlanFreshnessEvidence`: fake non-executable evidence that one plan id/version is fresh for exactly one `capture_id`, one `route_id`, and one funding settlement timestamp.
- `ExecutionCapabilityEvidence`: fake non-executable order-book quote evidence that the current route can still execute its full selected target notional on all required entry and unwind sides.
- `LiveGateEvidenceBundle`: fake non-executable aggregate evidence for the future live gate sequence, combining funding verification, explicit ledger reconciliation, CapturePlan freshness, and execution capability evidence for exactly one Capture settlement.
- `RouteStatus`: `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `LIVE_ELIGIBLE`, `REJECTED`.
- `EvaluationMode`: `DISCOVERY` or `ENTRY`.
- `ValueSource`: `DOCUMENTED`, `OBSERVED`, `ESTIMATED_FROM_ORDERBOOK`, `ESTIMATED_FROM_LAST_VALUE`, `USER_CONFIGURED`, `UNKNOWN`.
- `RejectReason`: the centralized route rejection and live-gate reason enum.
- `FundingCheckpointRequirement`: one required pre-settlement observation offset for future settlement proof.
- `FundingSettlementVerificationResult`: deterministic replay result proving whether checkpoint evidence and approval-gated observed settlement evidence agree for one Capture settlement.
- `LedgerReconciliationResult`: deterministic replay result proving whether one Capture ledger history is internally consistent and explicitly reconciled.
- `LiveGateEvidenceBundleReplayResult`: deterministic accounting replay result proving whether one recorded fake live-gate evidence bundle check is well-formed, current, and consistent with the existing bundle gate result.
- `PaperResultExplanation`: app-local fake paper result attribution copied from the input `DecisionResult`, including start/non-start blockers and existing PnL components without recalculating profitability.

## Capture lifecycle state machine

`core/domain/state_machine.py` is the single authoritative Capture lifecycle state machine. It owns the allowed transition table, validates transitions, and returns updated immutable `Capture` instances. It does not send orders, call venue adapters, write ledger events, or import execution modules.

Allowed lifecycle states:

- `DISCOVERED`
- `UNDERWRITING`
- `REJECTED`
- `APPROVED`
- `ENTERING`
- `PARTIALLY_ENTERED`
- `HEDGED`
- `WAITING_SETTLEMENT`
- `SETTLED`
- `EXITING`
- `CLOSED`
- `FAILED`
- `EMERGENCY_FLATTENED`

Normal transitions:

- `DISCOVERED -> UNDERWRITING`
- `UNDERWRITING -> APPROVED`
- `UNDERWRITING -> REJECTED`
- `APPROVED -> ENTERING`
- `ENTERING -> PARTIALLY_ENTERED`
- `ENTERING -> HEDGED`
- `PARTIALLY_ENTERED -> HEDGED`
- `HEDGED -> WAITING_SETTLEMENT`
- `WAITING_SETTLEMENT -> SETTLED`
- `SETTLED -> EXITING`
- `EXITING -> CLOSED`

Any non-terminal Capture may transition to `FAILED`. Capture states with possible market exposure (`ENTERING`, `PARTIALLY_ENTERED`, `HEDGED`, `WAITING_SETTLEMENT`, `SETTLED`, `EXITING`) may transition to `EMERGENCY_FLATTENED`. Terminal states are `REJECTED`, `CLOSED`, `FAILED`, and `EMERGENCY_FLATTENED`.

## Single-owner business logic

- Fees are calculated only in `core/economics/fees.py`.
- Funding is calculated only in `core/economics/funding.py`.
- Liquidity and VWAP are calculated only in `core/economics/liquidity.py`.
- Basis and unwind tracking belong only in `core/economics/basis.py`.
- Entry EV is calculated only in `core/economics/ev.py`.
- Risk gates belong only in `core/risk/gates.py`.
- Route snapshot assembly and the real market-data snapshot handoff happen only in `core/pipeline/snapshot.py`.
- Route decisions happen only in `core/pipeline/evaluate.py`.
- Offline route-candidate orchestration happens only in `core/pipeline/offline_scan.py`.
- Broad Scan and Focused Refresh orchestration happens only in `core/pipeline/scan_refresh.py`.
- One-route real-data research orchestration happens only in `apps/research_runner/real_data.py`.
- Orders can be sent only through `core/execution/`.
- Ledger writes happen only through `core/accounting/ledger.py`.
- Ledger reconciliation happens only in `core/accounting/reconciliation.py`.
- Funding settlement verification happens only in `core/monitoring/funding_settlement.py`.
- Fake paper lifecycle orchestration happens only in `apps/paper_runner/lifecycle.py`.
- Fake paper result attribution and PnL explanation happen only in `apps/paper_runner/lifecycle.py`; optional explanation payload recording remains inside existing accounting ledger events.
- Execution capability live gating happens only in `core/risk/gates.py` and reuses existing `ExecutableQuote` contracts.
- Live gate evidence bundle checking happens only in `core/risk/gates.py` and reuses existing funding verification, ledger reconciliation, CapturePlan freshness, and execution capability evidence outputs.
- Live gate evidence bundle ledger recording happens only in `core/accounting/ledger.py`; replay validation happens only in `core/accounting/reconciliation.py` and reuses the existing risk gate result.

## Roadmap anti-drift

The original architecture remains unchanged after the accepted offline safety-hardening work:

- The system is still a modular monolith.
- The domain is still capture-centric and contract-centric.
- One `Capture` still represents one funding settlement opportunity.
- `evaluate_route(route, snapshot, mode)` is still the only route decision path.
- `assemble_route_snapshot()` is still the only route snapshot assembly path.
- The append-only ledger remains the only accounting history.
- Each business logic area still has exactly one owner module.

RX-008 through RX-016 added deterministic fail-closed offline safety scaffolding around funding settlement verification, ledger reconciliation, fake CapturePlan freshness, fake execution capability, fake live-gate evidence bundles, bundle ledger recording, and SQLite replay behavior. These modules are accepted safety hardening only. They are not executable live trading architecture, do not create order plans, do not place orders, do not connect to venues, do not replace real read-only adapters, and do not permit future tasks to add speculative second paths.

Future roadmap stages are gates. A later roadmap item is not permission to implement live trading, adapters, dashboards, monitoring, execution planning, or order placement before that exact task is written into `NEXT_TASK.md`, reviewed in scope, implemented on its own branch, and accepted.

## Product rules

`core/config/product_rules.py` owns the single authoritative `ProductRules` object for product-level constants:

- `min_leg_notional_usd = 500`
- `min_net_profit_usd = 1`
- `live_trading_enabled = false`
- `points_value_usd = 0`
- `expected_airdrop_value_usd = 0`
- `leaderboard_rewards_base_pnl_usd = 0`
- `unreceived_rebates_usd = 0`

No other config object owns those same product constants.

## Evaluation pipeline

`evaluate_route(route, snapshot, mode)` is the only route decision path.

RX-003 behavior:

1. Verify the route target notional meets the configured minimum.
2. Verify route/snapshot alignment through `core/risk/gates.py` before any Entry EV calculation.
3. Verify all executable VWAP quotes meet the configured minimum notional and fully fill their own target notional.
4. Calculate entry EV from source-aware funding, source-aware fees, and simulated immediate roundtrip cost.
5. Reject through centralized `RejectReason` values, not ad hoc reason strings.
6. Reject when minimum leg notional is not met, route/snapshot alignment fails, required order-book liquidity cannot execute the configured minimum notional, required economics data is missing, or net profit is below the configured minimum.
7. Return `PAPER_ELIGIBLE` for profitable offline routes while live gates are not implemented.
8. Never create a live `CapturePlan` in RX-003, even if `ProductRules(live_trading_enabled=True)` is passed manually.
9. Never place orders.
10. Optionally append the decision event to the ledger through `core/accounting/ledger.py`.

RX-009 tightens future live gating without enabling live trading:

1. `core/risk/gates.py` requires explicit `ledger_explicitly_reconciled=True` before a future live path can pass the ledger reconciliation gate.
2. Missing or false reconciliation fails closed through centralized `RejectReason.LEDGER_NOT_RECONCILED`.
3. Tests derive that true value from `is_ledger_explicitly_reconciled(ledger.records())`, not from a manually supplied success flag.
4. RX-010 inserts a fresh CapturePlan evidence gate after this ledger gate; no live `CapturePlan` is created.

RX-010 adds deterministic offline fresh CapturePlan gate contracts and fake replay coverage:

1. `CapturePlanFreshnessEvidence` is fake plan evidence only. It records `plan_id`, `plan_version`, `capture_id`, `route_id`, one `settlement_time`, `planned_at`, `valid_until`, a source, and an optional referenced ledger reconciliation sequence.
2. `CapturePlanFreshnessEvidence` rejects non-timezone-aware timestamps, empty identity fields, `ValueSource.UNKNOWN`, invalid validity windows, and non-positive referenced reconciliation sequences at construction.
3. `core/risk/gates.py` owns `check_capture_plan_freshness_gate()`. Missing, duplicated, stale, future-dated, cross-capture, cross-route, cross-settlement, malformed, or unknown-source fake plan evidence fails closed through `RejectReason.CAPTURE_PLAN_NOT_FRESH`.
4. `check_live_capture_allowed()` evaluates live gates in this order: live trading switch, explicit ledger reconciliation, fresh CapturePlan evidence, then `RejectReason.LIVE_GATES_NOT_IMPLEMENTED`.
5. `evaluate_route()` may receive fake plan evidence for future live gating, but it does not read ledger/storage, mutate profitability decisions, create live `CapturePlan` objects, import execution/live runner modules, or return `LIVE_ELIGIBLE`.
6. Even with live trading manually enabled, helper-derived ledger reconciliation, and exact fresh plan evidence, current route decisions remain `PAPER_ELIGIBLE` with `RejectReason.LIVE_GATES_NOT_IMPLEMENTED`.

RX-011 adds deterministic offline execution-capability gate contracts and fake replay coverage:

1. `ExecutionCapabilityEvidence` is fake, non-executable evidence only. It records one `capture_id`, one `route_id`, one funding settlement timestamp, a freshness window, an order-book source, and the four current `ExecutableQuote` values already used by route/snapshot contracts.
2. `core/risk/gates.py` owns `check_execution_capability_gate()`. Missing, stale, future-dated, cross-capture, cross-route, cross-settlement, malformed, non-orderbook-source, missing-side, wrong-side, wrong-target-notional, partial-fill, or contradictory evidence fails closed.
3. Execution capability does not recalculate VWAP, profitability, fees, funding, EV, or basis. It reuses `quote_is_executable_for_notional()` and the existing quote identity/source/side/target-notional contracts.
4. `check_live_capture_allowed()` evaluates live gates in this order: live trading switch, explicit ledger reconciliation, fresh CapturePlan evidence, fresh execution-capability evidence, then `RejectReason.LIVE_GATES_NOT_IMPLEMENTED`.
5. `evaluate_route()` may receive fake execution-capability evidence for future live gating, but it does not read ledger/storage, call adapters, calculate VWAP, import execution/live runner modules, place orders, create live `CapturePlan` objects, or return `LIVE_ELIGIBLE`.
6. Even with live trading manually enabled, helper-derived ledger reconciliation, exact fresh plan evidence, and exact fresh execution-capability evidence, current route decisions remain `PAPER_ELIGIBLE` with `RejectReason.LIVE_GATES_NOT_IMPLEMENTED`.

RX-012 adds deterministic offline live-gate evidence bundle contracts and fake replay coverage:

1. `LiveGateEvidenceBundle` is fake, immutable, non-executable aggregate evidence for exactly one `capture_id`, one `route_id`, and one funding settlement timestamp.
2. The bundle carries already-derived proof outputs: funding settlement verified flag, helper-derived ledger reconciliation flag, fake CapturePlan freshness evidence, and fake execution-capability evidence.
3. `core/risk/gates.py` owns `check_live_gate_evidence_bundle()`. Missing, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale/missing plan evidence, or stale/missing/non-executable execution evidence fails closed through existing centralized reject reasons.
4. Bundle checking does not replay ledger history, replay funding settlement verification, recalculate VWAP, recalculate EV, decide profitability, call adapters, write ledger events, create order plans, or place orders.
5. `evaluate_route()` may receive a fake live-gate evidence bundle for future live gating, but it still does not read ledger/storage, import execution/live runner modules, place orders, create live `CapturePlan` objects, or return `LIVE_ELIGIBLE`.
6. Even with live trading manually enabled and exact fake bundle evidence, current route decisions remain `PAPER_ELIGIBLE` with `RejectReason.LIVE_GATES_NOT_IMPLEMENTED`.

RX-013 adds deterministic offline live-gate evidence bundle ledger recording and replay coverage:

1. `core/accounting/ledger.py` owns the `live_gate_evidence_bundle_recorded` append-only event type and append helper.
2. The event records one current `RouteCandidate`, one fake `LiveGateEvidenceBundle`, the evaluated timestamp, the referenced route-decision, funding-verification, and ledger-reconciliation event sequences, and the already-computed RX-012 bundle gate result.
3. `core/accounting/reconciliation.py` owns `replay_live_gate_evidence_bundle_recording()`. Replay validates exactly one current bundle record, referenced prior history, payload shape, stale reconciliation references, plan reconciliation references, and recorded result consistency by rerunning `check_live_gate_evidence_bundle()`.
4. Core ledger reconciliation treats `live_gate_evidence_bundle_recorded` as a known accounting event and requires any current bundle record to replay successfully before reconciliation can pass. Appending this event after a successful reconciliation makes the full ledger history unreconciled until a later reconciliation result covers the new append.
5. Bundle ledger replay does not recalculate EV, fees, funding, VWAP, basis, or profitability; it does not call adapters, call execution modules, place orders, create live plans, mutate route decisions, or return `LIVE_ELIGIBLE`.
6. Even with a replayed successful fake bundle check, current route decisions remain `PAPER_ELIGIBLE` with `RejectReason.LIVE_GATES_NOT_IMPLEMENTED`.

RX-014 adds deterministic SQLite persistence replay coverage for the RX-013 bundle record:

1. `storage/sqlite/ledger.py` remains the existing append-only persistence contract; no migration or second storage layer is introduced.
2. Persisted `live_gate_evidence_bundle_recorded` payloads replay with the same bundle result and referenced route-decision, funding-verification, and ledger-reconciliation event sequences as in-memory ledger records.
3. Persisted malformed or contradictory bundle records still fail closed after SQLite round-trip.
4. SQLite replay coverage does not recalculate EV, fees, funding, VWAP, basis, or profitability, and does not call adapters, execution modules, or live runner code.

RX-015 adds deterministic SQLite reopen append-continuity replay coverage:

1. `SQLiteLedger` remains the existing minimal append-only persistence contract; no migration or second storage layer is introduced.
2. Appending after closing and reopening an existing SQLite ledger continues from the last persisted sequence without overwriting or reusing earlier sequences.
3. A persisted append after successful reconciliation makes `is_ledger_explicitly_reconciled(reopened.records())` false until a later reconciliation result covers the new append with current `event_count` and `last_sequence`.
4. Reopened SQLite records replay deterministically after the later reconciliation.
5. SQLite reopen replay coverage does not recalculate EV, fees, funding, VWAP, basis, or profitability, and does not call adapters, execution modules, place orders, create live plans, mutate route eligibility, or return `LIVE_ELIGIBLE`.

RX-016 adds deterministic SQLite reopen fail-closed replay coverage:

1. `SQLiteLedger` remains the existing minimal append-only persistence contract; no migration or second storage layer is introduced.
2. Malformed, stale, or contradictory appends persisted after reopening an existing SQLite ledger remain unreconciled after SQLite round-trip.
3. `is_ledger_explicitly_reconciled(reopened.records())` remains false for those fail-closed histories, and the explicit reconciliation gate returns `LEDGER_NOT_RECONCILED`.
4. Reconciliation replay from reopened SQLite records remains deterministic for malformed, stale, and contradictory persisted appends.
5. SQLite reopen fail-closed replay coverage does not recalculate EV, fees, funding, VWAP, basis, or profitability, and does not call adapters, execution modules, place orders, create live plans, mutate route eligibility, or return `LIVE_ELIGIBLE`.

RX-004 adds a deterministic offline snapshot assembly layer before evaluation:

1. Venue adapters return per-venue `VenueObservation` objects, never cross-venue snapshots.
2. `core/pipeline/snapshot.py` owns the single `assemble_route_snapshot()` function.
3. The assembly function accepts one `RouteCandidate`, a mapping of `(venue, symbol)` observations, and an explicit timezone-aware assembly timestamp.
4. It locates the required RiseX and hedge observations, fails explicitly on missing or contradictory metadata, and uses `calculate_executable_quote()` for all four entry/immediate-unwind quotes.
5. It preserves per-leg observation timestamps and funding settlement timestamps on the resulting `VenueSnapshot`.
6. It does not call `evaluate_route()`, calculate EV, apply eligibility, rank routes, write ledger events, create `Capture`/`CapturePlan`, connect to venues, or place orders.

RX-024 adds a narrow real market-data snapshot handoff:

1. `core/pipeline/snapshot.py` owns `assemble_route_snapshot_from_adapters()`.
2. The handoff accepts one existing `RouteCandidate`, one RiseX `VenueAdapter`, one hedge `VenueAdapter`, and an explicit timezone-aware assembly timestamp.
3. It calls `fetch_observation(route.risex_symbol)` once on the RiseX adapter and `fetch_observation(route.hedge_symbol)` once on the hedge adapter.
4. It passes the two returned `VenueObservation` values into the existing `assemble_route_snapshot()` path; the handoff does not construct executable quotes, merge economics, or replace route/snapshot validation.
5. Adapter failures, non-observation returns, missing route observations, or contradictory observation metadata fail before any route decision path can run.
6. It does not call `evaluate_route()`, calculate EV, rank routes, mutate eligibility, write ledger events, start paper lifecycle, create plans, call execution modules, connect to private endpoints, or place orders.

RX-025 adds a narrow one-route real-data research runner:

1. `apps/research_runner/real_data.py` owns `run_real_data_research_route()`.
2. The runner accepts one existing `RouteCandidate`, one RiseX `VenueAdapter`, one hedge `VenueAdapter`, an explicit timezone-aware assembly timestamp, and one `EvaluationMode`.
3. It calls `assemble_route_snapshot_from_adapters()`, which remains the real market-data handoff into the single `assemble_route_snapshot()` path.
4. It calls `evaluate_route(route, snapshot, mode)` only after successful snapshot assembly and passes no ledger.
5. Adapter failures, non-observation returns, or contradictory route/observation metadata fail closed as `RejectReason.REQUIRED_LIVE_DATA_MISSING` before evaluation.
6. It does not discover routes, rank routes, loop in the background, write ledger events, start paper lifecycle, verify funding settlement, create plans, call execution modules, connect to private endpoints, place orders, or add live runner behavior.

RX-026 adds one approval-gated funding settlement verification workflow:

1. `core/monitoring/funding_settlement.py` owns `verify_approval_gated_funding_settlement()`.
2. The workflow accepts one existing `Capture`, one existing `RouteCandidate`, one explicit timezone-aware funding settlement timestamp, one explicit approval flag, one explicit observation timestamp, and caller-supplied actual settlement funding/notional evidence.
3. It validates that the `Capture`, `RouteCandidate`, and explicit settlement timestamp match before appending evidence.
4. It records settlement evidence only through the existing `append_funding_settlement_evidence_event()` helper and existing `funding_settlement_evidence_recorded` event type.
5. Canonical funding settlement replay requires `approval_granted=True`, `observed_at == settlement_time`, and actual funding/notional values with `ValueSource.OBSERVED`; missing, false, stale, malformed, cross-capture, cross-route, cross-settlement, unobserved, unknown, or contradictory evidence fails closed.
6. It then calls the existing `verify_funding_settlement()` replay path and does not calculate verification success itself.
7. It does not call `evaluate_route()`, assemble snapshots, calculate EV/profitability, reconcile ledgers, mutate route eligibility, start paper lifecycle, create plans, call execution modules, connect to private endpoints, place orders, or add live runner behavior.

RX-005 adds deterministic offline orchestration over multiple fake route candidates:

1. `core/pipeline/offline_scan.py` owns the route-candidate iteration layer.
2. The orchestration function accepts `RouteCandidate` values, one normalized observation mapping, an explicit timezone-aware assembly timestamp, and an explicit `EvaluationMode`.
3. For every candidate, it calls the single `assemble_route_snapshot()` function and then calls the single `evaluate_route(route, snapshot, mode)` decision path.
4. If snapshot assembly fails because required normalized observations are missing or contradictory, the candidate fails closed as a deterministic `DecisionResult` with `RejectReason.REQUIRED_LIVE_DATA_MISSING`; `evaluate_route()` is not called for that candidate.
5. The orchestration layer does not calculate VWAP, fees, funding, EV, risk gates, ranking, acceptance, or route eligibility for successfully assembled snapshots outside the existing owner modules.
6. It does not create `CapturePlan` objects, write ledger events, connect to venues, import execution modules, start paper execution, or place orders.

RX-006 adds deterministic two-stage fake scan orchestration over the RX-005 path:

1. `core/pipeline/scan_refresh.py` owns the fake Broad Scan and Focused Refresh orchestration layer.
2. Broad Scan calls `evaluate_offline_candidates()` with `EvaluationMode.DISCOVERY`.
3. Broad Scan returns deterministic decisions plus the same `RouteCandidate` contracts as refresh candidates; it does not rank, accept, reject, filter, or mutate candidates outside the shared decision path.
4. Focused Refresh accepts only a `BroadScanResult`, uses refreshed normalized observations, and calls `evaluate_offline_candidates()` with `EvaluationMode.ENTRY`.
5. Every successfully refreshed candidate still flows through `assemble_route_snapshot()` and then `evaluate_route(route, snapshot, mode)`.
6. Snapshot assembly failures continue to fail closed as `RejectReason.REQUIRED_LIVE_DATA_MISSING` before `evaluate_route()` is called.
7. RX-006 remains fake-data-only, deterministic, offline, read-only, and non-trading. It does not create `CapturePlan` objects, write ledger events, import execution or runner modules, connect to venues, start paper execution, or place orders.

RX-007 adds deterministic fake paper lifecycle and append-only ledger persistence scaffolding:

1. `apps/paper_runner/lifecycle.py` owns the fake paper lifecycle runner.
2. The paper runner accepts an existing `RouteCandidate`, an existing `DecisionResult`, an explicit funding settlement timestamp, and an append-only ledger.
3. The paper runner starts fake capture execution only when the input decision status is `PAPER_ELIGIBLE` and the input decision mode is `EvaluationMode.ENTRY`.
4. `PAPER_ELIGIBLE` discovery decisions, `REJECTED`, `RESEARCH_ONLY`, and `LIVE_ELIGIBLE` decisions are recorded as paper rejections and do not create a `Capture`.
5. A started paper lifecycle creates exactly one `Capture` using the route `capture_id`, route `route_id`, and the settlement timestamp for one funding settlement opportunity.
6. Every fake paper state change uses the single `core/domain/state_machine.py` transition contract.
7. Paper history is written only through `core/accounting/ledger.py` event helpers: route decision, paper capture opened, paper settlement observed, paper capture closed, and paper rejection recorded.
8. `core/accounting/ledger.py` owns immutable ledger event contracts, append helper functions, and deterministic paper replay into final `Capture` states.
9. `storage/sqlite/ledger.py` is minimal SQLite append-only persistence scaffolding for deterministic offline tests; it does not introduce migrations, adapters, exchange connectivity, secrets, or live trading.
10. RX-007 does not call `evaluate_route()`, assemble route snapshots, calculate EV, import economics/risk/execution/live runner modules, place orders, mutate route eligibility decisions, create `CapturePlan` objects, enable live trading, or hold a Capture into another funding cycle.

RX-021 adds deterministic fake paper-result attribution and PnL explanation downstream of RX-007:

1. `apps/paper_runner/lifecycle.py` owns `PaperResultExplanation` as the returned fake paper result explanation contract.
2. Paper start attribution reuses the existing start predicate: only ENTRY `PAPER_ELIGIBLE` decisions start fake paper captures.
3. Discovery decisions, rejected decisions, research-only decisions, and live-eligible decisions still record paper rejections and do not create `Capture` objects.
4. PnL explanation copies existing `DecisionResult` economics: expected funding, total fees, simulated roundtrip cost, and net profit when `entry_ev` is present, plus top-level decision net profit.
5. Missing `DecisionResult` economics remain `None`; paper attribution does not treat unknown values as zero.
6. Existing paper ledger events may carry optional `paper_result_explanation` payloads. Reconciliation shape-validates optional payloads when present, semantically checks them against authoritative route-decision or rejection event payloads where ledger evidence exists, and fails closed on contradictory well-formed explanation fields. It does not replay or recalculate profitability and does not change paper lifecycle state replay.
7. RX-021 does not call `evaluate_route()`, assemble route snapshots, recalculate EV, fees, funding, VWAP, liquidity, basis, spread, slippage, or profitability, create plans, place orders, import live/execution modules, or change route eligibility.

RX-008 adds deterministic offline funding settlement verifier contracts and fake replay coverage:

1. `core/monitoring/funding_settlement.py` owns the funding settlement verifier.
2. The verifier models required pre-settlement checkpoints at T-20 minutes, T-60 seconds, T-10 seconds, and T-5 seconds.
3. Checkpoint evidence, observed settlement evidence, and verification results are written only through append-only helper functions in `core/accounting/ledger.py`.
4. Replay compares source-aware fake expected RiseX and hedge funding inputs plus target notional from required checkpoints with fake observed settlement funding and actual leg notionals.
5. Actual settlement funding and actual settlement notional evidence are proof inputs and must use `ValueSource.OBSERVED`; user-configured, documented, estimated, unknown, missing, malformed, or non-positive notional actuals fail closed as not verified.
6. Pre-settlement expected funding checkpoints remain source-aware expected inputs and are not required to be `ValueSource.OBSERVED` only.
7. Missing required checkpoints, missing observed settlement evidence, unknown funding/notional values, unobserved actual settlement evidence, inconsistent capture identity, inconsistent settlement time, inconsistent checkpoint timing, inconsistent funding evidence, or inconsistent notional evidence fail closed as not verified.
8. The verifier stays downstream of existing route decisions, snapshots, Capture lifecycle, and ledger events. It does not decide route profitability, call route evaluation, call route snapshot assembly, calculate EV, place orders, create `CapturePlan` objects, mutate route eligibility decisions, or enable live trading.
9. Future live eligibility remains blocked until live gates, ledger reconciliation, fresh plan handling, execution capability, and proven funding settlement verification are implemented together in a future task.

RX-009 adds deterministic offline ledger reconciliation contracts and fake replay coverage:

1. `core/accounting/reconciliation.py` owns reconciliation for one Capture ledger history.
2. Reconciliation replays append-only ledger evidence downstream of route decision events, fake paper lifecycle events, funding evidence, and funding settlement verification results.
3. Reconciliation requires one ENTRY `PAPER_ELIGIBLE` route decision with no live plan, one ordered fake paper lifecycle (`paper_capture_opened`, `paper_settlement_observed`, `paper_capture_closed`), one verified funding settlement verification result, and referenced funding evidence that exists before the verification result.
4. Reconciliation records its result only through `core/accounting/ledger.py` as `ledger_reconciliation_recorded`.
5. Reconciliation result payloads include `event_count` and `last_sequence` describing the ledger history checked before the result was appended.
6. Replay validates the supplied ledger order exactly as given. The first sequence must be 1, every next sequence must increment by exactly 1, and duplicate, missing, non-contiguous, or out-of-order sequence evidence fails closed.
7. Unknown ledger event types and malformed known event payloads fail closed.
8. Reconciliation recomputes the funding settlement verification result with `core/monitoring/funding_settlement.py` through a lazy call boundary and requires the recorded funding verification event to match canonical replay on capture, route, settlement time, verified flag, reasons, checkpoint event sequences, settlement event sequence, and canonical required checkpoint labels.
9. Forged or stale `funding_settlement_verification_recorded` events fail closed when raw checkpoint or settlement evidence does not support them.
10. `is_ledger_explicitly_reconciled(events)` returns true only when the latest event is a successful reconciliation result whose `event_count` and `last_sequence` match the exact prior history and whose prior history replays as reconciled.
11. Any later append after a successful reconciliation makes the full ledger history stale until a new successful reconciliation result is appended.
12. Missing route decisions, missing paper lifecycle evidence, missing funding verification, duplicated decisions, duplicated paper or funding evidence, out-of-order verification evidence, contradictory identity, contradictory settlement time, or contradictory funding settlement verification fail closed as unreconciled.
13. Reconciliation replay ignores prior reconciliation result events after validating their payload shape and remains deterministic from append-only evidence.
14. Reconciliation does not decide route profitability, call route evaluation, call route snapshot assembly, calculate EV, place orders, create `CapturePlan` objects, mutate route eligibility decisions, or enable live trading.

## Route/snapshot alignment

`RouteCandidate` is the authoritative route contract for one RiseX leg and one hedge leg. It owns:

- Capture id and route id.
- RiseX venue and symbol.
- RiseX intended entry side.
- Hedge venue and symbol.
- Hedge intended entry side.
- Target notional in USD.

`RouteCandidate` construction rejects empty or non-string identity fields, invalid or non-opposing entry sides, and non-`Decimal`, non-finite, or non-positive target notionals. A positive target notional below `ProductRules.min_leg_notional_usd` is still a valid candidate input, but it fails closed through the existing minimum-notional route evaluation gate before any economics calculation.

`core/risk/gates.py` owns the centralized route/snapshot alignment gate. Before Entry EV, it verifies:

- RiseX entry and estimated-exit quotes match the route venue and symbol.
- Hedge entry and estimated-exit quotes match the route venue and symbol.
- RiseX and hedge entry sides are opposing market exposure.
- Entry quote sides match the route contract.
- Each estimated-exit side is opposite its corresponding entry side.
- All four quotes use `route.target_notional_usd`.
- All four quotes are sourced from `ValueSource.ESTIMATED_FROM_ORDERBOOK`.
- Entry and estimated-exit quotes paired for roundtrip math use the same venue and symbol.
- `snapshot.risex_funding_settlement_at == snapshot.hedge_funding_settlement_at`, so one eligible route snapshot represents exactly one funding settlement opportunity.

Alignment failures fail closed through centralized `RejectReason.TECHNICALLY_NOT_EXECUTABLE`. They are not spread, price-impact, levels-consumed, safety-margin, or conservative-buffer filters.

## Executable quote invariant

The product minimum notional and full quote executability are separate checks:

- `RouteCandidate.target_notional_usd` must meet `ProductRules.min_leg_notional_usd`.
- Every quote used by `evaluate_route()` must target the route's selected target notional.
- `ExecutableQuote(executable=True)` must have a valid VWAP, positive consumed base quantity, and `notional_filled_usd >= target_notional_usd`.
- A quote that only fills the product minimum is not executable for a larger selected route target.

Poor executable prices, high price impact, and many consumed order-book levels are not independent rejection filters when the full target can be filled. They affect Entry EV through VWAP and roundtrip PnL.

## Venue adapter boundary

Venue adapters are read-only and per-venue. The base adapter protocol exposes only a normalized per-symbol observation primitive:

```python
fetch_observation(symbol: str) -> VenueObservation
```

Adapters must not return or construct cross-venue route snapshots, calculate EV, evaluate routes, send orders, write ledger events, persist data, or assemble RiseX + hedge inputs. Cross-venue route snapshot assembly belongs to `core/pipeline/snapshot.py`.

## No artificial filters

Spread, price impact, basis, slippage, and fees are not independent arbitrary reject filters. They must be represented in executable VWAP, fee, funding, and PnL calculations.

`ProductRules` intentionally has no arbitrary `max_spread_bps`, `max_price_impact_bps`, `max_levels_consumed`, hidden conservative buffer, or safety margin fields. Invariant tests enforce that those fake runtime filters are not introduced.

## Unknown values

Unknown values must not silently become zero. `EstimatedValue` requires `source=UNKNOWN` values to carry no numeric value, and callers must use source-aware handling before a value can participate in economics. Fee defaults must use `USER_CONFIGURED`; last-observed funding estimates must use `ESTIMATED_FROM_LAST_VALUE`.

## Entry and exit economics

Entry EV does not use `expected_basis_change` as a prediction. Before entry, the architecture uses current executable VWAP from order books and simulated immediate roundtrip cost. After entry, basis logic monitors `current_unwind_pnl_usd`, meaning the PnL if both legs were closed using current executable quotes.
