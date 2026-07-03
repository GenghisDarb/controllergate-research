import json
from pathlib import Path


def test_batch021_target_intent_retry_waits_for_verified_provider():
    path = Path("outputs/clean_replication_batch_021/target_intent_alignment_retry_under_provider_audit.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "NOT_RUN"
        assert data["blocker"] == "runtime_provider_exact_version_unavailable"

