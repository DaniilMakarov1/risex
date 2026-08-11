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
