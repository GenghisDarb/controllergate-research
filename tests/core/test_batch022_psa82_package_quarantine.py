import json
from pathlib import Path


def test_psa82_quarantine_outputs_do_not_use_legacy_manifest_or_ingest_pyc():
    base = Path("outputs/clean_replication_batch_022")
    if base.exists():
        policy = json.loads((base / "psa82_package_quarantine_policy.json").read_text(encoding="utf-8"))
        legacy = json.loads((base / "psa82_legacy_manifest_stale_audit.json").read_text(encoding="utf-8"))
        pyc = json.loads((base / "psa82_pyc_payload_audit.json").read_text(encoding="utf-8"))
        assert policy["final_locked_manifest_authoritative"] is True
        assert policy["legacy_manifest_authoritative"] is False
        assert legacy["legacy_manifest_authoritative"] is False
        assert pyc["pyc_payloads_quarantined"] is True
        assert pyc.get("pyc_payloads_ingested") is not True
