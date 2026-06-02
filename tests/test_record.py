# ============================================================
#  tests/test_record.py
#  Unit tests for proofs/record.py (ledger write/read).
# ============================================================
import json
import pytest

import proofs.record as rec_mod
from proofs.record import record


@pytest.fixture(autouse=True)
def patch_ledger(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(
        json.dumps({"proofs": [], "fallacies": []}), encoding="utf-8")
    monkeypatch.setattr(rec_mod, "LEDGER", ledger_path)
    return ledger_path


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_gate0_fail_is_rejected(patch_ledger):
    record(id="P001", name="test", thesis="idea", gate0=False)
    assert _read(patch_ledger)["proofs"][0]["status"] == "rejected"


def test_gate0_pass_only(patch_ledger):
    record(id="P002", name="test", thesis="idea", gate0=True)
    assert _read(patch_ledger)["proofs"][0]["status"] == "gate0_only"


def test_both_pass(patch_ledger):
    record(id="P003", name="test", thesis="idea", gate0=True, gate1=True)
    assert _read(patch_ledger)["proofs"][0]["status"] == "passed"


def test_gate1_fail_is_rejected(patch_ledger):
    record(id="P004", name="test", thesis="idea", gate0=True, gate1=False)
    assert _read(patch_ledger)["proofs"][0]["status"] == "rejected"


def test_upsert_replaces_entry(patch_ledger):
    record(id="P005", name="v1", thesis="idea", gate0=False)
    record(id="P005", name="v2", thesis="idea revised", gate0=True, gate1=True)
    entries = [p for p in _read(patch_ledger)["proofs"] if p["id"] == "P005"]
    assert len(entries) == 1
    assert entries[0]["name"] == "v2" and entries[0]["status"] == "passed"


def test_preserves_fallacies(patch_ledger):
    data = _read(patch_ledger)
    data["fallacies"].append({"name": "trap", "text": "x", "triggers": []})
    patch_ledger.write_text(json.dumps(data), encoding="utf-8")
    record(id="P006", name="safe", thesis="idea", gate0=True)
    assert any(f["name"] == "trap" for f in _read(patch_ledger)["fallacies"])
