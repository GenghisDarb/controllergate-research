import json
from pathlib import Path


def test_batch016_incident_capture_records_mismatch_hashes():
    path = Path("outputs/clean_replication_batch_016/runtime_incident_issue112_mismatch.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["incident_bundle_hash"]) == 64
        assert len(data["expected_target_signature_hash"]) == 64
        assert data["observed_exception_class"] == "TypeError"
