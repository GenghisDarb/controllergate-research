import json
from pathlib import Path


def test_batch021_runtime_provider_safe_stop_integration():
    path = Path("outputs/clean_replication_batch_021/python37_runtime_provider_status.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "BLOCK"
        assert data["exact_provider_verified"] is False
        assert data["blocker"] == "runtime_provider_exact_version_unavailable"

