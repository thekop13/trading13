import json,pytest
import proofs.record as rec_mod
from proofs.record import record
@pytest.fixture(autouse=True)
def patch(tmp_path,monkeypatch):
    p=tmp_path/"ledger.json"; p.write_text(json.dumps({"proofs":[],"fallacies":[]}),encoding="utf-8")
    monkeypatch.setattr(rec_mod,"LEDGER",p); return p
def r(p): return json.loads(p.read_text(encoding="utf-8"))
def test_fail(patch): record(id="P1",name="t",thesis="i",gate0=False); assert r(patch)["proofs"][0]["status"]=="rejected"
def test_g0only(patch): record(id="P2",name="t",thesis="i",gate0=True); assert r(patch)["proofs"][0]["status"]=="gate0_only"
def test_pass(patch): record(id="P3",name="t",thesis="i",gate0=True,gate1=True); assert r(patch)["proofs"][0]["status"]=="passed"
def test_g1fail(patch): record(id="P4",name="t",thesis="i",gate0=True,gate1=False); assert r(patch)["proofs"][0]["status"]=="rejected"
def test_upsert(patch):
    record(id="P5",name="v1",thesis="i",gate0=False); record(id="P5",name="v2",thesis="i",gate0=True,gate1=True)
    e=[p for p in r(patch)["proofs"] if p["id"]=="P5"]; assert len(e)==1 and e[0]["status"]=="passed"
def test_fallacies(patch):
    d=r(patch); d["fallacies"].append({"name":"trap","text":"x","triggers":[]}); patch.write_text(json.dumps(d),encoding="utf-8")
    record(id="P6",name="s",thesis="i",gate0=True); assert any(f["name"]=="trap" for f in r(patch)["fallacies"])
