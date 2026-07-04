import json
from pathlib import Path


def test_batch023_psa82_package_is_summary_only():
    base = Path("outputs/clean_replication_batch_023")
    presence = json.loads((base / "psa82_local_package_presence_check.json").read_text(encoding="utf-8"))
    summary = json.loads((base / "psa82_local_package_quarantine_summary.json").read_text(encoding="utf-8"))
    pyc = json.loads((base / "psa82_pyc_quarantine_summary.json").read_text(encoding="utf-8"))
    assert summary["full_package_committed"] is False
    assert summary["controllergate_repair_evidence"] is False
    assert pyc["pyc_payloads_quarantined"] is True
    if presence["psa82_package_present"] is False:
        assert presence["status"] == "ABSENT"
