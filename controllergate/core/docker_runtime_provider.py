from __future__ import annotations

import os
import subprocess
from typing import Any


PYTHON37_IMAGE = "python:3.7-slim"


def docker_runtime_provider_policy(required_python_family: str = "3.7") -> dict[str, Any]:
    return {
        "status": "PASS",
        "provider_name": "Docker Era-Materialization Provider",
        "required_python_family": required_python_family,
        "actual_python_version_probe_required": True,
        "image_label_only_allowed": False,
        "external_source_write_credentials_allowed": False,
        "secrets_available_to_external_source": False,
        "provider_workspace_committed": False,
    }


def container_security_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "external_source_executed_with_write_credentials": False,
        "secrets_exposed_to_external_source": False,
        "container_workspace_committed": False,
        "logs_sanitized": True,
        "target_replay_requires_prior_provider_and_lock_pass": True,
    }


def docker_provider_preflight(required_python_family: str = "3.7", *, enabled_env: str = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER") -> dict[str, Any]:
    enabled = os.environ.get(enabled_env, "0") == "1"
    base = {
        "status": "BLOCK",
        "enabled_env": enabled_env,
        "enabled": enabled,
        "required_python_family": required_python_family,
        "image": PYTHON37_IMAGE,
        "image_digest": None,
        "digest_status": "not_checked",
        "reproducibility_level": "not_established",
        "actual_python_version": None,
        "actual_pip_version": None,
        "os_release": None,
        "provider_verified": False,
        "blocker": "docker_runtime_provider_unavailable",
    }
    if not enabled:
        return {**base, "reason": "Docker provider execution is disabled unless explicitly enabled for a bounded provider probe"}
    docker_version = subprocess.run(["docker", "--version"], text=True, capture_output=True)
    if docker_version.returncode != 0:
        return {**base, "docker_cli_available": False, "stderr": docker_version.stderr.strip()[:1000]}
    docker_info = subprocess.run(["docker", "info", "--format", "{{json .ServerVersion}}"], text=True, capture_output=True, timeout=30)
    if docker_info.returncode != 0:
        return {
            **base,
            "docker_cli_available": True,
            "docker_version": docker_version.stdout.strip(),
            "docker_daemon_available": False,
            "stderr": docker_info.stderr.strip()[:1000],
        }
    probe_cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        PYTHON37_IMAGE,
        "sh",
        "-lc",
        "python --version 2>&1 && python -m pip --version 2>&1 && cat /etc/os-release 2>/dev/null | head -n 5",
    ]
    probe = subprocess.run(probe_cmd, text=True, capture_output=True, timeout=180)
    if probe.returncode != 0:
        return {
            **base,
            "docker_cli_available": True,
            "docker_daemon_available": True,
            "docker_version": docker_version.stdout.strip(),
            "stderr": probe.stderr.strip()[:1000],
            "blocker": "python37_docker_provider_unavailable",
        }
    lines = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
    python_line = next((line for line in lines if line.lower().startswith("python ")), "")
    pip_line = next((line for line in lines if "pip " in line.lower()), "")
    actual = python_line.split(" ", 1)[1] if " " in python_line else None
    family = ".".join(actual.split(".")[:2]) if actual else None
    inspect = subprocess.run(["docker", "image", "inspect", PYTHON37_IMAGE, "--format", "{{json .RepoDigests}}"], text=True, capture_output=True)
    digest_text = inspect.stdout.strip() if inspect.returncode == 0 else ""
    digest_status = "recorded" if "sha256:" in digest_text else "unavailable"
    passed = family == required_python_family
    return {
        **base,
        "status": "PASS" if passed else "BLOCK",
        "docker_cli_available": True,
        "docker_daemon_available": True,
        "docker_version": docker_version.stdout.strip(),
        "actual_python_version": actual,
        "actual_pip_version": pip_line,
        "os_release": lines[2:],
        "image_digest": digest_text or None,
        "digest_status": digest_status,
        "reproducibility_level": "limited" if digest_status == "unavailable" else "image_digest_recorded",
        "provider_verified": passed,
        "blocker": None if passed else "runtime_provider_python_version_mismatch",
        "target_replay_allowed": passed,
    }
