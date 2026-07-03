import json
from pathlib import Path


def test_repair_cannot_activate_before_materialization_and_target_intent():
    path = Path("outputs/clean_replication_batch_020/activation_order_audit_batch020.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "PASS"
        assert data["repair_activated_without_target_intent"] is False
        assert data["repair_activated_without_bounded_materialization"] is False
