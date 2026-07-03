import json
from pathlib import Path


def test_harness_v6_not_generated_without_provider_materialization():
    path = Path("outputs/clean_replication_batch_021/issue_derived_harness_v6_verification_result.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "NOT_RUN"
        assert data["harness_generated"] is False
        assert data["candidate_verified"] is False

