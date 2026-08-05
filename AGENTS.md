# AGENTS.md

This repository is the source of truth for RiseX Points Farmer implementation work.

## Operating rules

- One Codex session equals one RX task.
- Work only on the task branch requested for that RX task.
- Before changing files, check repository, branch, HEAD, and git status.
- Do not overwrite uncommitted user changes.
- Read this file plus `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md` before implementing.
- Update `STATUS.md` and `NEXT_TASK.md` at the end of each task.
- Update `DECISIONS.md` when the task makes or changes an architectural decision.

## Hard prohibitions

- Do not add real API keys, secrets, or production credentials.
- Do not enable live trading by default.
- Do not place live orders unless a future task explicitly enables a safe live path.
- Do not create `CANARY_ELIGIBLE` or a separate `canary_runner` architecture.
- Do not use `expected_basis_change` as a future basis prediction.
- Do not add arbitrary max spread, max price impact, max levels consumed, hidden conservative buffers, or hidden safety margins.

## Architecture boundaries

- Modular monolith only, not microservices.
- Capture-centric and contract-centric architecture.
- One `Capture` represents one funding settlement opportunity.
- One shared route decision pipeline: `core/pipeline/evaluate.py`.
- Fees logic belongs only in `core/economics/fees.py`.
- Funding logic belongs only in `core/economics/funding.py`.
- Liquidity/VWAP logic belongs only in `core/economics/liquidity.py`.
- Basis/unwind tracking belongs only in `core/economics/basis.py`.
- EV logic belongs only in `core/economics/ev.py`.
- Risk gates belong only in `core/risk/gates.py`.
- Order sending belongs only in `core/execution/`.
- Ledger writes belong only in `core/accounting/ledger.py`.
- Venue adapters may fetch and normalize data only.

## Required report format

Return final RX task reports in one fenced Markdown code block for one-click copy.
The report must have no extra prose outside the code block.

End every RX task with:

- Task ID
- Branch
- Starting HEAD
- Final HEAD
- Changed files
- What was implemented
- Tests run
- Test results
- Known limitations
- Risk impact
- Next suggested task
