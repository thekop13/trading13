# ============================================================
#  tests/test_gate0.py
#  Unit tests for Gate 0 analytics (synthetic data, no network).
# ============================================================
import numpy as np
import pandas as pd
import pytest

from studies.gate0 import ic, conditional, incremental, permutation, sma_state


def make_feat(n=500, seed=0):
    """Signal positively correlated with forward return."""
    rng = np.random.default_rng(seed)
    sig = pd.Series(rng.choice([-1, 0, 1], size=n))
    fwd = sig * 0.01 + rng.normal(0, 0.005, n)
    return pd.DataFrame({"sig": sig, "fwd": pd.Series(fwd)})


def make_feat_noise(n=500, seed=1):
    """Signal uncorrelated with forward return."""
    rng = np.random.default_rng(seed)
    sig = pd.Series(rng.choice([-1, 0, 1], size=n))
    fwd = pd.Series(rng.normal(0, 0.01, n))
    return pd.DataFrame({"sig": sig, "fwd": fwd})


# ---- ic -----------------------------------------------------

def test_ic_positive_signal():
    val = ic(make_feat()["sig"], make_feat()["fwd"])
    assert val > 0.30


def test_ic_noise_near_zero():
    feat = make_feat_noise()
    assert abs(ic(feat["sig"], feat["fwd"])) < 0.15


def test_ic_too_few_obs():
    assert ic(pd.Series([1, -1, 1]), pd.Series([0.01, -0.01, 0.01])) == 0.0


def test_ic_constant_signal():
    assert ic(pd.Series([1] * 200), pd.Series(np.random.randn(200))) == 0.0


# ---- conditional --------------------------------------------

def test_conditional_monotonic():
    _, _, _, mono = conditional(make_feat(n=2000))
    assert mono


def test_conditional_returns_bool():
    _, _, _, mono = conditional(make_feat_noise(n=2000, seed=99))
    assert isinstance(mono, bool)


# ---- incremental --------------------------------------------

def test_incremental_no_baselines():
    feat = make_feat()
    s, base, best, edge = incremental(feat, [])
    assert best == 0.0 and edge == s


def test_incremental_signal_nonnegative():
    rng = np.random.default_rng(7)
    n = 600
    sig = pd.Series(rng.choice([-1, 0, 1], size=n))
    fwd = sig * 0.01 + rng.normal(0, 0.005, n)
    rand = pd.Series(rng.choice([-1, 0, 1], size=n))
    feat = pd.DataFrame({"sig": sig, "fwd": pd.Series(fwd), "rand": rand})
    s, _, _, _ = incremental(feat, ["rand"])
    assert s >= 0


# ---- permutation --------------------------------------------

def test_permutation_strong_signal():
    _, _, beat_pct = permutation(make_feat(n=1000), n=200)
    assert beat_pct > 80


def test_permutation_noise_fails():
    _, _, beat_pct = permutation(make_feat_noise(n=1000), n=200)
    assert beat_pct < 80


# ---- sma_state ----------------------------------------------

def test_sma_state_above():
    price = pd.Series([100.0] * 210 + [110.0] * 10)
    assert sma_state(price, 200).iloc[-1] == 1


def test_sma_state_below():
    price = pd.Series([100.0] * 210 + [90.0] * 10)
    assert sma_state(price, 200).iloc[-1] == -1
