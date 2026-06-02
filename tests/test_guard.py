import json,pytest
import proofs.guard as guard_mod
from proofs.guard import _tokens,_sim,check,report
MINI={"proofs":[{"id":"P0","name":"dead_momentum","thesis":"momentum factor beats market","status":"rejected"}],
      "fallacies":[{"name":"KPI-as-target","text":"Tuning to chase a KPI.","triggers":["best sharpe","maximize"]},
                   {"name":"multiple-testing","text":"Cheering the best.","triggers":["grid","scan parameters"]}]}
@pytest.fixture(autouse=True)
def patch(tmp_path,monkeypatch):
    p=tmp_path/"ledger.json"; p.write_text(json.dumps(MINI),encoding="utf-8")
    monkeypatch.setattr(guard_mod,"LEDGER",p)
def test_tokens(): assert "macd" in _tokens("MACD crossover")
def test_tokens_short(): assert _tokens("go up")==set()
def test_sim_identical(): t=_tokens("momentum factor"); assert _sim(t,t)==1.0
def test_sim_disjoint(): assert _sim({"aaa"},{"bbb"})==0.0
def test_clean(): assert check("go long above 200-day moving average")==[]
def test_warn(): hits=check("let us maximize returns"); assert hits[0]["severity"]=="warn"
def test_block(): hits=check("maximize and get best sharpe"); assert any(h["severity"]=="block" for h in hits)
def test_proof_hit(): hits=check("momentum factor beats market returns"); assert any(h["kind"]=="proof" for h in hits)
def test_pass_emoji(): assert "✅" in report("go long above moving average")
def test_block_emoji(): assert "🛑" in report("maximize and get best sharpe")
def test_sort():
    hits=check("grid maximize best sharpe scan parameters")
    sevs=[h["severity"] for h in hits]
    blocks=[i for i,s in enumerate(sevs) if s=="block"]
    warns=[i for i,s in enumerate(sevs) if s=="warn"]
    if blocks and warns: assert max(blocks)<min(warns)
