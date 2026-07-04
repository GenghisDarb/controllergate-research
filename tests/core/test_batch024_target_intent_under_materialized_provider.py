import json
from pathlib import Path


def test_target_intent_retry_requires_materialized_provider():
    batch = Path("outputs/clean_replication_batch_024")
    materialization = json.loads((batch / "manual_lock_environment_materialization_log.json").read_text(encoding="utf-8"))
    target = json.loads((batch / "target_intent_alignment_retry_audit.json").read_text(encoding="utf-8"))
    if target["target_intent_alignment"] is True:
        assert materialization["status"] == "PASS"
    else:
        assert target["repair_authorized"] is False
