import json
from pathlib import Path


def test_batch023_target_intent_cannot_precede_materialization():
    base = Path("outputs/clean_replication_batch_023")
    materialization = json.loads((base / "manual_lock_environment_materialization_log.json").read_text(encoding="utf-8"))
    target = json.loads((base / "target_intent_alignment_retry_audit.json").read_text(encoding="utf-8"))
    if materialization["status"] != "PASS":
        assert target["target_intent_alignment"] is False
        assert target["repair_authorized"] is False
