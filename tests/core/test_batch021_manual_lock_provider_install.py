import json
from pathlib import Path


def test_batch021_provider_install_does_not_run_without_verified_provider():
    path = Path("outputs/clean_replication_batch_021/provider_lock_install_log.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "NOT_RUN"
        assert data["blocker"] == "runtime_provider_exact_version_unavailable"

