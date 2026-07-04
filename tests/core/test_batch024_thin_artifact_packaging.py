import json
from pathlib import Path


def test_batch024_thin_artifact_does_not_package_prior_batches_recursively():
    audit = json.loads(Path("outputs/clean_replication_batch_024/artifact_minimality_audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "PASS"
    assert audit["recursive_prior_batch_packaging_detected"] is False
