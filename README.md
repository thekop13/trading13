# Strategy Testing Starter (with Claude Code)

A small, disciplined harness so you **prove a trading strategy before trusting it** —
instead of fooling yourself with an overfit backtest.

```
guard  →  Gate 0  →  Gate 1  →  ledger
(known   (edge      (survives   (memory of
 traps)   exists?)   costs OOS?)  every try)
```

## Setup
```bash
pip install -r requirements.txt
```

## How to use it with Claude
Open Claude Code in this folder and just describe a strategy in plain language, e.g.:

> "Test this: go long when price is above the 200-day SMA and the SMA is rising.
>  Use 12 US large caps."

Because of `CLAUDE.md`, Claude will:
1. Run the **Fallacy Guard** first (`python -m proofs.guard "..."`)
2. Turn your idea into a signal in `studies/gate0.py`
3. Run **Gate 0** — if no real edge, it stops here (no misleading backtest)
4. Only if Gate 0 passes, run **Gate 1** (walk-forward OOS, costs deducted)
5. Record the result to `proofs/ledger.json`

## Run manually
```bash
python -m proofs.guard "MACD confirmed by RSI"     # check the idea
python -m studies.gate0 --signal above_sma200      # does an edge exist?
python -m studies.gate1 --signal above_sma200      # does it survive costs OOS?
```

## Add your own strategy
Edit `studies/gate0.py` → add to `SIGNALS` a function returning +1/0/-1:
```python
SIGNALS = {
    "my_strategy": (lambda c: my_signal(c), ["above_sma200"]),  # baseline(s) to beat
}
```
Then run gate0 / gate1 with `--signal my_strategy`.

## Why these guards matter
- **Gate 0 before Gate 1** — a backtest on an edgeless idea will still show pretty
  numbers from overfitting. Gate 0 (IC + permutation + regime) catches that early.
- **Out-of-sample only** — tune on the past, judge on the future. Never on the full sample.
- **Costs deducted** — many "winning" strategies die after commission + slippage.
- **Ledger** — Claude forgets between sessions; the ledger is the project's memory.

Customize `CLAUDE.md` (set your language) and `TICKERS`/`START` in `studies/gate0.py`.
