# ============================================================
#  tests/test_gate1.py
#  Unit tests for Gate 1 analytics (synthetic data, no network).
# ============================================================
import numpy as np
import pandas as pd
import pytest

from studies.gate1 import metrics, strat_returns


def make_px(n=600, n_tickers=3, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=n, freq="B")
    data = {f"T{i}": 100 * np.cumprod(1 + rng.normal(0.0003, 0.01, n))
            for i in range(n_tickers)}
    return pd.DataFrame(data, index=idx)


def _always_long(close):
    return pd.Series(1, index=close.index)


def _always_flat(close):
    return pd.Series(0, index=close.index)


# ---- metrics ------------------------------------------------

def test_metrics_positive_returns():
    m = metrics(pd.Series([0.001] * 300))
    assert m is not None
    assert m["sharpe"] > 0
    assert m["max_dd"] == 0.0
    assert m["profit_factor"] == float("inf")


def test_metrics_negative_returns():
    m = metrics(pd.Series([-0.001] * 300))
    assert m["sharpe"] < 0 and m["max_dd"] < 0


def test_metrics_too_short():
    assert metrics(pd.Series([0.01] * 10)) is None


def test_metrics_zero_std():
    assert metrics(pd.Series([0.0] * 300)) is None


def test_metrics_hit_rate():
    m = metrics(pd.Series([0.01, -0.01] * 150))
    assert abs(m["hit"] - 0.5) < 0.01


# ---- strat_returns ------------------------------------------

def test_strat_returns_shape():
    px = make_px()
    strat, bh = strat_returns(px, _always_long)
    assert len(strat) == len(bh) == len(px)


def test_strat_always_flat_near_zero():
    strat, _ = strat_returns(make_px(), _always_flat)
    assert strat.abs().sum() < 0.01


def test_strat_no_lookahead():
    strat, _ = strat_returns(make_px(n_tickers=1), _always_long)
    assert strat.iloc[0] == 0.0


def test_strat_empty_on_short_series():
    strat, bh = strat_returns(make_px(n=100, n_tickers=2), _always_long)
    assert strat.empty


def test_strat_both_series_nonzero():
    strat, bh = strat_returns(make_px(seed=42), _always_long)
    assert (1 + strat).cumprod().iloc[-1] > 0
    assert (1 + bh).cumprod().iloc[-1] > 0
