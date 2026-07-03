from __future__ import annotations

from typing import Any


def runtime_version_gate_policy(required_python_family: str = "3.7") -> dict[str, Any]:
    return {
        "status": "PASS",
        "required_python_family": required_python_family,
        "actual_provider_python_version_required": True,
        "image_label_only_allowed": False,
        "host_runtime_mismatch_may_be_ignored": False,
        "target_replay_requires_runtime_gate_pass": True,
    }


def runtime_version_gate_result(actual_version: str | None, required_python_family: str = "3.7") -> dict[str, Any]:
    actual_family = ".".join(actual_version.split(".")[:2]) if actual_version else None
    passed = actual_family == required_python_family
    return {
        "status": "PASS" if passed else "BLOCK",
        "required_python_family": required_python_family,
        "actual_provider_python_version": actual_version,
        "actual_provider_python_family": actual_family,
        "version_family_matches": passed,
        "target_replay_allowed": passed,
        "blocker": None if passed else "runtime_provider_python_version_mismatch",
    }
