# ============================================================
#  proofs/record.py — write a proof result to ledger.json
#
#  Usage:
#    from proofs.record import record
#    record(id="P001", name="above_sma200", thesis="...",
#           gate0=True, gate1=False, notes="failed on OOS sharpe")
#
#    python -m proofs.record --id P001 --name above_sma200 \
#           --thesis "price above 200-day SMA" \
#           --gate0 pass --gate1 fail --notes "OOS sharpe 0.6 < 0.8"
# ============================================================
import json
import sys
from datetime import date
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "ledger.json"


def _load():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"proofs": [], "fallacies": []}


def record(*, id: str, name: str, thesis: str,
           gate0: bool, gate1: bool | None = None, notes: str = ""):
    led = _load()
    status = "rejected" if not gate0 or gate1 is False else (
        "passed" if gate1 else "gate0_only")
    entry = {
        "id": id,
        "name": name,
        "thesis": thesis,
        "date": str(date.today()),
        "gate0": gate0,
        "gate1": gate1,
        "status": status,
        "notes": notes,
    }
    led["proofs"] = [p for p in led["proofs"] if p.get("id") != id]
    led["proofs"].append(entry)
    LEDGER.write_text(json.dumps(led, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ledger updated: [{id}] {name} → {status}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--thesis", required=True)
    ap.add_argument("--gate0", choices=["pass", "fail"], required=True)
    ap.add_argument("--gate1", choices=["pass", "fail"], default=None)
    ap.add_argument("--notes", default="")
    a = ap.parse_args()
    record(
        id=a.id, name=a.name, thesis=a.thesis,
        gate0=(a.gate0 == "pass"),
        gate1=(a.gate1 == "pass") if a.gate1 else None,
        notes=a.notes,
    )
