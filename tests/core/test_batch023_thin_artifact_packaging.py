import json
from pathlib import Path


def test_batch023_thin_artifact_packaging_excludes_prior_batches():
    base = Path("outputs/clean_replication_batch_023")
    minimality = json.loads((base / "artifact_minimality_audit.json").read_text(encoding="utf-8"))
    budget = json.loads((base / "artifact_payload_budget.json").read_text(encoding="utf-8"))
    assert minimality["recursive_prior_batch_packaging_detected"] is False
    assert budget["status"] == "PASS"
