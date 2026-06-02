# ============================================================
#  tests/test_guard.py
#  Unit tests for the Fallacy Guard (no network required).
# ============================================================
import json
import pytest

import proofs.guard as guard_mod
from proofs.guard import _tokens, _sim, check, report


MINI_LEDGER = {
    "proofs": [
        {"id": "P000", "name": "dead_momentum",
         "thesis": "momentum factor beats market", "status": "rejected"}
    ],
    "fallacies": [
        {"name": "KPI-as-target", "text": "Tuning to chase a KPI.",
         "triggers": ["best sharpe", "maximize"]},
        {"name": "multiple-testing", "text": "Cheering the best of many runs.",
         "triggers": ["grid", "scan parameters"]}
    ]
}


@pytest.fixture(autouse=True)
def patch_ledger(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(json.dumps(MINI_LEDGER), encoding="utf-8")
    monkeypatch.setattr(guard_mod, "LEDGER", ledger_path)


def test_tokens_basic():
    t = _tokens("MACD crossover RSI")
    assert "macd" in t and "crossover" in t and "rsi" in t


def test_tokens_min_length():
    assert _tokens("go up") == set()


def test_sim_identical():
    t = _tokens("momentum factor")
    assert _sim(t, t) == 1.0


def test_sim_disjoint():
    assert _sim({"aaa"}, {"bbb"}) == 0.0


def test_clean_idea_passes():
    assert check("go long above the 200-day moving average") == []


def test_single_trigger_is_warn():
    hits = check("let us maximize returns")
    assert len(hits) == 1
    assert hits[0]["severity"] == "warn"
    assert hits[0]["name"] == "KPI-as-target"


def test_two_triggers_same_fallacy_is_block():
    hits = check("maximize and get best sharpe")
    assert any(h["severity"] == "block" and h["name"] == "KPI-as-target" for h in hits)


def test_rejected_proof_similarity_warn():
    # "dead_momentum" thesis is "momentum factor beats market" — high overlap
    hits = check("momentum factor beats market returns")
    assert any(h["kind"] == "proof" for h in hits)


def test_report_pass_emoji():
    assert "✅" in report("go long above moving average")


def test_report_block_emoji():
    assert "🛑" in report("maximize and get best sharpe")


def test_blocks_sorted_first():
    hits = check("grid maximize best sharpe scan parameters")
    severities = [h["severity"] for h in hits]
    blocks = [i for i, s in enumerate(severities) if s == "block"]
    warns = [i for i, s in enumerate(severities) if s == "warn"]
    if blocks and warns:
        assert max(blocks) < min(warns)
