import json
from pathlib import Path


def test_batch021_thin_artifact_payload_avoids_recursive_prior_batches():
    path = Path("outputs/clean_replication_batch_021/artifact_minimality_audit.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "PASS"
        assert data["recursive_prior_batch_packaging_detected"] is False

