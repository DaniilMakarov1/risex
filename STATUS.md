# Status

- Last accepted task: RX-002A — Add GitHub CI Workflow
- Accepted baseline RX-002A HEAD: `0ad00d8f7ac9796351d932950c4bd4b4864ebd94`
- Current completed candidate task: RX-003 — Economics Engine: Fees, Funding, VWAP Liquidity, Basis, and Entry EV
- Current branch: task/rx-003-economics-engine
- Starting HEAD for RX-003: `0ad00d8f7ac9796351d932950c4bd4b4864ebd94`
- Starting HEAD for RX-003 FIX: `a53100fc4f45540ccd31769bc867e81d3cc5aa94`
- RX-003 review status: completed candidate awaiting reviewer acceptance
- RX-003 FIX candidate HEAD: final branch HEAD after this status update; exact hash is reported in the task report after commit and push
- Repository state at RX-003 FIX start: clean checkout at `a53100fc4f45540ccd31769bc867e81d3cc5aa94`

## Completed candidate work summary

- Added source-aware order book, executable quote, fee model, and funding snapshot contracts.
- Implemented VWAP from order-book levels for the configured minimum leg notional, including partial final-level consumption and insufficient-liquidity non-executable quotes.
- Implemented fee calculations that accept documented, observed, or user-configured values and reject unknown, invalid default-source, or negative fee inputs.
- Implemented funding calculations that accept documented, observed, or last-observed estimates and reject missing or unsupported funding sources.
- Implemented entry EV from expected funding, source-aware fees, and simulated immediate unwind cost from executable VWAP quotes.
- Implemented current unwind PnL support in the basis module without forecasting future basis.
- Strengthened `evaluate_route()` to fail closed through centralized `RejectReason` values when required economics data is missing.
- Updated fake data and CLI path to use offline order-book VWAP instead of hardcoded fake VWAP shortcuts.
- Added unit, integration, and invariant tests for RX-003 economics contracts and forbidden architecture drift.

## RX-003 FIX summary

- Extended `RouteCandidate` with explicit RiseX venue, RiseX entry side, and hedge entry side.
- Added centralized route/snapshot alignment in `core/risk/gates.py` before Entry EV.
- Enforced route target notional, quote venue, quote symbol, quote side, quote source, and quote-pair consistency before economics math.
- Strengthened roundtrip quote-pair validation in `core/economics/liquidity.py`.
- Added scoped `EconomicsInputError` handling so expected missing economics input fails closed while unexpected programming errors remain visible.
- Removed `CapturePlan` construction from the RX-003 evaluation path; live gates remain unimplemented and profitable ENTRY decisions remain `PAPER_ELIGIBLE`.
- Replaced the cross-venue adapter protocol with a read-only per-venue `fetch_order_book(symbol) -> OrderBook` contract.
- Updated architecture, decisions, implementation plan, status, next-task governance, and tests.

## Latest RX-003 FIX verification

- `python3 -m apps.cli.main`: `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
- `python3 -m pytest`: `89 passed in 0.09s`
- `python3 -m compileall apps core storage tests`: exit 0
- `git diff --check`: exit 0

## Known limitations

- RX-003 is not accepted until reviewer approval.
- Only fake offline data is available.
- No real RiseX or Hyperliquid adapters exist.
- No live order placement exists.
- No persistent SQLite ledger exists yet.
- Funding settlement verification is not implemented.
- Broad Scan and Focused Refresh orchestration is not implemented yet.
- Live eligibility remains blocked by intentionally unimplemented live gates, even if the live trading switch is manually enabled.
- Fee rebates and negative fee modeling are intentionally not implemented in RX-003.
- Current unwind PnL is quote-based and deterministic; it does not persist capture lifecycle or accounting events.

## Next recommended task

RX-004 — Per-Venue Observation and Route Snapshot Contracts
