import json
from datetime import date
from pathlib import Path
LEDGER = Path(__file__).resolve().parent / "ledger.json"
def _load():
    return json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {"proofs":[],"fallacies":[]}
def record(*, id, name, thesis, gate0, gate1=None, notes=""):
    led=_load()
    status="rejected" if not gate0 or gate1 is False else ("passed" if gate1 else "gate0_only")
    entry={"id":id,"name":name,"thesis":thesis,"date":str(date.today()),
           "gate0":gate0,"gate1":gate1,"status":status,"notes":notes}
    led["proofs"]=[p for p in led["proofs"] if p.get("id")!=id]
    led["proofs"].append(entry)
    LEDGER.write_text(json.dumps(led,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"  ledger: [{id}] {name} -> {status}")
if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--id",required=True); ap.add_argument("--name",required=True)
    ap.add_argument("--thesis",required=True)
    ap.add_argument("--gate0",choices=["pass","fail"],required=True)
    ap.add_argument("--gate1",choices=["pass","fail"],default=None)
    ap.add_argument("--notes",default="")
    a=ap.parse_args()
    record(id=a.id,name=a.name,thesis=a.thesis,gate0=(a.gate0=="pass"),
           gate1=(a.gate1=="pass") if a.gate1 else None,notes=a.notes)
