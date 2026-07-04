import json
from pathlib import Path


def test_issue_derived_harness_v8_waits_for_target_intent():
    base = Path("outputs/clean_replication_batch_023")
    policy = json.loads((base / "issue_derived_harness_v8_policy.json").read_text(encoding="utf-8"))
    result = json.loads((base / "issue_derived_harness_v8_verification_result.json").read_text(encoding="utf-8"))
    assert policy["requires_target_intent_alignment"] is True
    if result["status"] == "NOT_RUN":
        assert result["harness_generated"] is False
        assert result["candidate_verified"] is False
