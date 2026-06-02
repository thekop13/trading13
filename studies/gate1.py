# ============================================================
#  studies/gate1.py — Gate 1: does it survive reality?
#  Walk-forward OUT-OF-SAMPLE backtest with realistic costs,
#  compared to buy-and-hold. Only run AFTER Gate 0 passes.
#
#  Long-only by default: hold when signal > 0, flat otherwise.
#  Cost is charged whenever the position changes.
#
#    python -m studies.gate1 --signal above_sma200
# ============================================================
import warnings; warnings.filterwarnings("ignore")
import sys
import numpy as np
import pandas as pd

from studies.gate0 import load_panel, SIGNALS, TICKERS, START

COST = 0.0010        # per side (commission + slippage), 0.10%
ANN = 252
OOS_FRAC = 0.30      # last 30% of the timeline is pure out-of-sample
PASS = {"sharpe_min": 0.8, "profit_factor_min": 1.2, "max_dd_max": 0.35}


def metrics(daily):
    r = daily.dropna()
    if len(r) < 30 or r.std() == 0:
        return None
    eq = (1 + r).cumprod()
    sharpe = r.mean() / r.std() * np.sqrt(ANN)
    dd = (eq / eq.cummax() - 1).min()
    gains, losses = r[r > 0].sum(), -r[r < 0].sum()
    pf = gains / losses if losses > 0 else float("inf")
    cagr = eq.iloc[-1] ** (ANN / len(r)) - 1
    return {"cagr": cagr, "sharpe": sharpe, "max_dd": dd, "profit_factor": pf,
            "hit": float((r > 0).mean()), "n": len(r)}


def strat_returns(px, sig_fn, long_only=True):
    """Equal-weight daily returns across the panel, costs deducted."""
    rets = []
    for t in px.columns:
        c = px[t].dropna()
        if len(c) < 260:
            continue
        sig = sig_fn(c)
        pos = (sig > 0).astype(float) if long_only else np.sign(sig).astype(float)
        pos = pos.shift(1).fillna(0)                 # trade next bar (no look-ahead)
        ret = c.pct_change().fillna(0)
        gross = pos * ret
        cost = pos.diff().abs().fillna(0) * COST
        rets.append(gross - cost)
    if not rets:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    strat = pd.concat(rets, axis=1).mean(axis=1)
    bh = px.pct_change().mean(axis=1)               # equal-weight buy & hold
    return strat, bh


def run(signal="above_sma200"):
    if signal not in SIGNALS:
        print(f"  unknown signal '{signal}' — available: {list(SIGNALS)}")
        return
    sig_fn, _ = SIGNALS[signal]
    print("=" * 56)
    print(f"  Gate 1 — Walk-forward OOS backtest: signal = '{signal}'")
    print(f"  cost = {COST*100:.2f}%/side | OOS = last {int(OOS_FRAC*100)}% of timeline")
    print("=" * 56)
    px = load_panel(TICKERS, START)
    strat, bh = strat_returns(px, sig_fn)
    if strat.empty:
        print("  not enough data")
        return

    split = int(len(strat) * (1 - OOS_FRAC))
    oos_strat, oos_bh = strat.iloc[split:], bh.iloc[split:]
    print(f"  OOS period: {strat.index[split].date()} -> {strat.index[-1].date()}")

    ms, mb = metrics(oos_strat), metrics(oos_bh)
    if not ms:
        print("  not enough OOS data")
        return
    print(f"\n  {'metric':<16}{'strategy':>12}{'buy&hold':>12}")
    for k, label in [("sharpe", "Sharpe"), ("profit_factor", "Profit Factor"),
                     ("max_dd", "Max Drawdown"), ("cagr", "CAGR"), ("hit", "Hit rate")]:
        bv = mb[k] if mb else float("nan")
        print(f"  {label:<16}{ms[k]:>12.2f}{bv:>12.2f}")

    checks = [
        (ms["sharpe"] >= PASS["sharpe_min"], f"Sharpe >= {PASS['sharpe_min']}"),
        (ms["profit_factor"] >= PASS["profit_factor_min"], f"PF >= {PASS['profit_factor_min']}"),
        (abs(ms["max_dd"]) <= PASS["max_dd_max"], f"MaxDD <= {PASS['max_dd_max']:.0%}"),
        (ms["sharpe"] > (mb["sharpe"] if mb else -9), "beats buy&hold (Sharpe)"),
    ]
    print("\n  " + "-" * 50)
    for ok, label in checks:
        print(f"  {'✓' if ok else '✗'} {label}")
    print("  " + "-" * 50)
    passed = all(ok for ok, _ in checks)
    print(f"  Gate 1: {'✅ PASS — candidate for paper trading' if passed else '❌ FAIL — not worth trading after costs'}")
    print("  NOTE: test more universes/periods + add slippage before risking real money.")
    return passed


if __name__ == "__main__":
    sig = "above_sma200"
    if "--signal" in sys.argv:
        i = sys.argv.index("--signal")
        if i + 1 < len(sys.argv):
            sig = sys.argv[i + 1]
    run(sig)
