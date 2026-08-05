# RiseX Points Farmer

RiseX Points Farmer is a modular-monolith research system for capture-centric hedged funding opportunities on RiseX with hedge venue support, initially Hyperliquid.

RX-000 is only a non-trading walking skeleton. It uses fake data, does not connect to exchanges, does not place orders, and does not contain real API keys.

## Product baseline

- Main strategy: hedged funding capture on RiseX with hedge venue support.
- One `Capture` equals one funding settlement opportunity.
- Points value, expected airdrop value, leaderboard rewards in base PnL, and unreceived rebates are all explicitly zero.
- `MIN_LEG_NOTIONAL_USD = 500`.
- `MIN_NET_PROFIT_USD = 1`.
- Live trading is disabled by default.
- Route statuses are `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `LIVE_ELIGIBLE`, and `REJECTED`.
- `CANARY_ELIGIBLE` and a separate canary runner are forbidden.

## Walking skeleton

The fake runner builds a `RouteCandidate` and `VenueSnapshot`, evaluates them through the single `evaluate_route()` pipeline, and writes a decision event to an append-only in-memory ledger.

```bash
python -m apps.cli.main
pytest
```

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

Venue adapters may fetch and normalize data only. They must not calculate EV, make route decisions, send orders, or write ledger events.
