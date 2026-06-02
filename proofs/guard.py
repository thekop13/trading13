# ============================================================
#  proofs/guard.py — Fallacy Guard
#  Check a strategy idea against past lessons BEFORE coding it.
#
#  Usage:
#    python -m proofs.guard "MACD crossover confirmed by RSI"
#    from proofs.guard import check
# ============================================================
import json
import re
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "ledger.json"

SIM_BLOCK = 0.40   # token-overlap above this (or >=2 trigger words) => block
SIM_WARN = 0.18    # ...above this => warn


def _load() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"proofs": [], "fallacies": []}


def _tokens(s: str) -> set:
    # keep latin + thai words, length >= 3
    return {w for w in re.findall(r"[a-zA-Z฀-๿]+", s.lower()) if len(w) >= 3}


def _sim(a: set, b: set) -> float:
    return len(a & b) / (len(a | b) or 1)


def check(idea: str) -> list[dict]:
    """Return list of hits: {severity: block|warn, name, text, matched}."""
    led = _load()
    itok = _tokens(idea)
    low = idea.lower()
    hits = []

    for f in led.get("fallacies", []):
        traps = f.get("triggers", [])
        matched = [t for t in traps if t.lower() in low]
        sim = _sim(itok, _tokens(f.get("name", "") + " " + f.get("text", "")))
        if matched or sim >= SIM_WARN:
            sev = "block" if (len(matched) >= 2 or sim >= SIM_BLOCK) else "warn"
            hits.append({"severity": sev, "kind": "fallacy",
                         "name": f["name"], "text": f["text"], "matched": matched})

    for p in led.get("proofs", []):
        if p.get("status") == "rejected":
            sim = _sim(itok, _tokens(p.get("name", "") + " " + p.get("thesis", "")))
            if sim >= 0.30:
                hits.append({"severity": "block" if sim >= 0.5 else "warn",
                             "kind": "proof",
                             "name": f"{p.get('id','?')} {p.get('name','')}",
                             "text": "Idea resembles a proof that already FAILED.",
                             "matched": []})

    hits.sort(key=lambda h: 0 if h["severity"] == "block" else 1)
    return hits


def report(idea: str) -> str:
    hits = check(idea)
    out = ["=" * 56, "  Fallacy Guard — checking idea against past lessons",
           "=" * 56, f"  Idea: {idea}", ""]
    if not hits:
        out.append("✅ No match against known fallacies/failed proofs — go ahead.")
        return "\n".join(out)
    icon = {"block": "🛑", "warn": "⚠️"}
    for h in hits:
        out.append(f"{icon[h['severity']]} [{h['kind']}] {h['name']}")
        out.append(f"     {h['text']}")
        if h["matched"]:
            out.append(f"     (trigger words: {', '.join(h['matched'])})")
    out.append("")
    if any(h["severity"] == "block" for h in hits):
        out.append("🛑 BLOCK present — do NOT proceed yet. Explain how this differs from before.")
    else:
        out.append("⚠️ WARN only — you may proceed, but design Gate 0 to clearly beat the baseline.")
    return "\n".join(out)


if __name__ == "__main__":
    idea = " ".join(sys.argv[1:]) or "(no idea given)"
    print(report(idea))
