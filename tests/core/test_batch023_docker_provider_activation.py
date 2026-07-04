import json
from pathlib import Path


def test_batch023_docker_provider_activation_is_explicit():
    gate = json.loads(Path("outputs/clean_replication_batch_023/docker_provider_activation_gate.json").read_text(encoding="utf-8"))
    policy = json.loads(Path("outputs/clean_replication_batch_023/docker_provider_activation_policy.json").read_text(encoding="utf-8"))
    assert policy["bounded_probe_required"] is True
    assert policy["broad_docker_execution_allowed"] is False
    assert gate["enabled_env"] == "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"
    if gate["enabled"] is False:
        assert gate["blocker"] == "docker_provider_not_enabled"
