# CLAUDE.md — Strategy Testing Framework (starter)

Guidance for Claude Code when working in this repository.

> Customize this file for your project. The rules below are what enforce
> *discipline* so you don't fool yourself with overfit backtests.

## Communication language
- Reply to the user in **ไทย**.
- Keep code, variable names, and technical identifiers in English.

## About this project
A disciplined harness for **proving trading strategies before trusting them**:
`proofs/guard.py` (fallacy guard) → `studies/gate0.py` (does an edge exist?) →
`studies/gate1.py` (does it survive costs out-of-sample?) → `proofs/ledger.json`
(institutional memory of every idea tried).

## ⚠️ Fallacy Guard — MANDATORY before any new strategy

**Hard rule:** When the user proposes a new idea/thesis/strategy (or when you
are about to propose one yourself), you **MUST run the Fallacy Guard first**.

Steps before designing/coding a strategy:
1. Run `python -m proofs.guard "<description of the idea>"`
2. If **🛑 block** → STOP and tell the user immediately which past proof/fallacy
   it echoes, and ask "how is this different from before?" — do not write code yet.
3. If **⚠️ warn** → tell the user it's close to a known trap, then design Gate 0
   so it clearly separates from the baseline (e.g. an incremental test).
4. If **✅ pass** → proceed.

Reason: pretty KPIs from overfit lie. A thesis that already failed is a lesson
already paid for — the ledger exists so you don't pay twice.

## The Gate framework — never skip Gate 0

- **Gate 0 (`studies/gate0.py`)** — *Does a real edge exist?* Model-free tests
  (information coefficient, permutation test, regime stability, incremental value
  over a simpler baseline). **No backtest until Gate 0 passes** — otherwise a
  backtest will show deceptive KPIs from overfitting (garbage-in-garbage-out).
- **Gate 1 (`studies/gate1.py`)** — *Does it survive reality?* Walk-forward
  out-of-sample, realistic commission + slippage deducted, compared to buy-and-hold.

## Anti-patterns the guard watches for
- **KPI-as-target** — tuning to chase a KPI. KPIs are fixed rulers, not optimization targets.
- **multiple-testing** — trying many parameter sets and cheering the best one. Pre-register; log every run.
- **redundant-confirmation** — assuming "A must confirm B" without an incremental test.
- **garbage-in-garbage-out** — backtesting before proving the thesis (Gate 0).

## Dev conventions
- Record every tested idea to `proofs/ledger.json` (pass or fail) — it's your memory across sessions.
- Runtime/output files (results, charts) should not be committed.
