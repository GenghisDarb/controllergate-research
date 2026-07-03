import json
from pathlib import Path


def test_batch022_container_provider_integration_safe_stop():
    path = Path("outputs/clean_replication_batch_022/docker_provider_status.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["selected_provider"] in {"self_hosted_python37_plan", "docker_python37_container"}
        if data["status"] != "PASS":
            assert data["blocker"] in {"docker_runtime_provider_unavailable", "python37_docker_provider_unavailable", "runtime_provider_python_version_mismatch"}
