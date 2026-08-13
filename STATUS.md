# Status

- Current branch: `task/rx-035-post-rx-034-roadmap-handoff-cleanup`.
- Current task: RX-035 — Post-RX-034 Roadmap Handoff Cleanup implementation.
- RX-035 starting baseline: `4c3532bb38860be815f65683f3f771865d3ed1ee`
- RX-035 review state: implementation-complete on task branch; reviewer acceptance pending.
- RX-035 implementation branch HEAD is intentionally not recorded in this file to avoid self-referential branch metadata; use git history for the exact final task-branch commit.
- RX-035 disposition: source-of-truth docs were re-inspected after RX-034 reviewer acceptance. They still do not clearly ground a concrete post-RX-034 product/runtime task, so RX-035 remains metadata-only and prepares one RX-036 roadmap source-of-truth clarification handoff instead of inventing product scope.
- RX-035 branch-discipline steer: Control Tower stopped work before implementation edits after detecting an initial branch switch in `/Users/daniilmakarov/Desktop/risex-main`. No files were edited there. The Desktop checkout was restored to clean `main`, and RX-035 implementation continued only in the clean executor worktree `/Users/daniilmakarov/.codex/worktrees/8b93/risex-main`.
- RX-034 starting baseline: `e4e7c940d17b83d08f78671f92ec5c18f4d71749`
- RX-034 review state: reviewer-accepted and finalized on `main`.
- Accepted RX-034 implementation HEAD: `25498f90a17889183fe4e5b262c3574ff362a785`
- RX-034 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- RX-034 disposition: source-of-truth docs were inspected after RX-033 reviewer acceptance. They do not clearly ground a concrete post-RX-034 product/runtime task, so the RX-034 fallback path prepared one metadata-only RX-035 handoff cleanup instead of inventing product scope.
- RX-034 branch-discipline steer: after an initial branch switch in `/Users/daniilmakarov/Desktop/risex-main`, Control Tower directed RX-034 work to continue only in the clean executor worktree `/Users/daniilmakarov/.codex/worktrees/69f5/risex-main`. No files were edited in the Desktop checkout; implementation edits are limited to the clean executor worktree.
- RX-033 starting baseline: `ff27045e0f1dccbccc21aec1d41eb4ad91549e8c`
- RX-033 review state: reviewer-accepted and finalized on `main`.
- Accepted RX-033 implementation HEAD: `9efc39fbf0e882d47259e1180eaa30189368dfdf`
- RX-033 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- RX-033 disposition: governance/docs-only changes define Control Tower autonomous task selection for future non-dangerous RX tasks while preserving explicit approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions.
- RX-032 starting baseline: `1eee2c26e40030b1ba7a3935d4eb6483acfd9a81`
- RX-032 review state: reviewer-accepted and finalized on `main`.
- Accepted RX-032 implementation HEAD: `9ee0e56a0ecb6be7c95182047353774db11a3155`
- RX-032 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- RX-032 disposition: Product Owner authorization, as narrowed by Control Tower, is recorded as authorization to prepare exactly one next governance/docs task: RX-033 Control Tower Autonomous Task Selection Governance. This does not remove explicit approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- RX-031 starting baseline: `917da9e241862f9c744e78fbc795f732f0f92f5f`
- RX-031 review state: reviewer-accepted and finalized on `main`.
- Accepted RX-031 implementation HEAD: `39931ba1bee85faba939741cc2545cdf9009e874`
- RX-031 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- RX-031 disposition: local repo/git evidence and the GitHub connector exposed no additional explicit actionable reviewer feedback after RX-030 finalization, so no dashboard or product code was changed.
- RX-030 starting baseline: `c91e7190b122de621fd035c38ed4943fac618bab`
- RX-030 review state: reviewer-accepted and finalized on `main`.
- Latest accepted product task: RX-030 — Read-Only Monitoring Dashboard Without Decisions Or Orders.
- Accepted RX-030 implementation HEAD: `dbbc7de1075a1dec9dfc295153f47859f1183763`
- RX-030 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- Previous accepted product task before RX-030: RX-029 — Explicit Approval-Gated Order Placement Boundary.
- RX-029 starting baseline: `e2771bc9e6ce2730159bb120d784635e9030f428`
- RX-029 review state: reviewer-accepted and finalized on `main`.
- Accepted RX-029 implementation HEAD: `101544b08c0233b9bebc90958e2d1049c8127116`
- RX-029 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- Previous accepted product task before RX-029: RX-028 — Guarded Live Runner Without Orders.
- RX-028 starting baseline: `4d8ea09ba5e06cb9d46ed22a9ea1f89564c8bfbb`
- RX-028 review state: reviewer-accepted and finalized on `main`.
- Accepted RX-028 implementation HEAD: `ca475a6c2ea3686e0ebf7710658160b1b4d3e4fc`
- RX-028 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- Previous accepted product task before RX-028: RX-027 — Execution Planning Without Orders.
- Accepted RX-027 implementation HEAD: `7131d752e23598515fb8eaf426e1cf98f97b756f`
- RX-027 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- Previous accepted product task before RX-027: RX-026 — Approval-Gated Real Funding Settlement Verification.
- Accepted RX-026 implementation HEAD: `481f9257ad5e541508001d86248cdac96e90ba7c`
- RX-026 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- RX-026 starting baseline: `709cf6c6e1b32ccb06f57d66ee18d862fef2056c`
- Previous accepted product task before RX-026: RX-025 — Real-Data Research Runner.
- Accepted RX-025 implementation HEAD: `c684c167579372b06c4400858bcff0763ecf1b38`
- RX-025 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- RX-025 starting baseline: `d2ef60e9ba5d0d06da23755c389d9981a66a22d7`
- Previous accepted product task before RX-025: RX-024 — Real Market-Data Route Snapshot Assembly.
- Accepted RX-024 implementation HEAD: `0a336dd5e00ee54795540fa5170e953b2b7d7131`
- RX-024 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- Previous accepted product task before RX-024: RX-023 — Read-only Hyperliquid Observation Adapter.
- Accepted RX-023 implementation HEAD: `49fd3215e8835c7beeb13a3261b562dfd782ae24`
- RX-023 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- RX-024 starting baseline: `ff5898c654c68859bdd07ea5099e94ae66e0cfd8`
- Previous accepted product task before RX-023: RX-022 — Read-only RiseX Observation Adapter.
- Accepted RX-022 implementation HEAD: `5f274c17d605cb75485c2d79608cd089190ac5a8`
- RX-022 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- Previous accepted product task before RX-022: RX-021 — Paper Result Attribution And PnL Explanation.
- Accepted RX-021 implementation HEAD: `4298916ed72067bbf4c008b2750f155de36761ee`
- RX-021 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- Previous accepted product task before RX-021: RX-020 — RouteCandidate Identity And Notional Contract Hardening.
- Accepted RX-020 implementation HEAD: `832bcf54019a7314581d02749673e40ae4d36d2a`
- RX-020 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- Latest completed governance/docs task: RX-Q004 — Roadmap And Rulebook Consolidation.
- RX-Q004 is accepted governance/docs-only consolidation work from `task/rx-q004-roadmap-rulebook-consolidation`; it does not change product behavior and is not a product baseline.
- RX-Q004 completion is recorded without a final `main` HEAD in this file to avoid self-referential handoff metadata; use git history for the exact finalization commit.
- Previous completed task: RX-019 — Reviewer-Directed Follow-up After RX-018
- RX-019 completion is recorded without a final HEAD in this file to avoid self-referential handoff metadata; use git history for the exact commit sequence.
- RX-019 changed only repository handoff metadata and did not change product behavior.
- Previous accepted product task before RX-020: RX-018 — Settlement Timestamp Alignment Contract
- Accepted RX-018 implementation HEAD: `f5420c8526fa9b7c5b3dd5780eea9e0d7fb764aa`
- Previous accepted product task before RX-018: RX-016 — Offline SQLite Ledger Reopen Fail-Closed Replay Coverage
- Accepted RX-016 implementation HEAD: `299c619db9e025ae1dca7b1a44eaa62cf7554f38`
- Accepted RX-016 finalized main HEAD: `b15aeed9a0006ea08742e194adef043379656536`
- Previous accepted product task before RX-016: RX-015 — Offline SQLite Ledger Reopen Append Continuity Replay Coverage
- Accepted RX-015 implementation HEAD: `5dd3cfefd320838c5a171aeacfee8220b2cbb995`
- Previous accepted product task before RX-015: RX-014 — Offline Live Gate Evidence Bundle SQLite Persistence Replay Coverage
- Accepted RX-014 implementation HEAD: `780918d59f3edbff0ea59196b911f4f20d429bc8`
- Accepted RX-014 finalized main HEAD: `85d122892b6dac36d44a3be7e9a261674250d1d7`
- Previous accepted product task before RX-014: RX-013 — Offline Live Gate Evidence Bundle Ledger Recording and Replay Coverage
- Accepted RX-013 implementation HEAD: `dfa06a8a52553b3dfb4687efba0e420abb3e7bf3`
- Previous accepted governance task: RX-Q002 — Worker Checkpoint Requirement for Architecture-Sensitive Tasks
- Accepted RX-Q002 implementation HEAD: `f5a709d290c0d919058cad1e7304fb52c1d12e20`
- Previous accepted product task before RX-013: RX-012 — Offline Live Gate Evidence Bundle Design and Fake Replay Coverage
- Accepted RX-012 implementation HEAD: `1c1c878372be2cbfab7216ef9411b2e4ed3ec94b`
- Previous accepted governance task before RX-Q002: RX-Q001 — Repository Workflow and Quality Guardrails
- Accepted RX-Q001 implementation HEAD: `74ded8e38e324fcf550c1e6946376067dbe08e55`
- Previous accepted product task before RX-012: RX-011 — Offline Execution Capability Gate Design and Fake Replay Coverage
- Accepted RX-011 implementation HEAD: `317d3913ad02082f3d17a228b40da8abee729343`
- Accepted baseline branch: `main`
- Current accepted `main` metadata/governance task: RX-034.
- Current accepted `main` product task: RX-030.
- Current RX task state: RX-035 is implementation-complete on `task/rx-035-post-rx-034-roadmap-handoff-cleanup` and pending reviewer acceptance; latest accepted product task remains RX-030 and latest accepted metadata/governance follow-up is RX-034.

RX-Q004 consolidated the roadmap and rulebook only. It preserved RX-018 as the latest accepted product baseline, classified RX-008 through RX-016 as accepted fail-closed offline safety hardening rather than a product strategy change, and prepared RX-020 as the immediate next implementation task before this branch.
RX-019 is the completed reviewer-directed repository handoff metadata follow-up on `main`.
RX-030 is the latest accepted product baseline on `main`. The accepted work adds one read-only monitoring dashboard renderer for already-derived deterministic fixture evidence only while avoiding route discovery, polling, adapters, route evaluation, snapshot assembly, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live execution, approval-boundary execution, ledger writes, network I/O, orders, and live trading by default.
RX-029 remains the previous accepted product baseline before RX-030. The accepted work adds an explicit approval-gated order placement boundary downstream of RX-028 guarded no-order readiness and RX-027 non-sending execution planning while still avoiding real exchange order submission, credentials, private endpoints, account state, and live trading by default.
RX-028 remains the previous accepted product baseline before RX-029. The accepted work adds a guarded no-order live runner for existing verified prerequisite evidence and existing non-sending execution-plan evidence while stopping before orders, sendable exchange requests, private endpoints, or live trading by default.
RX-027 remains the previous accepted product baseline before RX-028. The accepted RX-027 work includes corrective hardening so execution planning accepts only actual current funding verification and ledger reconciliation result contracts rather than attribute-compatible or module/qualname-spoofed wrong-type objects.
RX-026 remains the previous accepted product baseline before RX-027.
RX-025 remains the previous accepted product baseline before RX-026.
RX-024 remains the previous accepted product baseline before RX-025.
RX-023 remains the previous accepted product baseline before RX-024.
RX-022 remains the previous accepted product baseline before RX-023.
RX-021 remains the previous accepted product baseline before RX-022.
RX-020 remains the previous accepted product baseline before RX-021.
RX-018 remains the previous accepted product baseline before RX-020.
RX-016 remains the previous accepted product baseline before RX-018.
RX-015 remains the previous accepted product baseline before RX-016.
RX-014 remains the previous accepted product baseline before RX-015.
RX-Q002 remains the previous accepted governance baseline on `main`.
RX-013 remains the previous accepted product baseline before RX-014.
RX-012 remains the previous accepted product baseline before RX-013.
RX-Q001 remains the previous accepted governance baseline before RX-Q002.
RX-011 remains the previous accepted product implementation baseline before RX-012.
`NEXT_TASK.md` is prepared for RX-036 after the RX-035 post-audit handoff cleanup branch.
RX-031 found no additional explicit actionable reviewer feedback in local repo/git evidence or GitHub connector context after RX-030 finalization. RX-031 is accepted metadata-only follow-up work and does not change dashboard or product code.
RX-030 remains the latest accepted product task and adds one read-only dashboard renderer for already-derived deterministic fixture evidence only. It does not add route discovery, polling, adapters, route evaluation, snapshot assembly, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live execution, approval-boundary execution, ledger writes, network I/O, or orders.

## Completed accepted tasks

- RX-000
- RX-001
- RX-002
- RX-002A
- RX-003
- RX-004
- RX-005
- RX-006
- RX-007
- RX-008 — Funding Settlement Verifier Design and Fake Replay Coverage
- RX-009 — Ledger Reconciliation Gate Design and Fake Replay Coverage
- RX-010 — Fresh CapturePlan Gate Design and Fake Replay Coverage
- RX-011 — Offline Execution Capability Gate Design and Fake Replay Coverage
- RX-Q001 — Repository Workflow and Quality Guardrails
- RX-012 — Offline Live Gate Evidence Bundle Design and Fake Replay Coverage
- RX-Q002 — Worker Checkpoint Requirement for Architecture-Sensitive Tasks
- RX-013 — Offline Live Gate Evidence Bundle Ledger Recording and Replay Coverage
- RX-014 — Offline Live Gate Evidence Bundle SQLite Persistence Replay Coverage
- RX-015 — Offline SQLite Ledger Reopen Append Continuity Replay Coverage
- RX-016 — Offline SQLite Ledger Reopen Fail-Closed Replay Coverage
- RX-018 — Settlement Timestamp Alignment Contract
- RX-019 — Reviewer-Directed Follow-up After RX-018
- RX-Q004 — Roadmap And Rulebook Consolidation
- RX-020 — RouteCandidate Identity And Notional Contract Hardening
- RX-021 — Paper Result Attribution And PnL Explanation
- RX-022 — Read-only RiseX Observation Adapter
- RX-023 — Read-only Hyperliquid Observation Adapter
- RX-024 — Real Market-Data Route Snapshot Assembly
- RX-025 — Real-Data Research Runner
- RX-026 — Approval-Gated Real Funding Settlement Verification
- RX-027 — Execution Planning Without Orders
- RX-028 — Guarded Live Runner Without Orders
- RX-029 — Explicit Approval-Gated Order Placement Boundary
- RX-030 — Read-Only Monitoring Dashboard Without Decisions Or Orders
- RX-031 — Review-Directed Follow-up After RX-030
- RX-032 — Product Owner Roadmap Authorization Gate
- RX-033 — Control Tower Autonomous Task Selection Governance
- RX-034 — Control Tower Roadmap Selection Audit Gate

## Current architecture status

- Offline modular monolith.
- Capture-centric domain.
- One shared `evaluate_route()` decision path.
- One authoritative `assemble_route_snapshot()` path.
- One deterministic offline route-candidate orchestration path.
- Deterministic fake Broad Scan orchestration using `EvaluationMode.DISCOVERY`.
- Deterministic fake Focused Refresh orchestration using `EvaluationMode.ENTRY`.
- Deterministic fake paper lifecycle downstream of existing `DecisionResult` values.
- Deterministic fake paper result attribution explains start/non-start behavior from the input `DecisionResult` mode/status without changing fake paper start eligibility.
- Paper PnL explanation copies existing `DecisionResult` expected funding, total fees, simulated roundtrip cost, and net profit when present; missing economics remain missing and do not become zero.
- One fake paper `Capture` represents one funding settlement opportunity.
- Append-only ledger event contracts and helpers live in `core/accounting/ledger.py`.
- Existing `paper_capture_opened` and `paper_rejection_recorded` ledger events may carry optional paper-result explanation payloads; reconciliation validates their shape and fails closed on contradictory well-formed explanation fields without replaying profitability.
- Deterministic offline funding settlement verifier lives in `core/monitoring/funding_settlement.py`.
- Approval-gated funding settlement verification also lives in `core/monitoring/funding_settlement.py` and reuses canonical funding settlement replay for one existing Capture, route, and explicit settlement timestamp.
- Funding settlement evidence recorded through `core/accounting/ledger.py` now requires explicit `approval_granted` evidence; canonical replay requires `approval_granted=True`, `observed_at == settlement_time`, and actual funding/notional values with `ValueSource.OBSERVED`.
- Deterministic offline ledger reconciliation lives in `core/accounting/reconciliation.py`.
- Ledger reconciliation records checked `event_count` and `last_sequence`, and `is_ledger_explicitly_reconciled(ledger.records())` returns true only for the exact current append-only history.
- Deterministic fake CapturePlan freshness evidence lives in `core/domain/contracts.py` as `CapturePlanFreshnessEvidence`.
- Deterministic fake execution capability evidence lives in `core/domain/contracts.py` as `ExecutionCapabilityEvidence`.
- CapturePlan freshness gating lives in `core/risk/gates.py`.
- Missing, stale, duplicated, future-dated, cross-capture, cross-route, cross-settlement, malformed, or unknown-source fake plan evidence fails closed with `RejectReason.CAPTURE_PLAN_NOT_FRESH`.
- Execution capability gating lives in `core/risk/gates.py`.
- Missing, stale, future-dated, cross-capture, cross-route, cross-settlement, malformed, non-orderbook-source, missing-side, wrong-side, wrong-target-notional, partial-fill, or contradictory fake execution capability evidence fails closed through existing centralized reject reasons.
- Deterministic fake live gate evidence bundle lives in `core/domain/contracts.py` as `LiveGateEvidenceBundle`.
- Live gate evidence bundle checking lives in `core/risk/gates.py`.
- Missing, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale/missing CapturePlan evidence, or stale/missing/non-executable execution evidence in a fake bundle fails closed through existing centralized reject reasons.
- Deterministic fake live gate evidence bundle check recording lives in `core/accounting/ledger.py` as `live_gate_evidence_bundle_recorded`.
- Deterministic fake live gate evidence bundle check replay lives in `core/accounting/reconciliation.py` as `replay_live_gate_evidence_bundle_recording()`.
- Missing, duplicated, stale, malformed, or contradictory bundle ledger evidence fails closed, and the replayed recorded outcome must match `core/risk/gates.py`.
- Ledger reconciliation fails closed over any current `live_gate_evidence_bundle_recorded` event that does not replay successfully through `replay_live_gate_evidence_bundle_recording()`.
- Appending bundle-check evidence after successful reconciliation makes the full ledger history unreconciled until a new reconciliation event covers the append.
- SQLite persistence replay coverage proves valid, malformed, and contradictory `live_gate_evidence_bundle_recorded` payloads round-trip through `storage/sqlite/ledger.py` with the same replay outcomes as in-memory ledger records.
- SQLite reopen append-continuity coverage proves append sequences continue across close/reopen boundaries, later persisted appends make prior reconciliation stale, and later reconciliation over reopened records replays deterministically.
- SQLite reopen fail-closed coverage proves malformed, stale, or contradictory persisted appends after reopening remain unreconciled after SQLite round-trip and keep the helper-derived explicit reconciliation gate false.
- Future live gating now checks live trading switch, explicit ledger reconciliation, verified funding settlement, CapturePlan freshness evidence, execution capability evidence, and then the still-unimplemented live gates when a fake bundle is supplied.
- `evaluate_route()` may receive fake freshness evidence, execution-capability evidence, or a fake live gate evidence bundle but still does not read ledger/storage directly, create live `CapturePlan` objects, import execution/live runner modules, place orders, or return `LIVE_ELIGIBLE`.
- In-memory Broad Scan to Focused Refresh handoff using existing `RouteCandidate` contracts.
- Per-venue `VenueObservation` input contract.
- Source-aware fees and funding.
- Route/snapshot alignment.
- Route/snapshot alignment fails closed when RiseX and hedge funding settlement timestamps differ, so one eligible route snapshot represents exactly one funding settlement opportunity.
- Full-target order-book VWAP executability.
- Unknown economics fail closed.
- Live `CapturePlan` creation blocked.
- One read-only RiseX public market-data adapter exists in `core/venues/risex.py`.
- One read-only Hyperliquid public market-data adapter exists in `core/venues/hyperliquid.py`.
- One real market-data route snapshot handoff exists in `core/pipeline/snapshot.py` and delegates to `assemble_route_snapshot()` for one existing route at a time.
- One real-data research runner exists in `apps/research_runner/real_data.py` and evaluates one explicit existing route at a time through the existing adapter handoff and `evaluate_route()` path.
- One approval-gated funding settlement verification workflow exists in `core/monitoring/funding_settlement.py`; it records explicit caller-supplied observed settlement evidence through the existing ledger helper and does not call `evaluate_route()`, assemble snapshots, calculate profitability, reconcile ledgers, plan execution, place orders, or enable live trading.
- One non-sending execution planning workflow exists in `core/execution/planning.py`; it consumes existing Capture, RouteCandidate, route decision, funding verification, ledger reconciliation, CapturePlan freshness, and execution-capability evidence and returns evidence-only intended entry/unwind actions without ledger writes, adapters, live runner behavior, sendable API requests, orders, route eligibility mutation, or live trading.
- One guarded no-order live runner workflow exists in `apps/live_runner/guarded.py`; it consumes existing Capture, RouteCandidate, funding verification, ledger reconciliation, live-gate bundle, and non-sending execution-plan evidence and returns only blocked or no-order readiness without ledger writes, adapters, order placement imports, sendable API requests, route eligibility mutation, or live trading by default.
- One explicit approval-gated order placement boundary exists in `core/execution/orders.py`; it consumes exact current Capture, RouteCandidate, guarded readiness timestamp, non-sending execution plan, explicit approval evidence, explicit ProductRules, and an injected deterministic boundary. `apps/live_runner/order_placement.py` validates exact `GuardedLiveRunnerResult` values before delegation. Missing, stale, false, malformed, cross-identity, disabled-live, non-ready, or stale-plan evidence fails closed before the injected boundary is invoked.
- One read-only monitoring dashboard renderer exists in `apps/dashboard/read_only.py`; it consumes one existing Capture, one existing RouteCandidate, one explicit settlement timestamp, and already-derived caller-supplied fixture evidence only. Missing, malformed, stale, cross-identity, unverified, unreconciled, non-ready, false approval, stale approval, and boundary-blocked inputs render as missing or blocked display state without recomputing product decisions or invoking owner workflows.
- No paper exchange simulation, real exchange order submission, or live trading by default.

## Current repository governance status

- Non-trivial architecture-sensitive tasks require a supervised worker/subagent before implementation edits.
- Architecture-sensitive work includes live-gate, accounting, reconciliation, execution-boundary, ledger, safety-critical, broad contract, owner-boundary, and repository-governance tasks.
- Worker use remains optional for docs-only, metadata-only, tiny fix, or mechanical validation tasks when they are not non-trivial architecture-sensitive work.
- Required workers must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering; workers must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT when they continue beyond design support.
- Parent Codex owns steering, final diff review, validation, commit, push, and final report. Workers must not commit, push, merge, approve work, or start unrelated scope.
- If a required worker is unavailable, skips checkpoints, continues after being stopped, or drifts into forbidden scope, Parent Codex must stop or steer before accepting worker output.
- After RX-033 reviewer acceptance, Control Tower may autonomously select, create, run, coordinate review/fixes for, and finalize future non-dangerous RX tasks from source-of-truth repository docs without asking the user to name each next task.
- Control Tower autonomy remains limited to one RX task at a time, one clean executor task, one task branch, source-of-truth repository docs, Parent ownership, worker checkpoint requirements, exactly-one-task `NEXT_TASK.md`, and explicit reviewer acceptance.
- Control Tower must stop for explicit user approval before selecting, creating, running, fixing, or finalizing any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- Accepted offline safety-hardening work is guardrail evidence, not permission to keep adding speculative scaffolding.
- Future roadmap stages are gated and must be promoted through `NEXT_TASK.md` one task at a time before implementation.
- RX-020 keeps `RouteCandidate` as the authoritative route identity and selected-notional construction contract. Empty or non-string identity fields, invalid or non-opposing entry sides, and non-`Decimal`, non-finite, zero, or negative target notionals fail closed at construction. Positive target notionals below `MIN_LEG_NOTIONAL_USD` continue to fail through the existing minimum-notional route evaluation gate.

## Current roadmap status

- RX-008 through RX-016 are accepted fail-closed offline safety-hardening detour tasks.
- RX-032 is reviewer-accepted and finalized on `main`; it records Product Owner authorization, as narrowed by Control Tower, for exactly one next governance/docs task that may change workflow autonomy for future non-dangerous RX tasks.
- RX-022 is reviewer-accepted and finalized on `main`.
- RX-023 is reviewer-accepted and finalized on `main`.
- RX-024 is reviewer-accepted and finalized on `main`.
- RX-025 is reviewer-accepted and finalized on `main`.
- RX-026 is reviewer-accepted and finalized on `main`.
- RX-027 is reviewer-accepted and finalized on `main`.
- RX-028 is reviewer-accepted and finalized on `main`.
- RX-029 is reviewer-accepted and finalized on `main`.
- RX-030 is reviewer-accepted and finalized on `main`.
- RX-031 is reviewer-accepted and finalized on `main`.
- RX-032 is reviewer-accepted and finalized on `main`.
- RX-033 is reviewer-accepted and finalized on `main`.
- RX-034 is reviewer-accepted and finalized on `main`.
- RX-035 is implementation-complete on `task/rx-035-post-rx-034-roadmap-handoff-cleanup` and pending reviewer acceptance.
- The next recommended task is RX-036 Roadmap Source-of-Truth Clarification Gate.
- The RX-032 authorization does not permit live trading, adapters, private endpoints, credentials, account-state access, sendable exchange requests, order placement, destructive resets, unsafe scope, or financially dangerous actions without explicit user approval.
- RX-033 autonomy does not permit live trading, adapters, private endpoints, credentials, account-state access, sendable exchange requests, order placement, destructive resets, unsafe scope, or financially dangerous actions without explicit user approval.
- A future roadmap stage is not permission to implement live trading, adapters, network calls, execution planning, monitoring, dashboards, or orders before that exact task is authorized and accepted.

## Tests last reported for RX-035 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `37 passed`
- `python3 -m pytest`: `560 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0
- `git status --short`: `M DECISIONS.md`; `M IMPLEMENTATION_PLAN.md`; `M NEXT_TASK.md`; `M STATUS.md`

## Tests last reported for RX-034 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `37 passed in 0.25s`
- `python3 -m pytest`: `560 passed in 0.85s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0
- `git status --short`: empty after commit and push

## Tests last reported for RX-034 finalization on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `37 passed in 0.23s`
- `python3 -m pytest`: `560 passed in 0.75s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-032 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `37 passed in 0.26s`
- `python3 -m pytest`: `560 passed in 0.86s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0
- `git status --short`: `M DECISIONS.md`; `M IMPLEMENTATION_PLAN.md`; `M NEXT_TASK.md`; `M STATUS.md`

## Tests last reported for RX-033 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `37 passed in 0.24s`
- `python3 -m pytest`: `560 passed in 0.77s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0
- `git status --short`: `M AGENTS.md`; `M DECISIONS.md`; `M IMPLEMENTATION_PLAN.md`; `M NEXT_TASK.md`; `M STATUS.md`; `M docs/WORKFLOW.md`; `M docs/templates/REVIEW_CHECKLIST.md`; `M docs/templates/RX_TASK_TEMPLATE.md`

## Tests last reported for RX-033 finalization on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `37 passed in 0.24s`
- `python3 -m pytest`: `560 passed in 0.76s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-032 finalization on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `37 passed in 0.26s`
- `python3 -m pytest`: `560 passed in 0.82s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`

## Tests last reported for RX-031 finalization on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `37 passed in 0.27s`
- `python3 -m pytest`: `560 passed in 0.86s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0

## Tests last reported for RX-031 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `37 passed`
- `python3 -m pytest`: `560 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-030 finalization on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/unit/test_read_only_dashboard.py`: `8 passed in 0.05s`
- `python3 -m pytest tests/invariant`: `37 passed in 0.26s`
- `python3 -m pytest`: `560 passed in 0.77s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-029 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `36 passed in 0.24s`
- `python3 -m pytest tests/unit/test_approval_gated_order_placement.py`: `45 passed in 0.09s`
- `python3 -m pytest`: `551 passed in 0.82s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-029 finalization on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest`: `551 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-028 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `36 passed in 0.24s`
- `python3 -m pytest tests/unit/test_guarded_live_runner.py`: `39 passed in 0.08s`
- `python3 -m pytest`: `506 passed in 0.77s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-028 finalization on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest`: `506 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-027 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/unit/test_execution_planning.py`: `49 passed in 0.07s`
- `python3 -m pytest tests/invariant`: `36 passed in 0.20s`
- `python3 -m pytest`: `467 passed in 0.62s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-027 finalization on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `python3 -m pytest`: `467 passed`
- `python3 -m compileall apps core storage tests`: exit 0
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-026 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `36 passed in 0.21s`
- `python3 -m pytest tests/replay/test_funding_settlement_verifier.py`: `21 passed in 0.07s`
- `python3 -m pytest tests/replay/test_ledger_reconciliation.py tests/replay/test_live_gate_evidence_bundle.py tests/replay/test_capture_plan_freshness.py tests/replay/test_execution_capability.py`: `73 passed in 0.37s`
- `python3 -m pytest`: `418 passed in 0.63s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-026 finalization on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `python3 -m pytest`: `418 passed`
- `python3 -m compileall apps core storage tests`: exit 0
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-025 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `36 passed in 0.23s`
- `python3 -m pytest tests/unit/test_real_data_research_runner.py`: `7 passed in 0.02s`
- `python3 -m pytest`: `412 passed in 0.59s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-025 finalization on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest`: `412 passed in 0.58s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-024 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `36 passed`
- `python3 -m pytest tests/unit/test_snapshot_assembly.py`: `23 passed`
- `python3 -m pytest`: `405 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-011

- `python3 -m apps.cli.main`: exit 0
- `python3 -m pytest`: `222 passed in 0.37s`
- `python3 -m compileall apps core storage tests`: exit 0
- `python3 -c "import core.monitoring.funding_settlement; import core.accounting.reconciliation"`: exit 0
- `python3 -c "from core.monitoring.funding_settlement import replay_funding_settlement_verification; from core.accounting.reconciliation import replay_ledger_reconciliation"`: exit 0
- targeted pytest: `37 passed in 0.08s`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-Q001

- `python scripts/validate_next_task.py`: `NEXT_TASK.md: OK` under login `bash`; default `zsh` has no `python` command
- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `32 passed`
- `python3 -m pytest`: `234 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-012 on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `33 passed in 0.14s`
- `python3 -m pytest`: `255 passed in 0.38s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-Q002 on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest`: `255 passed in 0.41s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-013 on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/replay/test_live_gate_evidence_bundle.py tests/replay/test_ledger_reconciliation.py tests/invariant/test_economics_boundaries.py`: `56 passed`
- `python3 -m pytest`: `264 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-014 on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `33 passed`
- `python3 -m pytest`: `268 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-015 on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `33 passed`
- `python3 -m pytest`: `270 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-016 on main

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `33 passed`
- `python3 -m pytest tests/replay/test_ledger_reconciliation.py`: `34 passed`
- `python3 -m pytest`: `273 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-018 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `33 passed`
- `python3 -m pytest tests/unit/test_risk_gates.py tests/unit/test_evaluate_route.py tests/unit/test_snapshot_assembly.py`: `78 passed`
- `python3 -m pytest`: `278 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for completed RX-019 metadata follow-up

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `33 passed`
- `python3 -m pytest`: `278 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-Q004 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `33 passed`
- `python3 -m pytest`: `278 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-020 branch

- `python3 -m pytest tests/unit/test_route_candidate_contract.py tests/unit/test_evaluate_route.py tests/unit/test_snapshot_assembly.py tests/unit/test_risk_gates.py`: `117 passed in 0.09s`
- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `33 passed in 0.18s`
- `python3 -m pytest`: `317 passed in 0.60s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-021 branch

- `python3 -m pytest tests/unit/test_paper_runner_lifecycle.py tests/unit/test_ledger.py tests/replay/test_ledger_reconciliation.py`: `51 passed in 0.28s`
- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `33 passed in 0.18s`
- `python3 -m pytest`: `320 passed in 0.61s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-023 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `35 passed`
- `python3 -m pytest tests/unit/test_hyperliquid_adapter.py`: `41 passed`
- `python3 -m pytest`: `397 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Known limitations

- Funding settlement verifier, ledger reconciliation, and CapturePlan freshness remain deterministic offline replay scaffolding only.
- Approval-gated funding settlement verification consumes only explicit caller/test-supplied observed settlement evidence; it does not poll venues, read private account state, reconcile ledgers, mutate route eligibility, plan execution, place orders, or enable live trading.
- Execution capability remains deterministic fake offline gate scaffolding only.
- Live gate evidence bundle remains deterministic fake offline gate scaffolding only.
- Live gate evidence bundle ledger recording remains deterministic fake offline accounting scaffolding only.
- Non-sending execution plans are evidence-only descriptions, are not ledger-recorded in RX-027, and do not contain credentials, account state, private endpoint payloads, sendable order requests, or order placement permission.
- Approval-gated order placement remains a deterministic injected boundary only; it does not submit real exchange orders, read account state, create exchange request payloads, use credentials, or enable live trading by default.
- The read-only dashboard renderer consumes caller-supplied deterministic evidence only; it does not poll venues, read ledger/storage state, run verification/reconciliation, plan execution, run guarded readiness, invoke approval boundaries, or place orders.
- CapturePlan freshness evidence is not executable live order planning.
- Execution capability evidence is not executable live order planning.
- Live gate evidence bundle is not executable live order planning.
- RiseX adapter is read-only public market data only and is wired only through the one-route real-data research runner when a caller explicitly supplies it.
- Hyperliquid adapter is read-only public market data only and is wired only through the one-route real-data research runner when a caller explicitly supplies it.
- Current public real adapters still return `UNKNOWN` funding and fee cash-flow values, so real public-adapter research decisions are expected to fail closed as missing live data until a future task supplies approved source-aware economics.
- Offline fake runners still perform no network calls.
- The real-data research runner has no CLI command in this branch; existing fake CLI behavior is unchanged.
- No real exchange order submission.
- No automatic order-placing live runner behavior.
- No live trading by default.
- No live `CapturePlan` creation.
- Fresh CapturePlan evidence is not permission to trade live by itself.
- Approval-gated verified settlement evidence is not permission to trade live by itself.
- Fresh execution capability evidence is not permission to trade live by itself.
- Exact fake live gate evidence bundle is not permission to trade live by itself.
- Replayed successful fake live gate evidence bundle ledger recording is not permission to trade live by itself.
- SQLite persistence replay coverage is deterministic offline test coverage only.
- SQLite reopen append-continuity replay coverage is deterministic offline test coverage only.
- SQLite reopen fail-closed replay coverage is deterministic offline test coverage only.
- Paper result attribution and PnL explanation are deterministic fake offline reporting only; they copy existing `DecisionResult` economics and do not verify realized PnL.
- RX-031 did not discover any external reviewer feedback beyond local repo/git evidence and the GitHub connector's available PR/commit context. Any out-of-band reviewer direction must be supplied explicitly in a future handoff.
- RX-033 is governance/docs-only. It changes repository task-selection workflow after reviewer acceptance, but it does not change product/runtime behavior, remove reviewer acceptance, or weaken hard approval gates.
- RX-034 is governance/docs-only. It selects no product/runtime implementation task because the source-of-truth docs do not clearly ground one after RX-034; it prepares a metadata-only RX-035 cleanup handoff instead.
- RX-035 is governance/docs-only. It re-confirms that the source-of-truth docs still do not clearly ground a concrete product/runtime implementation task after RX-034 and prepares a metadata-only RX-036 clarification handoff instead.

## Next recommended task

RX-036 — Roadmap Source-of-Truth Clarification Gate.
