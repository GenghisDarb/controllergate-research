import json
from pathlib import Path


def test_issue_derived_harness_v9_waits_for_target_intent():
    batch = Path("outputs/clean_replication_batch_024")
    target = json.loads((batch / "target_intent_alignment_retry_audit.json").read_text(encoding="utf-8"))
    harness = json.loads((batch / "issue_derived_harness_v9_verification_result.json").read_text(encoding="utf-8"))
    if harness["harness_generated"]:
        assert target["target_intent_alignment"] is True
    else:
        assert harness["status"] == "NOT_RUN"
