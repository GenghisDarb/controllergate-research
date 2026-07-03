import json
from pathlib import Path


def test_target_intent_retry_requires_materialized_environment():
    path = Path("outputs/clean_replication_batch_020/target_intent_alignment_retry_audit.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "NOT_RUN"
        assert data["repair_authorized"] is False
