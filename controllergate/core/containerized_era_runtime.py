from __future__ import annotations

from typing import Any


def containerized_era_runtime_policy(required_python: str) -> dict[str, Any]:
    return {
        "status": "PASS",
        "required_python_family": required_python,
        "container_runtime_allowed": True,
        "container_digest_required": True,
        "in_container_python_version_probe_required": True,
        "secrets_available_to_external_tests": False,
        "external_source_workspace_committed": False,
        "policy_result": "container path remains available only after digest and runtime probe verification",
    }


def containerized_workflow_plan(required_python: str) -> dict[str, Any]:
    return {
        "status": "PLAN_ONLY",
        "required_python_family": required_python,
        "workflow_pattern": "separate provider job or contained step with verified runtime probe",
        "target_replay_in_current_workflow": False,
        "blocker": "runtime_provider_exact_version_unavailable",
    }

