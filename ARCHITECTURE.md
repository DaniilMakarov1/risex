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
- `RouteCandidate`: a potential RiseX + hedge route with authoritative venues, symbols, target notional, and intended opposing entry sides.
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
- `RouteStatus`: `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `LIVE_ELIGIBLE`, `REJECTED`.
- `EvaluationMode`: `DISCOVERY` or `ENTRY`.
- `ValueSource`: `DOCUMENTED`, `OBSERVED`, `ESTIMATED_FROM_ORDERBOOK`, `ESTIMATED_FROM_LAST_VALUE`, `USER_CONFIGURED`, `UNKNOWN`.
- `RejectReason`: the centralized route rejection and live-gate reason enum.
- `FundingCheckpointRequirement`: one required pre-settlement observation offset for future settlement proof.
- `FundingSettlementVerificationResult`: deterministic replay result proving whether fake checkpoint evidence and fake observed settlement evidence agree for one Capture settlement.
- `LedgerReconciliationResult`: deterministic replay result proving whether one Capture ledger history is internally consistent and explicitly reconciled.

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
- Route snapshot assembly happens only in `core/pipeline/snapshot.py`.
- Route decisions happen only in `core/pipeline/evaluate.py`.
- Offline route-candidate orchestration happens only in `core/pipeline/offline_scan.py`.
- Broad Scan and Focused Refresh orchestration happens only in `core/pipeline/scan_refresh.py`.
- Orders can be sent only through `core/execution/`.
- Ledger writes happen only through `core/accounting/ledger.py`.
- Ledger reconciliation happens only in `core/accounting/reconciliation.py`.
- Funding settlement verification happens only in `core/monitoring/funding_settlement.py`.
- Fake paper lifecycle orchestration happens only in `apps/paper_runner/lifecycle.py`.

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

RX-004 adds a deterministic offline snapshot assembly layer before evaluation:

1. Venue adapters return per-venue `VenueObservation` objects, never cross-venue snapshots.
2. `core/pipeline/snapshot.py` owns the single `assemble_route_snapshot()` function.
3. The assembly function accepts one `RouteCandidate`, a mapping of `(venue, symbol)` observations, and an explicit timezone-aware assembly timestamp.
4. It locates the required RiseX and hedge observations, fails explicitly on missing or contradictory metadata, and uses `calculate_executable_quote()` for all four entry/immediate-unwind quotes.
5. It preserves per-leg observation timestamps and funding settlement timestamps on the resulting `VenueSnapshot`.
6. It does not call `evaluate_route()`, calculate EV, apply eligibility, rank routes, write ledger events, create `Capture`/`CapturePlan`, connect to venues, or place orders.

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

- RiseX venue and symbol.
- RiseX intended entry side.
- Hedge venue and symbol.
- Hedge intended entry side.
- Target notional in USD.

`core/risk/gates.py` owns the centralized route/snapshot alignment gate. Before Entry EV, it verifies:

- RiseX entry and estimated-exit quotes match the route venue and symbol.
- Hedge entry and estimated-exit quotes match the route venue and symbol.
- RiseX and hedge entry sides are opposing market exposure.
- Entry quote sides match the route contract.
- Each estimated-exit side is opposite its corresponding entry side.
- All four quotes use `route.target_notional_usd`.
- All four quotes are sourced from `ValueSource.ESTIMATED_FROM_ORDERBOOK`.
- Entry and estimated-exit quotes paired for roundtrip math use the same venue and symbol.

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
