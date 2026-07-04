import json
from pathlib import Path


def test_batch023_structured_fragility_remains_diagnostic():
    status = json.loads(Path("outputs/clean_replication_batch_023/structured_fragility_audit_status.json").read_text(encoding="utf-8"))
    policy = json.loads(Path("outputs/clean_replication_batch_023/structured_fragility_audit_policy.json").read_text(encoding="utf-8"))
    assert status["status"] == "NOT_RUN_NO_PATCH_CANDIDATE"
    assert policy["can_replace_target_validation"] is False
