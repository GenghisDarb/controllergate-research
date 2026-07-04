import json
from pathlib import Path


def test_batch023_provider_preflight_records_runtime_or_blocker():
    result = json.loads(Path("outputs/clean_replication_batch_023/python37_provider_preflight_results.json").read_text(encoding="utf-8"))
    assert result["required_python_family"] == "3.7"
    assert result["image"] == "python:3.7-slim"
    if result["status"] == "PASS":
        assert result["actual_python_version"].startswith("3.7.")
        assert result["actual_pip_version"]
    else:
        assert result["blocker"] in {"docker_provider_not_enabled", "docker_runtime_provider_unavailable", "python37_docker_provider_unavailable", "runtime_provider_python_version_mismatch"}
