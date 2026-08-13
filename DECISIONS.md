# Decisions

## RX-000

- Adopted a modular-monolith structure with explicit single-owner modules for economics, risk, evaluation, execution, accounting, configuration, and venue normalization.
- Established capture-centric domain language: one `Capture` is one funding settlement opportunity.
- Established allowed route statuses: `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `LIVE_ELIGIBLE`, `REJECTED`.
- Explicitly excluded `CANARY_ELIGIBLE` and separate canary architecture.
- Set product constants: `MIN_LEG_NOTIONAL_USD = 500`, `MIN_NET_PROFIT_USD = 1`, live trading disabled by default, and points/airdrop/leaderboard/unreceived rebates set to zero in base PnL.
- Entry EV uses current executable VWAP and simulated immediate roundtrip cost. It does not use `expected_basis_change` as a future basis prediction.

## RX-001

- Added explicit `CaptureState` lifecycle states for one `Capture`, separate from `RouteStatus` eligibility decisions.
- Made `core/domain/state_machine.py` the single authoritative Capture lifecycle transition table and validator.
- Terminal Capture states are `REJECTED`, `CLOSED`, `FAILED`, and `EMERGENCY_FLATTENED`.
- Any non-terminal Capture may transition to `FAILED`; exposure states may transition to `EMERGENCY_FLATTENED`.
- State transitions are pure domain operations: they do not send orders, call execution modules, connect to venues, or write ledger events.

## RX-002

- Made `ProductRules` the authoritative product-level config contract for minimum notional, minimum net profit, live trading switch, points value, expected airdrop value, leaderboard rewards in base PnL, and unreceived rebates.
- Added `ValueSource` as the explicit source contract for future documented, observed, order-book-estimated, last-value-estimated, user-configured, and unknown values.
- Added `EstimatedValue` as a small source-aware value object. `UNKNOWN` values cannot carry or return a numeric zero fallback.
- Added centralized `RejectReason` values and moved current route/risk gate reasons away from ad hoc strings.
- Enforced the no-artificial-filters rule in code shape and invariant tests: no arbitrary max spread, max price impact, max levels consumed, hidden conservative buffers, or safety margins in `ProductRules`.
- Kept live trading offline: even when the live switch is manually enabled, RX-002 still returns paper eligibility because live gates are not implemented.

## RX-002A

- Added minimal GitHub CI for pushes and pull requests that installs dev dependencies, runs `python -m pytest`, and runs `python -m compileall apps core storage tests`.
- Kept CI infrastructure-only: no linting, formatting, type checking, coverage, secrets, deployment, Docker, exchange connectivity, or live trading.

## RX-003

- Introduced source-aware offline economics contracts for order books, executable VWAP quotes, fee components, fee models, and funding snapshots.
- Made VWAP-from-orderbook the required path for entry and immediate-unwind economics in fake data and `evaluate_route()`.
- Kept unknown values fail-closed: `ValueSource.UNKNOWN` cannot carry or return a numeric value, and fee/funding/EV calculations reject missing economics instead of using zero.
- Limited RX-003 fee sources to documented, observed, and user-configured values; user-configured defaults are valid only with `ValueSource.USER_CONFIGURED`.
- Limited RX-003 funding sources to documented, observed, and last-observed estimates; last-observed fallback is represented only by `ValueSource.ESTIMATED_FROM_LAST_VALUE`.
- Preserved the no-artificial-filters rule: insufficient order-book depth for the configured minimum notional is a technical rejection, while poor executable liquidity changes roundtrip cost and net PnL instead of becoming a standalone reject filter.
- Kept basis logic as current unwind PnL from executable quotes only; RX-003 does not forecast future basis or introduce `expected_basis_change`.
- Kept live trading blocked by `LIVE_TRADING_DISABLED` / `LIVE_GATES_NOT_IMPLEMENTED`; RX-003 does not create orders, real adapters, or live capture plans by default.

## 2026-08-06 — RX-003 FIX

- Date: 2026-08-06
- Decision: `RouteCandidate` is the authoritative route contract for RiseX venue/symbol, hedge venue/symbol, target notional, and intended opposing entry sides; `core/risk/gates.py` owns centralized route/snapshot alignment before Entry EV.
- Reason: RX-003 review found that executable quotes could be mismatched by venue, symbol, side, source, or notional and still enter EV/roundtrip math. Alignment must fail closed before economics calculations.
- Affected files/modules: `core/domain/contracts.py`, `core/risk/gates.py`, `core/pipeline/evaluate.py`, `core/economics/liquidity.py`, `core/economics/fees.py`, `core/economics/funding.py`, `core/economics/errors.py`, `core/venues/base.py`, `apps/research_runner/fake_data.py`, tests, and governance docs.
- Superseded decision: the previous `VenueAdapter.fetch_snapshot() -> VenueSnapshot` boundary is superseded. Adapters are now per-venue and expose only `fetch_order_book(symbol: str) -> OrderBook`; cross-venue route snapshot assembly is reserved for future observation/orchestration contracts.
- Decision: RX-003 `evaluate_route()` does not construct `CapturePlan`, does not invent settlement timestamps, and does not bypass the Capture state machine. Even with `ProductRules(live_trading_enabled=True)`, profitable ENTRY evaluations remain `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED`.
- Reason: RX-003 has no implemented live gates, funding settlement timestamp contract, fresh CapturePlan contract, or live execution boundary.

## 2026-08-06 — RX-003 FIX 2

- Date: 2026-08-06
- Decision: `ExecutableQuote(executable=True)` means the quote fully fills its own `target_notional_usd`; filling only `ProductRules.min_leg_notional_usd` is insufficient for larger route targets.
- Reason: RX-003 FIX review found that an internally inconsistent quote could claim `target_notional_usd=10000` and `executable=True` while only filling `500`, allowing a larger selected route to pass the minimum-notional executability gate.
- Affected files/modules: `core/domain/contracts.py`, `core/economics/liquidity.py`, `core/risk/gates.py`, `tests/unit/test_liquidity.py`, `tests/unit/test_evaluate_route.py`, `ARCHITECTURE.md`, `DECISIONS.md`, and `STATUS.md`.
- Superseded decision: no previous decision is superseded; this tightens the RX-003 executable quote contract.
- Decision: order sides are runtime-validated as exactly `buy` or `sell` in `RouteCandidate`, `ExecutableQuote`, and order-book VWAP selection.
- Reason: invalid side strings must not silently fall through to sell-side bid consumption.

## 2026-08-06 — RX-004

- Date: 2026-08-06
- Decision: Introduced immutable `VenueObservation` as the normalized read-only per-venue/per-symbol input contract containing a timezone-aware observation timestamp, matching `OrderBook`, source-aware expected funding cash flow, funding settlement timestamp, and per-venue source-aware `FeeModel`.
- Reason: RX-004 needs fake-data-compatible observation contracts that preserve unknown economics and timestamps before any route-level evaluation.
- Decision: `core/pipeline/snapshot.py` owns the single authoritative `assemble_route_snapshot()` function. It accepts one `RouteCandidate`, an explicit observation mapping, and an explicit assembly timestamp, then builds the existing `VenueSnapshot` shape for `evaluate_route()`.
- Reason: Cross-venue snapshot assembly must be deterministic and offline while keeping `evaluate_route()` as the only route decision function and keeping liquidity VWAP in `core/economics/liquidity.py`.
- Decision: `VenueAdapter.fetch_order_book(symbol) -> OrderBook` is superseded by `VenueAdapter.fetch_observation(symbol) -> VenueObservation`.
- Reason: Future adapters should remain read-only and per-venue, but RX-004 requires normalized funding, fee, timestamp, and order-book inputs from one venue without allowing adapters to assemble route snapshots or calculate EV.
- Affected files/modules: `core/domain/contracts.py`, `core/domain/__init__.py`, `core/pipeline/snapshot.py`, `core/venues/base.py`, `apps/research_runner/fake_data.py`, tests, and governance docs.
- Non-decisions: RX-004 does not implement Broad Scan, Focused Refresh, Watchlist, real adapters, paper execution, persistence, dashboard, order placement, live trading, canary architecture, hold-next-cycle logic, or artificial filters.

## 2026-08-07 — RX-005

- Date: 2026-08-07
- Decision: `core/pipeline/offline_scan.py` owns deterministic offline iteration over multiple `RouteCandidate` values and normalized `VenueObservation` mappings.
- Reason: RX-005 needs a repeatable fake orchestration layer while preserving `assemble_route_snapshot()` as the only snapshot assembly path and `evaluate_route(route, snapshot, mode)` as the only route decision path.
- Decision: For each candidate, offline orchestration first calls `assemble_route_snapshot()`. Only successfully assembled snapshots are passed to `evaluate_route()`.
- Reason: The orchestration layer must not calculate VWAP, EV, fees, funding, risk gates, or route eligibility itself.
- Decision: Snapshot assembly failures caused by missing or contradictory normalized observations produce a deterministic per-route `DecisionResult` with `RouteStatus.REJECTED` and `RejectReason.REQUIRED_LIVE_DATA_MISSING` before evaluation.
- Reason: Missing required observations must fail closed without creating trades, orders, ledger records, or `CapturePlan` objects.
- Affected files/modules: `core/pipeline/offline_scan.py`, `apps/research_runner/fake_data.py`, `apps/cli/main.py`, tests, and governance docs.
- Non-decisions: RX-005 does not implement Broad Scan, Focused Refresh, Watchlist, real adapters, network/API/authentication, paper execution lifecycle, persistent ledger storage, dashboard code, order placement, live trading, canary architecture, hold-next-cycle logic, ranking, artificial filters, or `CapturePlan` creation.

## 2026-08-07 — RX-006

- Date: 2026-08-07
- Decision: `core/pipeline/scan_refresh.py` owns deterministic fake Broad Scan and Focused Refresh orchestration over the RX-005 offline candidate path.
- Reason: RX-006 needs to model the two-stage workflow without introducing a second route decision function, second snapshot assembly function, second EV path, real adapters, paper execution, or live trading.
- Decision: Broad Scan calls `evaluate_offline_candidates()` with `EvaluationMode.DISCOVERY` and returns a `BroadScanResult` containing decisions plus the original `RouteCandidate` contracts as refresh candidates.
- Reason: The handoff should be in-memory, deterministic, and route-contract preserving, with no orchestration-side ranking, acceptance, eligibility, economics, or risk rules.
- Decision: Focused Refresh accepts only a `BroadScanResult`, refreshed normalized observations, and a refreshed timestamp, then calls `evaluate_offline_candidates()` with `EvaluationMode.ENTRY`.
- Reason: Focused Refresh must consume only Broad Scan handoff candidates while still flowing through observation lookup, `assemble_route_snapshot()`, and `evaluate_route(route, snapshot, mode)`.
- Affected files/modules: `core/pipeline/scan_refresh.py`, `apps/research_runner/fake_data.py`, `apps/cli/main.py`, tests, and governance docs.
- Non-decisions: RX-006 does not implement real RiseX or Hyperliquid adapters, network calls, API clients, authentication, order placement, paper execution lifecycle, persistent ledger storage, migrations, dashboard code, live trading, live `CapturePlan` creation, canary architecture, hold-next-cycle logic, ranking, artificial filters, or production credentials.

## 2026-08-07 — RX-007

- Date: 2026-08-07
- Decision: `apps/paper_runner/lifecycle.py` owns the deterministic fake paper lifecycle downstream of existing `DecisionResult` values.
- Reason: Paper execution must not become a second route decision path, second EV path, second snapshot assembly path, or live execution path.
- Decision: Fake paper capture execution starts only for `PAPER_ELIGIBLE` input decisions in `EvaluationMode.ENTRY`. `PAPER_ELIGIBLE` discovery decisions, `REJECTED`, `RESEARCH_ONLY`, and `LIVE_ELIGIBLE` decisions are recorded as paper rejections and do not create a `Capture`.
- Reason: Broad Scan discovery decisions are research-stage signals only. Route eligibility decisions must remain immutable inputs to the paper lifecycle, and live eligibility must not be treated as permission to paper-execute or live-execute.
- Decision: A started fake paper lifecycle creates one `Capture` for one funding settlement opportunity and advances it through `core/domain/state_machine.py`.
- Reason: Capture lifecycle behavior must remain centralized and separate from route status.
- Decision: `core/accounting/ledger.py` owns append-only paper event contracts, event append helpers, immutable payload freezing, and deterministic replay of paper lifecycle events into final `Capture` states.
- Reason: Ledger events are the source of fake paper history and must stay behind the accounting boundary.
- Decision: `storage/sqlite/ledger.py` is the only persistence scaffolding introduced by RX-007.
- Reason: RX-007 needs deterministic append-only persistence tests without broad storage design, migrations, real adapters, exchange connectivity, secrets, or live trading.
- Affected files/modules: `apps/paper_runner/lifecycle.py`, `core/accounting/ledger.py`, `storage/sqlite/ledger.py`, tests, and governance docs.
- Non-decisions: RX-007 does not implement real RiseX or Hyperliquid adapters, network calls, API clients, authentication, order placement, live runner behavior, live trading, live `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, a second route model, a second EV path, a second route decision function, or a second snapshot assembly function.

## 2026-08-07 — RX-008

- Date: 2026-08-07
- Decision: `core/monitoring/funding_settlement.py` owns deterministic offline funding settlement verification.
- Reason: Settlement-time evidence must be replayable from append-only history without becoming a route decision path, EV path, snapshot assembly path, execution path, or live trading gate.
- Decision: Required fake pre-settlement checkpoints are T-20 minutes, T-60 seconds, T-10 seconds, and T-5 seconds before the funding settlement timestamp.
- Reason: Future live work must be able to prove settlement-time capture inputs from explicit checkpoint evidence rather than trusting a single late observation.
- Decision: `core/accounting/ledger.py` owns append-only event helpers for funding checkpoint evidence, observed settlement evidence, and funding settlement verification results.
- Reason: Evidence and verification history must remain immutable and replayable through the accounting boundary.
- Decision: Funding settlement verification fails closed when required checkpoints are missing, observed settlement evidence is missing, funding/notional evidence is unknown, capture identity or settlement time is inconsistent, checkpoint timing is inconsistent, or fake expected funding/notional inputs do not match fake observed settlement records.
- Reason: Unknown or contradictory evidence must never silently become zero or success.
- Decision: RX-008 verification results do not mutate route eligibility decisions and do not satisfy live eligibility by themselves.
- Reason: Live trading still requires future live gates, ledger reconciliation, fresh plan handling, execution capability, and explicit safe live path implementation.
- Affected files/modules: `core/accounting/ledger.py`, `core/monitoring/funding_settlement.py`, tests, and governance docs.
- Non-decisions: RX-008 does not implement real RiseX or Hyperliquid adapters, network calls, API clients, authentication, order placement, live runner behavior, live trading, live `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, a second route model, a second EV path, a second route decision function, or a second snapshot assembly function.

## 2026-08-07 — RX-008 FIX

- Date: 2026-08-07
- Decision: Actual settlement funding and actual settlement notional evidence must use `ValueSource.OBSERVED` before funding settlement verification can succeed.
- Reason: Actual settlement evidence is a proof input. User-configured, documented, estimated, unknown, missing, malformed, or non-positive notional actuals are not proof that the settlement mechanism behaved as expected.
- Decision: Pre-settlement expected funding checkpoints remain source-aware expected inputs and are not restricted to `ValueSource.OBSERVED`.
- Reason: Checkpoints are expected/estimated pre-settlement inputs, while actual settlement evidence is the settlement-time proof input.
- Affected files/modules: `core/monitoring/funding_settlement.py`, replay tests, and governance docs.
- Non-decisions: RX-008 FIX does not implement real adapters, network calls, orders, live runner behavior, live trading, `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, route eligibility mutation, a second route model, a second EV path, a second route decision function, or a second snapshot assembly function.

## 2026-08-07 — RX-009

- Date: 2026-08-07
- Decision: `core/accounting/reconciliation.py` owns deterministic offline ledger reconciliation for one Capture ledger history.
- Reason: Future live Capture paths need an explicit, replayable proof that append-only route decision, fake paper lifecycle, funding evidence, and funding settlement verification history are internally consistent before live gates can proceed.
- Decision: `core/accounting/ledger.py` owns the `ledger_reconciliation_recorded` event type and append helper for reconciliation results.
- Reason: Reconciliation results are ledger history and must be recorded through the accounting boundary without update/delete APIs.
- Decision: Missing, duplicated, out-of-order, or contradictory ledger evidence fails closed as unreconciled with explicit `LedgerReconciliationReason` values.
- Reason: A missing or ambiguous ledger fact must never become implicit success for a future live gate.
- Decision: `core/risk/gates.py` now has an explicit ledger reconciliation gate. If live trading is manually enabled but reconciliation is not exactly `True`, the route decision remains `PAPER_ELIGIBLE` with `RejectReason.LEDGER_NOT_RECONCILED`; if reconciliation is `True`, live still remains blocked with `RejectReason.LIVE_GATES_NOT_IMPLEMENTED`.
- Reason: RX-009 can define the future gate contract without enabling live trading or creating live plans.
- Affected files/modules: `core/accounting/ledger.py`, `core/accounting/reconciliation.py`, `core/risk/gates.py`, `core/pipeline/evaluate.py`, tests, and governance docs.
- Non-decisions: RX-009 does not implement real RiseX or Hyperliquid adapters, network calls, API clients, authentication, order placement, live runner behavior, live trading, live `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, route profitability recalculation, route eligibility mutation, a second route model, a second EV path, a second route decision function, or a second snapshot assembly function.

## 2026-08-07 — RX-009 FIX

- Date: 2026-08-07
- Decision: `ledger_reconciliation_recorded` payloads include `event_count` and `last_sequence` for the checked ledger history before the reconciliation event is appended.
- Reason: A future live gate must know whether the latest reconciliation result covers the exact current append-only history, not just a historical prefix.
- Decision: `core/accounting/reconciliation.py` validates ledger sequence order exactly as supplied before replaying business evidence.
- Reason: Sorting input events before validation can hide out-of-order, duplicated, or missing sequence evidence.
- Decision: `is_ledger_explicitly_reconciled(events)` is the source of the future live gate boolean. It returns true only when the latest event is a successful reconciliation result that covers the exact prior history and that prior history replays as reconciled.
- Reason: Raw hand-written booleans are not sufficient safety evidence for live gating.
- Decision: Unknown ledger event types and malformed known event payloads fail closed.
- Reason: Ledger replay must not silently skip unrecognized or malformed append-only evidence.
- Affected files/modules: `core/accounting/ledger.py`, `core/accounting/reconciliation.py`, `core/accounting/__init__.py`, `core/risk/gates.py`, `core/pipeline/evaluate.py`, replay tests, and governance docs.
- Non-decisions: RX-009 FIX does not implement real adapters, network calls, orders, live runner behavior, live trading, `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, route profitability recalculation, route eligibility mutation, a second route model, a second EV path, a second route decision function, or a second snapshot assembly function.

## 2026-08-07 — RX-009 FIX 2

- Date: 2026-08-07
- Decision: Ledger reconciliation recomputes every recorded funding settlement verification result with `core/monitoring/funding_settlement.py`.
- Reason: A forged or accidentally inconsistent `funding_settlement_verification_recorded` event must not make ledger reconciliation pass when raw checkpoint or settlement evidence contradicts the recorded result.
- Decision: The recorded funding verification event must match canonical replay on capture id, route id, settlement time, verified flag, reasons, checkpoint event sequences, settlement event sequence, and canonical required checkpoint labels.
- Reason: Future live gating must be based on append-only evidence coverage, not on manually supplied or stale success claims.
- Affected files/modules: `core/accounting/reconciliation.py`, replay tests, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `DECISIONS.md`, and `STATUS.md`.
- Non-decisions: RX-009 FIX 2 does not implement real adapters, network calls, orders, live runner behavior, live trading, `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, route profitability recalculation, route eligibility mutation, a second route model, a second EV path, a second route decision function, or a second snapshot assembly function.

## 2026-08-07 — RX-009 FIX 3

- Date: 2026-08-07
- Decision: Ledger reconciliation keeps the funding verifier dependency lazy inside the canonical replay comparison helper.
- Reason: `core.monitoring.funding_settlement` imports `core.accounting.ledger`, and `core/accounting/__init__.py` re-exports reconciliation; a top-level reconciliation import of monitoring creates a circular import risk in fresh Python processes.
- Decision: Direct import regression coverage now checks both module imports and function imports for `core.monitoring.funding_settlement` and `core.accounting.reconciliation` in subprocesses.
- Reason: Pytest's normal import order can mask package-level circular imports.
- Affected files/modules: `core/accounting/reconciliation.py`, `tests/replay/test_ledger_reconciliation.py`, `ARCHITECTURE.md`, `DECISIONS.md`, and `STATUS.md`.
- Non-decisions: RX-009 FIX 3 does not duplicate funding verifier logic, remove the canonical verifier replay comparison, implement real adapters, network calls, orders, live runner behavior, live trading, `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, route profitability recalculation, route eligibility mutation, a second route model, a second EV path, a second route decision function, or a second snapshot assembly function.

## 2026-08-07 — RX-010

- Date: 2026-08-07
- Decision: Added `CapturePlanFreshnessEvidence` as deterministic fake, non-executable plan freshness evidence for exactly one `capture_id`, one `route_id`, and one funding settlement timestamp.
- Reason: Future live Capture paths need an explicit fail-closed plan freshness contract without turning RX-010 into live execution architecture or executable order planning.
- Decision: `core/risk/gates.py` owns `check_capture_plan_freshness_gate()`. Missing, stale, duplicated, cross-capture, cross-route, cross-settlement, malformed, future-dated, or unknown-source fake plan evidence fails closed with centralized `RejectReason.CAPTURE_PLAN_NOT_FRESH`.
- Reason: Fresh plan gating is a risk/live boundary concern and must not mutate route profitability decisions or duplicate the route decision, EV, ledger reconciliation, or funding settlement verification paths.
- Decision: `check_live_capture_allowed()` now orders future live blockers as live trading switch, explicit ledger reconciliation, fresh CapturePlan evidence, and then `LIVE_GATES_NOT_IMPLEMENTED`.
- Reason: Live trading remains disabled by default, reconciliation remains required first, and a fresh plan alone must never permit live trading.
- Affected files/modules: `core/domain/contracts.py`, `core/domain/__init__.py`, `core/risk/gates.py`, `core/pipeline/evaluate.py`, `tests/unit/test_risk_gates.py`, `tests/replay/test_capture_plan_freshness.py`, `tests/replay/test_ledger_reconciliation.py`, and governance docs.
- Superseded decisions: RX-009's final live-gate stopping point after successful ledger reconciliation is narrowed. Successful reconciliation without fresh CapturePlan evidence now stops at `CAPTURE_PLAN_NOT_FRESH`; successful reconciliation plus exact fresh fake evidence still stops at `LIVE_GATES_NOT_IMPLEMENTED`.
- Non-decisions: RX-010 does not implement real RiseX or Hyperliquid adapters, network calls, API clients, authentication, order placement, live runner behavior, live trading, executable live order plans, live `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, route profitability recalculation, route eligibility mutation, a second route model, a second EV path, a second route decision function, or a second snapshot assembly function.

## 2026-08-08 — RX-011

- Date: 2026-08-08
- Decision: Added `ExecutionCapabilityEvidence` as deterministic fake, non-executable evidence that references the current four `ExecutableQuote` values for one `capture_id`, one `route_id`, and one funding settlement timestamp.
- Reason: Future live Capture paths need explicit proof that the selected full route target can still execute on RiseX entry, hedge entry, RiseX unwind, and hedge unwind sides without creating order plans or recalculating liquidity outside the existing quote contracts.
- Decision: `core/risk/gates.py` owns `check_execution_capability_gate()`. Missing, stale, future-dated, cross-capture, cross-route, cross-settlement, malformed, non-orderbook-source, missing-side, wrong-side, wrong-target-notional, partial-fill, or contradictory fake execution evidence fails closed through existing centralized reject reasons.
- Reason: Execution capability is a live risk gate and must remain downstream of route decisions, ledger reconciliation, funding settlement verification, and CapturePlan freshness while reusing `quote_is_executable_for_notional()` instead of duplicating VWAP logic.
- Decision: `check_live_capture_allowed()` now orders future live blockers as live trading switch, explicit ledger reconciliation, fresh CapturePlan evidence, fresh execution-capability evidence, and then `LIVE_GATES_NOT_IMPLEMENTED`.
- Reason: Fresh execution capability alone must never bypass live disabled, unreconciled ledger history, missing/stale CapturePlan evidence, or the still-unimplemented live path.
- Affected files/modules: `core/domain/contracts.py`, `core/domain/__init__.py`, `core/risk/gates.py`, `core/pipeline/evaluate.py`, tests, and governance docs.
- Superseded decisions: RX-010's final live-gate stopping point after successful ledger reconciliation plus fresh CapturePlan evidence is narrowed. Successful reconciliation plus fresh CapturePlan evidence but without fresh execution-capability evidence now stops at `REQUIRED_LIVE_DATA_MISSING`; successful reconciliation plus exact fresh CapturePlan and execution-capability evidence still stops at `LIVE_GATES_NOT_IMPLEMENTED`.
- Non-decisions: RX-011 does not implement real RiseX or Hyperliquid adapters, network calls, API clients, authentication, order placement, live runner behavior, live trading, executable live order plans, live `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, route profitability recalculation, route eligibility mutation, a second route model, a second EV path, a second route decision function, a second snapshot assembly function, or a second VWAP/liquidity path.

## 2026-08-10 - RX-Q001

- Date: 2026-08-10
- Decision: Repository governance now requires `NEXT_TASK.md` to contain exactly one complete next task and pass `python scripts/validate_next_task.py`.
- Reason: Future Codex sessions need a fail-closed handoff contract instead of relying on chat memory or duplicate task definitions.
- Decision: Added explicit Parent/Worker/Reviewer workflow docs and templates for task prompts, worker checkpoints, final reports, PRs, and review checklists.
- Reason: Non-trivial tasks need supervised worker checkpoints, Parent-owned final diff review, and reviewer-only acceptance without mixing implementation completion with accepted baseline state.
- Decision: CI runs the `NEXT_TASK.md` validator before pytest and includes `scripts` in compileall.
- Reason: Governance scripts must stay importable and next-task drift must fail in repository-level validation.
- Affected files/modules: `AGENTS.md`, `docs/WORKFLOW.md`, `docs/templates/`, `scripts/validate_next_task.py`, invariant tests, `.github/`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Non-decisions: RX-Q001 does not change product architecture, route evaluation, economics, risk gates, domain trading contracts, ledger behavior, adapters, order flow, live runner behavior, route statuses, reject reasons, canary architecture, or live trading.

## 2026-08-11 - RX-012

- Date: 2026-08-11
- Decision: Added `LiveGateEvidenceBundle` as deterministic fake, non-executable aggregate evidence for exactly one `capture_id`, one `route_id`, and one funding settlement timestamp.
- Reason: Future live gate work needs one explicit bundle boundary that can carry already-derived funding verification, helper-derived ledger reconciliation, CapturePlan freshness, and execution-capability evidence without creating a second replay or decision path.
- Decision: `core/risk/gates.py` owns `check_live_gate_evidence_bundle()`. The bundle gate validates capture/route/settlement identity, explicit ledger reconciliation, verified funding settlement, fresh CapturePlan evidence, and execution capability by reusing existing gates and reject reasons.
- Reason: Live-gate bundle behavior is a risk boundary and must fail closed without recalculating EV, fees, funding, VWAP, basis, or profitability.
- Decision: `evaluate_route()` accepts an optional fake `live_gate_evidence_bundle` and only passes it to `check_live_capture_allowed()` after the existing route/economics checks.
- Reason: `evaluate_route(route, snapshot, mode)` remains the single decision path while still allowing future live-gate evidence to be checked offline.
- Affected files/modules: `core/domain/contracts.py`, `core/domain/__init__.py`, `core/risk/gates.py`, `core/pipeline/evaluate.py`, tests, and governance docs.
- Superseded decisions: RX-011's unbundled live-gate input path remains backward compatible for existing offline tests, but RX-012 adds the preferred aggregate bundle path for future live-gate work.
- Non-decisions: RX-012 does not implement real RiseX or Hyperliquid adapters, network calls, API clients, authentication, order placement, live runner behavior, live trading, executable live order plans, live `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, route profitability recalculation, route eligibility mutation, a second route model, a second EV path, a second route decision function, a second snapshot assembly function, a second VWAP/liquidity path, ledger writes, or live execution.

## 2026-08-11 - RX-Q002

- Date: 2026-08-11
- Decision: Repository governance now requires a supervised worker/subagent for non-trivial architecture-sensitive tasks, including live-gate, accounting, reconciliation, execution-boundary, ledger, safety-critical, broad contract, owner-boundary, and repository-governance tasks.
- Reason: Architecture-sensitive work needs an explicit second-pass design checkpoint while preserving Parent Codex ownership of scope, steering, final diff review, validation, commit, push, and final reporting.
- Decision: Required workers must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing. Workers must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT when they continue beyond design support.
- Reason: Checkpoints must gate the work during the task, not only appear as final-report evidence.
- Decision: If a required worker is unavailable, Parent Codex must stop before edits. If a worker skips checkpoints, continues after being stopped, or drifts into forbidden scope, Parent Codex must stop or steer before accepting worker output.
- Reason: Governance failures should fail closed before they can enter product or repository history.
- Affected files/modules: `AGENTS.md`, `docs/WORKFLOW.md`, `docs/templates/WORKER_CHECKPOINT_TEMPLATE.md`, `docs/templates/RX_TASK_TEMPLATE.md`, `docs/templates/REVIEW_CHECKLIST.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Non-decisions: RX-Q002 does not change product architecture, route evaluation, economics, risk gates, domain trading contracts, ledger behavior, adapters, order flow, live runner behavior, route statuses, reject reasons, canary architecture, or live trading.

## 2026-08-11 - RX-013

- Date: 2026-08-11
- Decision: Added `live_gate_evidence_bundle_recorded` as an append-only accounting event for fake live-gate evidence bundle check outcomes.
- Reason: Future live-gate work needs deterministic ledger evidence that a fake RX-012 bundle check was recorded against explicit route-decision, funding-verification, and ledger-reconciliation history without relying on a hand-written success flag.
- Decision: `core/accounting/ledger.py` owns `append_live_gate_evidence_bundle_event()`, including deterministic serialization of the existing `RouteCandidate`, `LiveGateEvidenceBundle`, CapturePlan freshness evidence, execution-capability evidence, executable quotes, referenced ledger sequences, and the already-computed bundle gate result.
- Reason: Ledger writes must stay behind the accounting boundary and must not recalculate risk, economics, funding, VWAP, basis, or profitability.
- Decision: `core/accounting/reconciliation.py` owns `replay_live_gate_evidence_bundle_recording()`, which validates exactly one current bundle record, prior reconciliation freshness, referenced route/funding/reconciliation events, plan reconciliation references, and recorded result consistency by rerunning `check_live_gate_evidence_bundle()`.
- Reason: Bundle recording replay must fail closed on missing, duplicated, stale, malformed, or contradictory evidence while reusing the existing RX-012 gate instead of creating a second live-gate decision path.
- Decision: Appending a live-gate evidence bundle record after successful ledger reconciliation makes `is_ledger_explicitly_reconciled(ledger.records())` false until a later reconciliation event covers the new append.
- Reason: The append-only ledger must prove the exact current history; successful prior reconciliation cannot silently cover later bundle evidence.
- Affected files/modules: `core/accounting/ledger.py`, `core/accounting/reconciliation.py`, `core/accounting/__init__.py`, replay tests, invariant tests, and governance docs.
- Superseded decisions: no previous decision is superseded; RX-013 records and replays the RX-012 fake bundle gate result without changing the gate itself.
- Non-decisions: RX-013 does not implement real RiseX or Hyperliquid adapters, network calls, API clients, authentication, order placement, live runner behavior, live trading, executable live order plans, live `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, route profitability recalculation, route eligibility mutation, a second route model, a second EV path, a second route decision function, a second snapshot assembly function, a second VWAP/liquidity path, or live execution.

## 2026-08-11 - RX-013 FIX

- Date: 2026-08-11
- Decision: Ledger reconciliation now requires any current `live_gate_evidence_bundle_recorded` event to replay successfully through `replay_live_gate_evidence_bundle_recording()` before reconciliation can pass.
- Reason: Payload shape validation alone can allow a syntactically valid but semantically contradictory bundle record to be covered by a later successful reconciliation, weakening the append-only evidence chain.
- Decision: Valid live-gate bundle record event sequences are included in `LedgerReconciliationResult.checked_event_sequences`.
- Reason: A reconciliation result must identify that it covered the bundle evidence append, not only the earlier route, paper lifecycle, and funding evidence.
- Affected files/modules: `core/accounting/reconciliation.py`, `tests/replay/test_ledger_reconciliation.py`, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `DECISIONS.md`, `STATUS.md`, and `NEXT_TASK.md`.
- Superseded decisions: RX-013's bundle event shape validation is tightened; semantic bundle replay is now part of ledger reconciliation when bundle records are present.
- Non-decisions: RX-013 FIX does not change route decisions, economics, risk gate behavior, route statuses, `RejectReason` values, adapters, orders, live runner behavior, live trading, executable live order plans, live `CapturePlan` creation, canary architecture, hold-next-cycle logic, artificial filters, or RX-014 implementation.

## 2026-08-11 - RX-018

- Date: 2026-08-11
- Decision: `core/risk/gates.py` route/snapshot alignment now requires `snapshot.risex_funding_settlement_at == snapshot.hedge_funding_settlement_at` before a route can pass into executability, EV, and paper eligibility.
- Reason: One route snapshot must represent exactly one funding settlement opportunity. If the RiseX and hedge legs settle at different timestamps, the route is not one aligned capture opportunity and must fail closed before `PAPER_ELIGIBLE`.
- Decision: Mismatched settlement timestamps fail through existing `RejectReason.TECHNICALLY_NOT_EXECUTABLE`.
- Reason: The failure is a route/snapshot alignment problem like mismatched venue, symbol, side, quote source, or quote notional. It is not a profitability calculation and does not require a new route status or reject reason.
- Decision: `assemble_route_snapshot()` continues to preserve per-leg settlement timestamps without deciding eligibility.
- Reason: Snapshot assembly remains the single normalized data assembly path, while `evaluate_route()` remains the single decision path through the existing risk gate.
- Affected files/modules: `core/risk/gates.py`, focused unit tests, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no previous decision is superseded; RX-018 tightens the existing route/snapshot alignment contract.
- Non-decisions: RX-018 does not recalculate EV, fees, funding, VWAP, basis, or profitability; it does not add spread, impact, slippage, max-level, buffer, or safety-margin filters; it does not add adapters, network calls, orders, live runner behavior, live trading, executable `CapturePlan`, route statuses, reject reasons, second decision paths, or second snapshot assembly paths.

## 2026-08-11 - RX-Q004

- Date: 2026-08-11
- Decision: Consolidated repository roadmap and rulebook language so `IMPLEMENTATION_PLAN.md`, `PRODUCT_INVARIANTS.md`, `ARCHITECTURE.md`, `STATUS.md`, `AGENTS.md`, `README.md`, and `NEXT_TASK.md` agree on the post-safety-hardening path.
- Reason: The accepted RX-008 through RX-016 offline safety work needed to be classified explicitly as fail-closed safety hardening, not as a product strategy change or a standing reason to keep adding offline scaffolding.
- Decision: Future roadmap stages are gated handoffs. A later stage can be implemented only when it is the exact current task in `NEXT_TASK.md` and remains inside that task's allowed scope.
- Reason: The repository needs to return toward the intended product path after RX-020 without drifting into unnecessary abstractions, speculative live architecture, artificial filters, second owner paths, or premature live trading.
- Decision: RX-020 remains the immediate next implementation task after RX-Q004.
- Reason: Governance consolidation must not create a second roadmap that conflicts with `NEXT_TASK.md` or implement RX-020 early.
- Affected files/modules: `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no architecture or product decisions are superseded; RX-Q004 clarifies repository-governance and roadmap policy.
- Non-decisions: RX-Q004 does not change product behavior, code contracts, route statuses, reject reasons, economics, risk gates, route evaluation, snapshot assembly, ledger behavior, adapters, network calls, orders, live runner behavior, live trading, executable `CapturePlan`, canary architecture, hold-next-cycle logic, artificial filters, second decision paths, second snapshot paths, second VWAP paths, second ledger-write paths, or second live execution paths.

## 2026-08-11 - RX-020

- Date: 2026-08-11
- Decision: `RouteCandidate` construction now rejects empty or non-string capture id, route id, venues, and symbols; invalid or non-opposing entry sides; and target notionals that are missing, non-`Decimal`, non-finite, zero, or negative.
- Reason: Malformed route identity or selected-notional values must fail before they can enter the single snapshot assembly path, route evaluation path, fake paper lifecycle, ledger evidence, or future live-gate evidence.
- Decision: Positive `Decimal` target notionals below `ProductRules.min_leg_notional_usd` remain constructible route candidates and continue to fail through the existing minimum-notional route evaluation gate.
- Reason: Below-minimum notional is a product rule violation already owned by the centralized risk gate, not malformed domain identity.
- Affected files/modules: `core/domain/contracts.py`, focused unit tests, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no previous decision is superseded; RX-020 tightens the existing authoritative `RouteCandidate` contract.
- Non-decisions: RX-020 does not add route statuses, reject reasons, artificial filters, EV/fee/funding/VWAP/basis changes, snapshot or decision paths, ledger-write or replay paths, adapters, network calls, orders, live runner behavior, live trading, executable `CapturePlan`, canary architecture, hold-next-cycle logic, paper-result attribution, execution planning, or later roadmap stages.

## 2026-08-11 - RX-021

- Date: 2026-08-11
- Decision: Added app-local `PaperResultExplanation` to the fake paper lifecycle result contract.
- Reason: Paper outcomes need deterministic inspection of why fake paper started or did not start without making callers infer behavior from raw lifecycle events alone.
- Decision: Paper start attribution reuses the existing fake paper predicate: only ENTRY `PAPER_ELIGIBLE` decisions start. Non-started paper results record deterministic mode/status blockers and preserve centralized `RejectReason` values from the input decision without adding new route statuses or reject reasons.
- Reason: RX-021 must explain paper behavior without changing route eligibility or creating a second decision path.
- Decision: Paper PnL explanation copies existing `DecisionResult` economics when present: expected funding, total fees, simulated roundtrip cost, and net profit. Missing economics remain `None`.
- Reason: Paper attribution is downstream of `evaluate_route()` and must not recalculate profitability or silently turn unknown values into zero.
- Decision: Existing `paper_capture_opened` and `paper_rejection_recorded` ledger events may carry optional `paper_result_explanation` payloads; reconciliation shape-validates them when present, semantically checks them against authoritative route-decision or rejection event payloads where ledger evidence exists, fails closed on contradictory well-formed explanation fields, and leaves paper lifecycle replay state-only.
- Reason: Paper outcomes should be inspectable from append-only history and SQLite round-trip without creating a new event type, ledger-write path, profitability replay path, or paper lifecycle replay behavior change.
- Affected files/modules: `apps/paper_runner/lifecycle.py`, `apps/paper_runner/__init__.py`, `core/accounting/ledger.py`, `core/accounting/reconciliation.py`, focused tests, and governance docs.
- Superseded decisions: no previous decision is superseded; RX-021 extends fake paper result reporting downstream of RX-007.
- Non-decisions: RX-021 does not recalculate EV, fees, funding, VWAP/liquidity, basis, spread, slippage, price impact, or profitability; does not mutate route eligibility; does not add route statuses or `RejectReason` values; does not add adapters, network calls, orders, live runner behavior, live trading, executable `CapturePlan`, execution planning, canary architecture, hold-next-cycle logic, or a second decision, snapshot, ledger-write, replay, economics, or live execution path.

## 2026-08-12 - RX-022

- Date: 2026-08-12
- Decision: Added `RiseXObservationAdapter` in `core/venues/risex.py` as a read-only public market-data adapter implementing the existing `VenueAdapter.fetch_observation(symbol) -> VenueObservation` boundary.
- Reason: RX-022 needs a real RiseX venue-data ingestion boundary while preserving per-venue normalization and keeping cross-venue snapshot assembly in `core/pipeline/snapshot.py`.
- Decision: The adapter fetches only public `GET /v1/markets` and `GET /v1/orderbook` data, maps the requested symbol to one RiseX market id, normalizes orderbook levels into `OrderBook`/`OrderBookLevel`, and converts `next_funding_time` from Unix nanoseconds into a timezone-aware funding settlement timestamp.
- Reason: `VenueObservation` requires normalized per-venue orderbook and settlement timestamp inputs before the existing snapshot assembly and route decision paths can consume real data in later tasks.
- Decision: RiseX expected funding cash flow and fee cash flow remain `ValueSource.UNKNOWN` inside the adapter.
- Reason: RISEx public market data exposes funding rates and fee bps/account-tier schedules, while the existing `VenueObservation` economics contract requires USD cash values and `fetch_observation(symbol)` has no selected route notional or account fee tier. Converting rates or bps to USD inside the adapter would duplicate economics and silently invent missing inputs.
- Decision: Adapter tests use injected deterministic JSON responses and an injected clock; live HTTP availability is not required for test success.
- Reason: The adapter may have a production read-only HTTP fallback, but repository tests must remain deterministic and fail closed over malformed or missing market-data shapes.
- Affected files/modules: `core/venues/risex.py`, `core/venues/__init__.py`, focused unit tests, invariant tests, and governance docs.
- Superseded decisions: RX-004's adapter boundary remains unchanged; RX-022 fills it for RiseX only.
- Non-decisions: RX-022 does not implement a Hyperliquid adapter, route snapshot assembly, route evaluation, route ranking, route eligibility mutation, EV/fee/funding/VWAP/basis calculations, ledger writes, replay paths, private/account/auth endpoints, credentials, orders, paper lifecycle, live runner behavior, live trading, executable `CapturePlan`, execution planning, canary architecture, hold-next-cycle logic, artificial filters, or a second decision, snapshot, ledger-write, economics, or live execution path.

## 2026-08-12 - RX-023

- Date: 2026-08-12
- Decision: Added `HyperliquidObservationAdapter` in `core/venues/hyperliquid.py` as a read-only public market-data adapter implementing the existing `VenueAdapter.fetch_observation(symbol) -> VenueObservation` boundary.
- Reason: RX-023 needs the hedge venue data-ingestion boundary while preserving per-venue normalization and keeping cross-venue snapshot assembly in `core/pipeline/snapshot.py`.
- Decision: The adapter posts only public Hyperliquid `/info` requests for `metaAndAssetCtxs`, `l2Book`, and `predictedFundings`, maps the requested symbol to exactly one Hyperliquid coin, normalizes orderbook levels into `OrderBook`/`OrderBookLevel`, converts `l2Book.time` into `observed_at`, and converts `HlPerp.nextFundingTime` into the funding settlement timestamp.
- Reason: `VenueObservation` requires normalized per-venue orderbook, observation timestamp, and settlement timestamp inputs before the existing snapshot assembly and route decision paths can consume real data in later tasks.
- Decision: Hyperliquid expected funding cash flow and fee cash flow remain `ValueSource.UNKNOWN` inside the adapter.
- Reason: Hyperliquid public market data exposes funding rates and fee schedules, while the existing `VenueObservation` economics contract requires USD cash values and `fetch_observation(symbol)` has no selected route notional, side, or account fee tier. Converting rates or schedule terms to USD inside the adapter would duplicate economics and silently invent missing inputs.
- Decision: Adapter tests use injected deterministic `/info` responses; live HTTP availability is not required for test success.
- Reason: The adapter may have a production read-only HTTP fallback, but repository tests must remain deterministic and fail closed over malformed or missing market-data shapes.
- Affected files/modules: `core/venues/hyperliquid.py`, `core/venues/__init__.py`, focused unit tests, invariant tests, and governance docs.
- Superseded decisions: RX-004's adapter boundary remains unchanged; RX-023 fills it for Hyperliquid only.
- Non-decisions: RX-023 does not implement real market-data route snapshot assembly, route evaluation, route ranking, route eligibility mutation, EV/fee/funding/VWAP/basis calculations, ledger writes, replay paths, private/account/auth endpoints, credentials, orders, paper lifecycle, live runner behavior, live trading, executable `CapturePlan`, execution planning, canary architecture, hold-next-cycle logic, artificial filters, or a second decision, snapshot, ledger-write, economics, or live execution path.

## 2026-08-12 - RX-024

- Date: 2026-08-12
- Decision: Added `assemble_route_snapshot_from_adapters()` in `core/pipeline/snapshot.py` as the narrow real market-data route snapshot handoff.
- Reason: RX-024 needs one explicit bridge from the existing read-only RiseX and Hyperliquid `VenueAdapter.fetch_observation(symbol)` boundary into the existing `assemble_route_snapshot()` path for one `RouteCandidate`, without introducing a runner or second snapshot assembly owner.
- Decision: The handoff fetches exactly `route.risex_symbol` from the RiseX adapter and `route.hedge_symbol` from the hedge adapter, verifies that both returned values are `VenueObservation` instances, and delegates route-aligned snapshot construction to `assemble_route_snapshot()`.
- Reason: Adapters must remain per-venue observation sources, while cross-venue route alignment, executable quote construction, funding/fee preservation, and metadata validation remain in the existing snapshot owner path.
- Decision: Focused tests use injected adapters only and invariant coverage checks that the handoff does not call `evaluate_route()` or own EV, VWAP, fee, funding, ledger, paper, execution, or live behavior.
- Reason: Real HTTP availability, credentials, profitability decisions, and trading behavior are outside RX-024 and must remain fail-closed behind later explicit tasks.
- Affected files/modules: `core/pipeline/snapshot.py`, focused unit tests, invariant tests, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no previous decision is superseded; RX-024 reuses the RX-004 `assemble_route_snapshot()` owner boundary and the RX-022/RX-023 read-only adapter boundaries.
- Non-decisions: RX-024 does not call `evaluate_route()`, calculate EV, rank routes, mutate eligibility, write ledger events, replay ledger history, start paper lifecycle, create plans, use private/account/auth endpoints, add credentials, place orders, add live runner behavior, enable live trading, add route statuses, add reject reasons, add artificial filters, create canary architecture, add hold-next-cycle logic, or create a second decision, snapshot, EV, fee, funding, VWAP, basis, ledger-write, replay, or live execution path.

## 2026-08-12 - RX-025

- Date: 2026-08-12
- Decision: Added `run_real_data_research_route()` in `apps/research_runner/real_data.py` as the one-route real-data research runner.
- Reason: RX-025 needs a non-trading runner surface that accepts one existing `RouteCandidate`, existing read-only venue adapters, an explicit timezone-aware assembly timestamp, and an `EvaluationMode` while preserving the existing snapshot and decision owners.
- Decision: The runner delegates snapshot creation to `assemble_route_snapshot_from_adapters()` and delegates route decisions to `evaluate_route(route, snapshot, mode)` only after successful snapshot assembly.
- Reason: Real-data research orchestration must not become a second snapshot assembly path, second route decision path, or app-owned economics path.
- Decision: Adapter or snapshot handoff failures return a deterministic `DecisionResult` with `RouteStatus.REJECTED`, `RejectReason.REQUIRED_LIVE_DATA_MISSING`, and `decided_at=assembled_at` before evaluation.
- Reason: Real-data availability failures must fail closed without calculating profitability, writing ledger evidence, starting paper lifecycle, or invoking live/execution behavior.
- Decision: The existing fake CLI remains unchanged; RX-025 exposes an importable app-layer runner only.
- Reason: The task required minimal app wiring only if needed, and avoiding CLI changes preserves fake runner behavior while still exposing the research runner to explicit callers.
- Affected files/modules: `apps/research_runner/real_data.py`, focused unit tests, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no previous decision is superseded; RX-025 reuses the RX-024 adapter handoff, the RX-004 `assemble_route_snapshot()` owner boundary, and the existing `evaluate_route()` decision path.
- Non-decisions: RX-025 does not discover routes, rank routes, add watchlists, start background loops, write ledger events, start paper lifecycle, verify funding settlement, plan execution, place orders, use private/account/auth endpoints, add credentials, add CLI behavior, add live runner behavior, enable live trading, add route statuses, add reject reasons, add artificial filters, create canary architecture, add hold-next-cycle logic, or create a second decision, snapshot, EV, fee, funding, VWAP, basis, ledger-write, replay, or live execution path.

## 2026-08-12 - RX-026

- Date: 2026-08-12
- Decision: Added `verify_approval_gated_funding_settlement()` in `core/monitoring/funding_settlement.py` as the approval-gated workflow for one existing `Capture`, one existing `RouteCandidate`, and one explicit funding settlement timestamp.
- Reason: RX-026 needs a narrow caller-supplied observed settlement verification path without creating a second funding verifier, second ledger-write path, second replay path, route decision path, snapshot path, execution path, or live runner.
- Decision: Existing `funding_settlement_evidence_recorded` events now carry mandatory `approval_granted` evidence through `append_funding_settlement_evidence_event()`.
- Reason: Canonical replay must not treat settlement values as observed proof unless the caller or deterministic test explicitly approved that evidence for the current Capture settlement.
- Decision: Canonical funding settlement replay now requires `approval_granted=True`, `observed_at == settlement_time`, actual settlement funding/notional values with `ValueSource.OBSERVED`, and exact Capture/route/settlement consistency.
- Reason: Missing approval, false approval, stale observation time, unknown values, unobserved sources, malformed payloads, cross-capture, cross-route, cross-settlement, or contradictory settlement evidence must fail closed.
- Affected files/modules: `core/monitoring/funding_settlement.py`, `core/accounting/ledger.py`, `core/accounting/reconciliation.py`, replay tests, and governance docs.
- Superseded decisions: RX-008's observed settlement evidence contract is tightened; observed actual values alone are not sufficient proof without explicit approval and exact settlement-time observation.
- Non-decisions: RX-026 does not call `evaluate_route()`, assemble snapshots, calculate EV, fees, funding, VWAP, basis, spread, slippage, or profitability; does not mutate route eligibility; does not start or change paper lifecycle; does not change real-data research runner behavior; does not reconcile ledgers; does not add execution planning, orders, live runner behavior, private/account/auth endpoints, credentials, live trading, executable `CapturePlan`, route statuses, reject reasons, artificial filters, canary architecture, hold-next-cycle logic, or a second decision, snapshot, verifier, ledger-write, replay, economics, or live execution path.

## 2026-08-12 - RX-027

- Date: 2026-08-12
- Decision: Added `NonSendingExecutionPlan` and `plan_execution_without_orders()` in `core/execution/planning.py` as the execution-boundary planning surface for one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, and already-derived prerequisite evidence.
- Reason: RX-027 needs an explicit way to describe intended entry and unwind actions after route decision, funding verification, ledger reconciliation, CapturePlan freshness, and execution-capability evidence have already passed, without turning that description into orders or live runner behavior.
- Decision: Planning consumes existing `DecisionResult`, `FundingSettlementVerificationResult`, `LedgerReconciliationResult`, `CapturePlanFreshnessEvidence`, and `ExecutionCapabilityEvidence` values and reuses the existing CapturePlan freshness and execution-capability risk gates.
- Reason: The workflow must stay downstream of existing owner modules and avoid a second route decision path, funding verifier, ledger replay path, VWAP/liquidity path, economics path, or execution-capability gate.
- Decision: RX-027 does not add a ledger event or reconciliation replay for generated plans.
- Reason: The task requires plans as non-executable evidence only. Recording plans would require a broader accounting/replay contract and is deferred unless a future accepted task explicitly requires it.
- Affected files/modules: `core/execution/planning.py`, focused unit tests, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no previous decision is superseded; RX-027 adds a narrow non-sending execution-planning boundary after existing prerequisite evidence.
- Non-decisions: RX-027 does not call `evaluate_route()`, assemble snapshots, calculate EV, fees, funding, VWAP, basis, spread, slippage, price impact, or profitability; does not mutate route eligibility; does not write ledger events or add ledger replay; does not start or change paper lifecycle; does not change funding settlement verification, ledger reconciliation, real-data research runner behavior, risk gate contracts, route statuses, or `RejectReason` values; does not call adapters, use private/account/auth endpoints, add credentials, import live runner behavior, create executable `CapturePlan` objects, place orders, enable live trading, add artificial filters, create canary architecture, add hold-next-cycle logic, or create a second decision, snapshot, verifier, ledger-write, replay, economics, or live execution path.

## 2026-08-12 - RX-028

- Date: 2026-08-12
- Decision: Added `GuardedLiveRunnerResult` and `run_guarded_live_without_orders()` in `apps/live_runner/guarded.py` as the app-level guarded live runner surface for one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one existing non-sending execution plan, and already-derived prerequisite evidence.
- Reason: RX-028 needs a deterministic live-runner workflow that can prove exact prerequisite coverage and explicit live-switch intent while still stopping before orders, sendable exchange requests, private endpoints, or live eligibility mutation.
- Decision: The runner consumes existing `FundingSettlementVerificationResult`, `LedgerReconciliationResult`, `LiveGateEvidenceBundle`, and `NonSendingExecutionPlan` values and reuses `check_live_gate_evidence_bundle()` for risk-owned bundle validation.
- Reason: The workflow must remain downstream of accepted owner modules and avoid a second route decision path, funding verifier, ledger replay path, CapturePlan freshness gate, execution-capability gate, execution-planning path, or order path.
- Decision: `tests/invariant/test_no_forbidden_imports.py` now treats `apps/live_runner` as a downstream app boundary that may import `core.execution.planning`; upstream modules still must not import execution modules.
- Reason: RX-028 must accept the existing `NonSendingExecutionPlan` contract exactly, without weakening the upstream execution-import boundary.
- Affected files/modules: `apps/live_runner/guarded.py`, `apps/live_runner/__init__.py`, focused unit tests, invariant import tests, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no previous decision is superseded; RX-028 adds a narrow no-order live-runner boundary after non-sending execution planning.
- Non-decisions: RX-028 does not call `evaluate_route()`, assemble snapshots, calculate EV, fees, funding, VWAP, basis, spread, slippage, price impact, or profitability; does not replay funding or ledger history; does not write ledger events or add ledger replay; does not start or change paper lifecycle; does not change funding settlement verification, ledger reconciliation, execution planning, real-data research runner behavior, risk gate contracts, route statuses, or `RejectReason` values; does not call adapters, use private/account/auth endpoints, add credentials, import order placement behavior, create executable `CapturePlan` objects, construct sendable exchange requests, place orders, enable live trading by default, add artificial filters, create canary architecture, add hold-next-cycle logic, or create a second decision, snapshot, verifier, ledger-write, replay, economics, execution-planning, or order path.

## 2026-08-12 - RX-029

- Date: 2026-08-12
- Decision: Added `OrderPlacementApproval`, `ApprovalGatedOrderPlacementResult`, and `run_approval_gated_order_boundary()` in `core/execution/orders.py` as the execution-owned explicit approval-gated order placement boundary for one existing Capture, route, funding settlement timestamp, guarded readiness timestamp, non-sending plan, and caller-supplied approval.
- Reason: RX-029 needs a deterministic boundary after guarded no-order readiness that distinguishes human task authorization from exact per-capture order approval, without creating exchange requests, credentials, adapters, or automatic order placement.
- Decision: Added `run_approval_gated_live_order_placement()` in `apps/live_runner/order_placement.py` as a thin app wrapper that consumes exact `GuardedLiveRunnerResult` values and delegates to `core/execution`.
- Reason: `GuardedLiveRunnerResult` is app-local. The wrapper preserves dependency direction by avoiding a `core/execution -> apps/live_runner` import while still making the workflow downstream of the existing guarded runner result.
- Decision: Direct `send_order()` remains disabled and raises `OrderPlacementDisabled`.
- Reason: RX-029 establishes an approval boundary only. It is not permission for direct send calls, real exchange order submission, or default live trading.
- Affected files/modules: `core/execution/orders.py`, `apps/live_runner/order_placement.py`, `apps/live_runner/__init__.py`, focused unit tests, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: RX-028's no-order readiness remains no-order readiness only; RX-029 adds a separate explicit approval gate downstream and does not make guarded readiness order permission by itself.
- Non-decisions: RX-029 does not call `evaluate_route()`, assemble snapshots, calculate EV, fees, funding, VWAP, basis, spread, slippage, price impact, or profitability; does not replay funding or ledger history; does not write ledger events or add ledger replay; does not start or change paper lifecycle; does not change funding settlement verification, ledger reconciliation, execution planning, guarded live runner behavior, real-data research runner behavior, risk gate contracts, route statuses, or `RejectReason` values; does not call adapters, use private/account/auth endpoints, add credentials, create exchange request payloads, place real orders, enable live trading by default, add artificial filters, create canary architecture, add hold-next-cycle logic, or create a second decision, snapshot, verifier, ledger-write, replay, economics, live-runner, execution-planning, or order path.

## 2026-08-12 - RX-030

- Date: 2026-08-12
- Decision: Added `render_capture_monitor_view()` in `apps/dashboard/read_only.py` as the read-only dashboard renderer for one existing Capture, one existing RouteCandidate, one explicit settlement timestamp, and already-derived caller-supplied deterministic evidence.
- Reason: RX-030 needs a minimal monitoring surface after the explicit approval boundary without turning dashboard display into a decision path, evidence replay path, execution path, polling loop, or order path.
- Decision: The renderer returns display dictionaries with exact identity, route details, existing decision state, funding verification state, ledger reconciliation state, live-gate bundle state, non-sending plan state, guarded no-order readiness state, approval evidence state, approval-boundary result state, and copied economics values.
- Reason: Dashboard output must be inspectable by callers while preserving existing owner modules as the source of all product decisions and prerequisite evidence.
- Decision: Missing, malformed, stale, cross-capture, cross-route, cross-settlement, unverified, unreconciled, non-ready, false approval, stale approval, or boundary-blocked evidence renders as `missing` or `blocked`; missing economics render as missing values instead of zero.
- Reason: Monitoring must fail closed and must not silently normalize absent or unknown facts into successful display state.
- Affected files/modules: `apps/dashboard/read_only.py`, `apps/dashboard/__init__.py`, focused unit tests, invariant tests, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: RX-004/RX-005/RX-006 non-decisions that excluded dashboard code are narrowed only for this RX-030 read-only dashboard owner area; adapter, decision, ledger, execution, and live boundaries remain unchanged.
- Non-decisions: RX-030 does not call `evaluate_route()`, assemble snapshots, calculate EV, fees, funding, VWAP, basis, spread, slippage, price impact, or profitability; does not verify funding, reconcile ledger history, check live-gate bundles, plan execution, run guarded live readiness, call approval-boundary execution, replay funding or ledger history, write ledger events, start or change paper lifecycle, mutate route eligibility, call adapters, use private/account/auth endpoints, add credentials, poll, schedule, alert, auto-refresh, create exchange request payloads, place real orders, enable live trading by default, add route statuses, add `RejectReason` values, add artificial filters, create canary architecture, add hold-next-cycle logic, or create a second decision, snapshot, verifier, ledger-write, replay, economics, live-runner, execution-planning, or order path.

## 2026-08-13 - RX-032

- Date: 2026-08-13
- Decision: Recorded Product Owner authorization, as narrowed by Control Tower, as authorization for exactly one next governance/docs task: Control Tower Autonomous Task Selection Governance.
- Reason: The Product Owner requested autonomous future task execution, and Control Tower rejected blanket authorization for dangerous scope. The repository handoff must therefore capture the narrowed authorization before any workflow autonomy rule changes are made.
- Decision: The authorization does not remove explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- Reason: Autonomous task selection for non-dangerous work must not weaken the product's live/order/private/account-state safety boundaries or the repository's one-task-at-a-time review discipline.
- Affected files/modules: `STATUS.md`, `IMPLEMENTATION_PLAN.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no product or architecture decisions are superseded; RX-Q001, RX-Q002, RX-Q004, and the existing live/order safety decisions remain in force.
- Non-decisions: RX-032 does not change product behavior, dashboard behavior, route discovery, ranking, watchlists, loops, polling, scheduling, alerts, auto-refresh, adapters, market-data calls, private endpoints, credentials, account balances/state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay behavior, paper lifecycle, route eligibility, Capture state transitions, EV, fees, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, safety-margin filters, route statuses, reject reasons, canary architecture, hold-next-cycle logic, live trading by default, or any new functions, classes, dataclasses, enums, modules, wrappers, config values, trace fields, future hooks, or contracts.

## 2026-08-13 - RX-033

- Date: 2026-08-13
- Decision: After RX-033 reviewer acceptance, Control Tower may autonomously select, create, run, coordinate review/fixes for, and finalize future non-dangerous RX tasks from source-of-truth repository docs without asking the user to name each next task.
- Reason: RX-032 recorded the narrowed Product Owner authorization for autonomous future task execution while preserving the repository's safety and review boundaries.
- Decision: Control Tower autonomy is constrained to one RX task at a time, one clean Codex executor task, one task branch, source-of-truth repository docs, exactly-one-task `NEXT_TASK.md`, Parent ownership, worker checkpoint requirements, and explicit reviewer acceptance.
- Reason: Autonomous task selection must not become batched work, continuous unattended chaining, self-acceptance, or a bypass around branch/review discipline.
- Decision: Explicit user approval remains required before selecting, creating, running, fixing, or finalizing any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- Reason: Autonomy for non-dangerous repository tasks must not weaken live/order/private/account-state safety gates.
- Affected files/modules: `AGENTS.md`, `docs/WORKFLOW.md`, `docs/templates/RX_TASK_TEMPLATE.md`, `docs/templates/REVIEW_CHECKLIST.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: RX-032's authorization-only decision is narrowed by this governance implementation after reviewer acceptance; no product or architecture decisions are superseded.
- Non-decisions: RX-033 does not change product behavior, dashboard behavior, route discovery, ranking, watchlists, loops, polling, scheduling, alerts, auto-refresh, adapters, market-data calls, private endpoints, credentials, account balances/state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay behavior, paper lifecycle, route eligibility, Capture state transitions, EV, fees, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, safety-margin filters, route statuses, reject reasons, canary architecture, hold-next-cycle logic, live trading by default, or any new functions, classes, dataclasses, enums, modules, wrappers, config values, trace fields, future hooks, or contracts.

## 2026-08-13 - RX-034

- Date: 2026-08-13
- Decision: After RX-033 reviewer acceptance, the roadmap selection audit inspected the source-of-truth repository docs and found no clearly grounded concrete post-RX-034 product/runtime task.
- Reason: `NEXT_TASK.md` authorized a fallback when candidate tasks are not clearly grounded in source-of-truth docs, and `IMPLEMENTATION_PLAN.md` / `STATUS.md` listed RX-034 as the current next task without defining a concrete later product handoff.
- Decision: The next handoff is RX-035 Post-RX-034 Roadmap Handoff Cleanup, a metadata-only governance cleanup task rather than inferred product scope.
- Reason: The repository must preserve one task, one branch, source-of-truth grounding, reviewer-only acceptance, and hard approval gates while avoiding product/runtime invention.
- Decision: RX-034 implementation work must occur only in the clean executor worktree `/Users/daniilmakarov/.codex/worktrees/69f5/risex-main`; the earlier `/Users/daniilmakarov/Desktop/risex-main` branch switch produced no file edits and is excluded from RX-034 implementation.
- Reason: Control Tower corrected branch placement before implementation edits, preserving one clean executor task branch for RX-034.
- Affected files/modules: `STATUS.md`, `IMPLEMENTATION_PLAN.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no product or architecture decisions are superseded; RX-033 autonomy and all hard approval gates remain in force.
- Non-decisions: RX-034 does not change product behavior, dashboard behavior, route discovery, ranking, watchlists, loops, polling, scheduling, alerts, auto-refresh, adapters, market-data calls, private endpoints, credentials, account balances/state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay behavior, paper lifecycle, route eligibility, Capture state transitions, EV, fees, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, safety-margin filters, route statuses, reject reasons, canary architecture, hold-next-cycle logic, live trading by default, or any new functions, classes, dataclasses, enums, modules, wrappers, config values, trace fields, future hooks, or contracts.

## 2026-08-13 - RX-035

- Date: 2026-08-13
- Decision: After RX-034 reviewer acceptance, RX-035 re-inspected the source-of-truth repository docs and found that they still do not clearly ground a concrete post-RX-034 product/runtime task.
- Reason: RX-034 prepared RX-035 as a metadata-only fallback handoff, and the current source-of-truth docs still identify no specific non-dangerous product/runtime implementation step after RX-034.
- Decision: The next handoff is RX-036 Roadmap Source-of-Truth Clarification Gate, a metadata-only governance clarification task rather than inferred product scope.
- Reason: The repository must preserve one task, one branch, source-of-truth grounding, reviewer-only acceptance, Parent ownership, and hard approval gates while avoiding product/runtime invention.
- Decision: RX-035 implementation work occurs only in the clean executor worktree `/Users/daniilmakarov/.codex/worktrees/8b93/risex-main`; an initial branch switch in `/Users/daniilmakarov/Desktop/risex-main` produced no file edits and was stopped by Control Tower before implementation edits.
- Reason: Control Tower corrected branch placement before edits, preserving one clean executor task branch for RX-035 and excluding the Desktop checkout from implementation.
- Affected files/modules: `STATUS.md`, `IMPLEMENTATION_PLAN.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no product or architecture decisions are superseded; RX-033 autonomy, reviewer-only acceptance, Parent ownership, worker checkpoint requirements, and all hard approval gates remain in force.
- Non-decisions: RX-035 does not change product behavior, dashboard behavior, route discovery, ranking, watchlists, loops, polling, scheduling, alerts, auto-refresh, adapters, market-data calls, private endpoints, credentials, account balances/state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay behavior, paper lifecycle, route eligibility, Capture state transitions, EV, fees, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, safety-margin filters, route statuses, reject reasons, canary architecture, hold-next-cycle logic, live trading by default, or any new functions, classes, dataclasses, enums, modules, wrappers, config values, trace fields, future hooks, or contracts.

## 2026-08-13 - RX-036

- Date: 2026-08-13
- Decision: After RX-035 reviewer acceptance, RX-036 re-inspected the source-of-truth repository docs and found that they still do not clearly ground a concrete non-dangerous post-RX-035 product/runtime task.
- Reason: RX-035 prepared RX-036 as a metadata-only clarification gate, and the current source-of-truth docs still identify no specific product/runtime implementation step after the repeated post-audit fallback.
- Decision: The next handoff is RX-037 Product Owner Roadmap Direction Gate, a metadata-only governance gate requiring explicit Product Owner roadmap direction before product/runtime scope resumes.
- Reason: The repository must avoid an endless metadata-cleanup loop while preserving one task, one branch, source-of-truth grounding, reviewer-only acceptance, Parent ownership, worker checkpoint requirements, and hard approval gates.
- Decision: RX-036 implementation work occurs only in the clean executor worktree `/Users/daniilmakarov/.codex/worktrees/95af/risex-main`; an initial branch switch in `/Users/daniilmakarov/Desktop/risex-main` produced no file edits and was stopped by Control Tower before implementation edits.
- Reason: Control Tower corrected branch placement before edits, preserving one clean executor task branch for RX-036 and excluding the Desktop checkout from implementation.
- Affected files/modules: `STATUS.md`, `IMPLEMENTATION_PLAN.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no product or architecture decisions are superseded; RX-033 autonomy, reviewer-only acceptance, Parent ownership, worker checkpoint requirements, and all hard approval gates remain in force.
- Non-decisions: RX-036 does not change product behavior, dashboard behavior, route discovery, ranking, watchlists, loops, polling, scheduling, alerts, auto-refresh, adapters, market-data calls, private endpoints, credentials, account balances/state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay behavior, paper lifecycle, route eligibility, Capture state transitions, EV, fees, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, safety-margin filters, route statuses, reject reasons, canary architecture, hold-next-cycle logic, live trading by default, or any new functions, classes, dataclasses, enums, modules, wrappers, config values, trace fields, future hooks, or contracts.

## 2026-08-13 - RX-037

- Date: 2026-08-13
- Decision: Recorded explicit Product Owner roadmap direction supplied through Control Tower: the long-term product direction is a live-capable hedged funding capture system on RiseX with hedge venue support, initially Hyperliquid.
- Reason: RX-036 intentionally stopped at a Product Owner roadmap direction gate before product/runtime scope resumed. The supplied direction resolves the post-RX-035 source-of-truth gap without inventing scope from chat memory or broad roadmap implication.
- Decision: The current implementation posture remains non-trading and fail-closed. Future movement toward live readiness must happen through exact, reviewable, fail-closed stages and must not enable live trading by default.
- Reason: The Product Owner direction names a live-capable end goal but does not authorize live trading, private/account endpoints, credentials, account balances/state, orders, sendable exchange request construction, execution automation, or financially dangerous actions in RX-037 or RX-038.
- Decision: The next handoff is exactly one task: RX-038, a manual one-route real-data CLI toward live readiness using existing read-only public RiseX and Hyperliquid adapters, the existing one-route real-data snapshot handoff, and the existing one-route real-data research runner/evaluate path.
- Reason: RX-038 is the only next product/runtime task explicitly supplied by the Product Owner direction, and it is non-dangerous when scoped as manual, one-route-at-a-time, public-data-only, read-only, fail-closed, and non-trading.
- Decision: RX-038 must fail closed on missing, unknown, or malformed input, and unknown values must never silently become zero.
- Reason: The existing repository invariants require source-aware missing data handling, explicit route identity and target notional construction, and fail-closed behavior before route evaluation or live-adjacent workflows.
- Affected files/modules: `STATUS.md`, `IMPLEMENTATION_PLAN.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: no product or architecture decisions are superseded; RX-033 autonomy, reviewer-only acceptance, Parent ownership, worker checkpoint requirements, and all hard approval gates remain in force.
- Non-decisions: RX-037 does not change product behavior, runtime code, dashboard behavior, route discovery, ranking, watchlists, loops, polling, scheduling, alerts, auto-refresh, adapters, market-data behavior, private endpoints, credentials, account balances/state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay behavior, paper lifecycle, route eligibility, Capture state transitions, EV, fees, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, safety-margin filters, route statuses, reject reasons, canary architecture, hold-next-cycle logic, live trading by default, or any new functions, classes, dataclasses, enums, modules, wrappers, config values, trace fields, future hooks, or contracts.

## 2026-08-13 - RX-038

- Date: 2026-08-13
- Decision: Added `real-data-route` in `apps/cli/main.py` as the manual CLI entry point for one explicitly supplied RiseX plus Hyperliquid route.
- Reason: RX-038 needs an operator-invoked read-only public-data surface toward live readiness while preserving the existing one-route real-data runner and the single route evaluation path.
- Decision: The CLI validates route id, capture id, exact RiseX and Hyperliquid venue names, symbols, opposing entry sides, positive finite target notional, evaluation mode, and timezone-aware assembly timestamp before adapter construction.
- Reason: Malformed CLI input must fail closed before public adapter calls and before the existing runner can be invoked.
- Decision: After validation, the CLI instantiates the existing read-only public `RiseXObservationAdapter` and `HyperliquidObservationAdapter`, then calls `run_real_data_research_route()`.
- Reason: The CLI must not call `assemble_route_snapshot_from_adapters()` or `evaluate_route()` directly, and it must not create a second snapshot, decision, or economics owner path.
- Decision: CLI output is deterministic key/value text copied from the existing `DecisionResult`, preserving missing net profit and entry EV fields as `None`.
- Reason: Unknown public-adapter economics must remain missing and must not silently become zero or default economics.
- Decision: Existing no-argument fake Broad Scan/Focused Refresh CLI behavior is unchanged.
- Reason: RX-038 adds a manual subcommand only and must not disturb the deterministic offline fake runner path.
- Affected files/modules: `apps/cli/main.py`, `tests/unit/test_cli_main.py`, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Superseded decisions: RX-025's non-decision that excluded CLI behavior is narrowed only by adding this manual CLI boundary; the RX-025 runner remains the only one-route real-data research orchestration path.
- Non-decisions: RX-038 does not add route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, private endpoints, credentials, account balances/state, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route evaluation changes, snapshot assembly changes, profitability/EV/fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin changes, route statuses, reject reasons, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.
