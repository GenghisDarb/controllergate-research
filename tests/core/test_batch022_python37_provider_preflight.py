import os

from controllergate.core.docker_runtime_provider import docker_provider_preflight
from controllergate.core.runtime_version_gate import runtime_version_gate_policy, runtime_version_gate_result


def test_provider_preflight_disabled_blocks_without_ignoring_host_mismatch(monkeypatch):
    monkeypatch.delenv("CONTROLLERGATE_ENABLE_DOCKER_PROVIDER", raising=False)
    result = docker_provider_preflight("3.7")
    assert result["status"] == "BLOCK"
    assert result["provider_verified"] is False
    assert result["blocker"] == "docker_runtime_provider_unavailable"
    assert runtime_version_gate_policy("3.7")["host_runtime_mismatch_may_be_ignored"] is False


def test_runtime_version_gate_requires_python37_family():
    assert runtime_version_gate_result("3.7.17", "3.7")["status"] == "PASS"
    assert runtime_version_gate_result("3.10.14", "3.7")["status"] == "BLOCK"
