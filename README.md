# RiseX Points Farmer

RiseX Points Farmer is a modular-monolith research system for capture-centric hedged funding opportunities on RiseX with hedge venue support, initially Hyperliquid.

The current baseline is a non-trading research and fake paper-lifecycle skeleton. It uses fake data, does not connect to exchanges, does not place orders, and does not contain real API keys.

## Product baseline

- Main strategy: hedged funding capture on RiseX with hedge venue support.
- One `Capture` equals one funding settlement opportunity.
- Points value, expected airdrop value, leaderboard rewards in base PnL, and unreceived rebates are all explicitly zero.
- `MIN_LEG_NOTIONAL_USD = 500`.
- `MIN_NET_PROFIT_USD = 1`.
- Live trading is disabled by default.
- Route statuses are `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `LIVE_ELIGIBLE`, and `REJECTED`.
- `CANARY_ELIGIBLE` and a separate canary runner are forbidden.

## Offline research runner

The fake runner builds multiple `RouteCandidate` values and normalized `VenueObservation` inputs. It runs deterministic Broad Scan followed by Focused Refresh. Both stages reuse the RX-005 offline orchestration path: each successful candidate assembles a route snapshot through the single `assemble_route_snapshot()` path and evaluates through the single `evaluate_route()` decision pipeline.

```bash
python -m apps.cli.main
pytest
```

## Offline paper runner

The fake paper runner is downstream of route decisions. It consumes existing `DecisionResult` values, starts fake capture execution only for `PAPER_ELIGIBLE` decisions, and records non-started decisions as paper rejections. It does not recalculate profitability, assemble snapshots, place orders, import the live runner, or create `CapturePlan` objects.

Paper history is written through `core/accounting/ledger.py` as append-only events. `storage/sqlite/ledger.py` is a minimal deterministic SQLite implementation of the same ledger contract for offline persistence and replay tests.

## Offline funding settlement verifier

The deterministic fake funding settlement verifier is downstream of paper lifecycle and ledger evidence. It models required pre-settlement checkpoints at T-20 minutes, T-60 seconds, T-10 seconds, and T-5 seconds, then replays append-only ledger events to compare fake expected funding/notional inputs with observed fake settlement evidence.

The verifier records evidence and verification results only through `core/accounting/ledger.py`. Missing, unknown, or inconsistent settlement evidence fails closed as not verified. It does not evaluate route profitability, assemble snapshots, calculate EV, place orders, create `CapturePlan` objects, or enable live trading.

## Boundaries

Business logic has single-owner modules:

- fees: `core/economics/fees.py`
- funding: `core/economics/funding.py`
- liquidity/VWAP: `core/economics/liquidity.py`
- basis/unwind tracking: `core/economics/basis.py`
- EV: `core/economics/ev.py`
- risk gates: `core/risk/gates.py`
- route decision: `core/pipeline/evaluate.py`
- orders: `core/execution/`
- ledger writes: `core/accounting/ledger.py`
- funding settlement verification: `core/monitoring/funding_settlement.py`

Venue adapters may fetch and normalize data only. They must not calculate EV, make route decisions, send orders, or write ledger events.
