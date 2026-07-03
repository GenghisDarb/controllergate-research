import json
from pathlib import Path


def test_batch022_target_intent_retry_requires_materialized_provider():
    base = Path("outputs/clean_replication_batch_022")
    if base.exists():
        target = json.loads((base / "target_intent_alignment_retry_audit.json").read_text(encoding="utf-8"))
        repair = json.loads((base / "repair_only_fallback_status.json").read_text(encoding="utf-8"))
        assert target["status"] == "NOT_RUN"
        assert target["repair_authorized"] is False
        assert repair["repair_only_fallback_attempted"] is False
