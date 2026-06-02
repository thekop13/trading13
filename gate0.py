# ============================================================
#  studies/gate0.py — Gate 0: does a real edge exist?
#  Model-free tests BEFORE any backtest (so KPIs can't fool you).
#
#  Tests:
#    1) IC          — Spearman corr(signal, forward return)
#    2) Conditional — E[r | +1] vs E[r | 0] vs E[r | -1] monotonic?
#    3) Incremental — does the signal beat a simpler baseline?
#    4) Permutation — does IC beat chance? (block-shuffle null)
#    5) Regime      — is the effect's sign stable across bull/bear/sideways?
#
#  Add your strategy as a SIGNALS entry, then run:
#    python -m studies.gate0 --signal above_sma200
# ============================================================
import warnings; warnings.filterwarnings("ignore")
import sys
import numpy as np
import pandas as pd
import yfinance as yf

# ── EDIT THESE ──────────────────────────────────────────────
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA",
           "JPM", "XOM", "JNJ", "PG", "KO", "WMT"]
START = "2018-01-01"
HOLD = 20                       # forward-return horizon (trading days)
PRE_REG = {                     # pre-register BEFORE looking at results
    "ic_min": 0.02,
    "perm_pctile": 95,
    "regimes_pass": 2,
    "incremental_min": 0.0,
    "expect_sign": "+",
}


# ============================================================
#  SIGNALS — define +1/0/-1 states (model-free). Add your own.
#  A signal returns a Series aligned to `close`.
# ============================================================
def sma_state(close, win):
    sma = close.rolling(win).mean()
    return (close > sma).astype(int) - (close < sma).astype(int)


def trend_state(close, win):
    """+1 if price>SMA and SMA rising; -1 if price<SMA and falling; else 0."""
    sma = close.rolling(win).mean()
    above = (close > sma).astype(int) - (close < sma).astype(int)
    slope = np.sign(sma.diff(5)).fillna(0)
    s = pd.Series(0, index=close.index)
    s[(above > 0) & (slope > 0)] = 1
    s[(above < 0) & (slope < 0)] = -1
    return s


SIGNALS = {
    # name: (signal_fn, [baseline names it must beat])
    "above_sma200": (lambda c: sma_state(c, 200), []),
    "trend_sma200": (lambda c: trend_state(c, 200), ["above_sma200"]),
}
BASELINE_FNS = {
    "above_sma200": lambda c: sma_state(c, 200),
}


# ============================================================
#  Data
# ============================================================
def load_panel(tickers, start):
    px = yf.download(tickers, start=start, auto_adjust=True, progress=False)["Close"]
    if isinstance(px, pd.Series):
        px = px.to_frame()
    px = px.dropna(how="all").sort_index()
    if px.empty:
        raise SystemExit(
            "  could not download price data (empty result).\n"
            "  - check your internet connection / ticker symbols\n"
            "  - if behind a firewall, allow query1/query2.finance.yahoo.com")
    print(f"  loaded {px.shape[1]} tickers | {px.index[0].date()} -> {px.index[-1].date()} "
          f"({len(px)} days)")
    return px


def build(px, sig_fn, baseline_names):
    rows = []
    for t in px.columns:
        c = px[t].dropna()
        if len(c) < 260 + HOLD:
            continue
        d = {"sig": sig_fn(c)}
        for b in baseline_names:
            d[b] = BASELINE_FNS[b](c)
        d["fwd"] = c.shift(-HOLD) / c - 1.0
        rows.append(pd.DataFrame(d).dropna())
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


# ============================================================
#  Tests
# ============================================================
def ic(sig, fwd):
    m = sig.notna() & fwd.notna()
    if m.sum() < 50 or sig[m].nunique() < 2:
        return 0.0
    return float(sig[m].rank().corr(fwd[m].rank()))


def conditional(feat):
    up = feat.loc[feat["sig"] == 1, "fwd"].mean()
    flat = feat.loc[feat["sig"] == 0, "fwd"].mean()
    dn = feat.loc[feat["sig"] == -1, "fwd"].mean()
    return up, flat, dn, bool(up > flat > dn)


def incremental(feat, baseline_names):
    s = abs(ic(feat["sig"], feat["fwd"]))
    base = {b: abs(ic(feat[b], feat["fwd"])) for b in baseline_names}
    best = max(base.values()) if base else 0.0
    return s, base, best, s - best


def permutation(feat, n=500, block=HOLD):
    real = abs(ic(feat["sig"], feat["fwd"]))
    fwd = feat["fwd"].values.copy()
    sig = feat["sig"]
    rng = np.random.default_rng(42)
    nb = max(1, len(fwd) // block)
    null = []
    for _ in range(n):
        idx = rng.permutation(nb)
        sh = np.concatenate([fwd[i * block:(i + 1) * block] for i in idx])
        sh = np.resize(sh, len(fwd))
        null.append(abs(ic(sig, pd.Series(sh, index=feat.index))))
    null = np.array(null)
    return real, float(np.percentile(null, 95)), float((real > null).mean() * 100)


def regime(px, sig_fn):
    eq = px.mean(axis=1)
    trend = eq.rolling(200).mean().diff(20)
    reg = pd.Series(np.where(trend > 0, "bull", np.where(trend < 0, "bear", "side")),
                    index=eq.index)
    buckets = {"bull": [], "bear": [], "side": []}
    for t in px.columns:
        c = px[t].dropna()
        if len(c) < 260 + HOLD:
            continue
        sig = sig_fn(c)
        fwd = c.shift(-HOLD) / c - 1.0
        r = reg.reindex(c.index)
        for g in buckets:
            buckets[g].append((sig[r == g], fwd[r == g]))
    out = {}
    for g, pairs in buckets.items():
        s = pd.concat([p[0] for p in pairs]) if pairs else pd.Series(dtype=float)
        f = pd.concat([p[1] for p in pairs]) if pairs else pd.Series(dtype=float)
        out[g] = round(ic(s, f), 4)
    return out


# ============================================================
#  Run
# ============================================================
def run(signal="above_sma200"):
    if signal not in SIGNALS:
        print(f"  unknown signal '{signal}' — available: {list(SIGNALS)}")
        return
    sig_fn, baselines = SIGNALS[signal]
    print("=" * 56)
    print(f"  Gate 0 — Thesis Validation: signal = '{signal}'")
    print("=" * 56)
    px = load_panel(TICKERS, START)
    feat = build(px, sig_fn, baselines)
    if feat.empty:
        print("  not enough data")
        return

    the_ic = ic(feat["sig"], feat["fwd"])
    up, flat, dn, mono = conditional(feat)
    s_ic, base, best, edge = incremental(feat, baselines)
    p_real, p95, beat = permutation(feat)
    reg = regime(px, sig_fn)

    print(f"\n  n_obs = {len(feat):,} | horizon = {HOLD}d")
    print(f"  1) IC                 : {the_ic:+.4f}")
    print(f"  2) E[r] up/flat/down  : {up:+.4f} / {flat:+.4f} / {dn:+.4f}"
          f"  {'(monotonic)' if mono else '(not monotonic)'}")
    print(f"  3) signal vs baseline : {s_ic:.4f} / best {best:.4f}  edge {edge:+.4f}  {base}")
    print(f"  4) permutation        : IC {p_real:.4f} beats null {beat:.1f}% (p95 {p95:.4f})")
    print(f"  5) regime IC          : {reg}")

    sign = 1 if PRE_REG["expect_sign"] == "+" else -1
    n_reg = sum(1 for v in reg.values() if np.sign(v) == sign and v != 0)
    checks = [
        (abs(the_ic) >= PRE_REG["ic_min"] and np.sign(the_ic) == sign,
         f"|IC| >= {PRE_REG['ic_min']} ({PRE_REG['expect_sign']})"),
        (beat >= PRE_REG["perm_pctile"], f"beat null >= {PRE_REG['perm_pctile']}%"),
        (edge > PRE_REG["incremental_min"], f"edge over baseline > {PRE_REG['incremental_min']}"),
        (n_reg >= PRE_REG["regimes_pass"], f"regimes on-side >= {PRE_REG['regimes_pass']}"),
    ]
    print("\n  " + "-" * 50)
    for ok, label in checks:
        print(f"  {'✓' if ok else '✗'} {label}")
    print("  " + "-" * 50)
    passed = all(ok for ok, _ in checks)
    print(f"  Gate 0: {'✅ PASS — allowed to backtest (Gate 1)' if passed else '❌ FAIL — drop or fix the thesis'}")
    return passed


if __name__ == "__main__":
    sig = "above_sma200"
    if "--signal" in sys.argv:
        i = sys.argv.index("--signal")
        if i + 1 < len(sys.argv):
            sig = sys.argv[i + 1]
    run(sig)
