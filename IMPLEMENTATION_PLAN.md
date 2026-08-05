# Implementation Plan

## RX-000 — Project Constitution and Walking Skeleton Foundation

Create repository docs, structure, Python test setup, minimal domain contracts, fake route evaluation, and append-only ledger tests. No real adapters, no live orders, and no external exchange connectivity.

## RX-001 — Domain Contracts and State Machine

Strengthen domain contracts and introduce the formal state machine for `Capture`, route lifecycle, decision history, and future `CapturePlan` freshness rules.

## Later task themes

- Fee source modeling and user-configured default fee handling.
- Funding estimate source modeling and settlement verifier design.
- VWAP/order-book models for the `$500` target notional.
- Broad Scan and Focused Refresh using the same `evaluate_route()` function.
- Paper runner lifecycle and append-only ledger persistence.
- Dashboard and monitoring snapshots.
- Real venue adapters only after contracts and fake/paper paths are stable.
