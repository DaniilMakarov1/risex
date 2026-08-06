# Status

- Last accepted task: RX-002A — Add GitHub CI Workflow
- Accepted baseline RX-002A HEAD: `0ad00d8f7ac9796351d932950c4bd4b4864ebd94`
- Current completed candidate task: RX-003 — Economics Engine: Fees, Funding, VWAP Liquidity, Basis, and Entry EV
- Current branch: task/rx-003-economics-engine
- Starting HEAD for RX-003: `0ad00d8f7ac9796351d932950c4bd4b4864ebd94`
- Repository state at task start: clean checkout at accepted baseline RX-002A HEAD

## Completed work summary

- Added source-aware order book, executable quote, fee model, and funding snapshot contracts.
- Implemented VWAP from order-book levels for the configured minimum leg notional, including partial final-level consumption and insufficient-liquidity non-executable quotes.
- Implemented fee calculations that accept documented, observed, or user-configured values and reject unknown, invalid default-source, or negative fee inputs.
- Implemented funding calculations that accept documented, observed, or last-observed estimates and reject missing or unsupported funding sources.
- Implemented entry EV from expected funding, source-aware fees, and simulated immediate unwind cost from executable VWAP quotes.
- Implemented current unwind PnL support in the basis module without forecasting future basis.
- Strengthened `evaluate_route()` to fail closed through centralized `RejectReason` values when required economics data is missing.
- Updated fake data and CLI path to use offline order-book VWAP instead of hardcoded fake VWAP shortcuts.
- Added unit, integration, and invariant tests for RX-003 economics contracts and forbidden architecture drift.

## Tests run

- `python3 -m apps.cli.main`
- `python3 -m pytest`
- `python3 -m compileall apps core storage tests`
- `git diff --check`

## Known limitations

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

RX-004 — Broad Scan and Focused Refresh Over Shared `evaluate_route()`
