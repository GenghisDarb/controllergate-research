from __future__ import annotations

from typing import Any


def runtime_provider_selection_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "exact_runtime_version_required": True,
        "label_only_runtime_evidence_allowed": False,
        "host_runtime_may_materialize_on_version_mismatch": False,
        "target_replay_requires_verified_provider": True,
        "fallback_order": [
            "verified_host_runtime",
            "verified_hosted_runtime",
            "verified_container_runtime",
            "self_hosted_runtime_plan",
        ],
    }


def select_runtime_provider(registry: dict[str, Any], required_python: str) -> dict[str, Any]:
    providers = [item for item in registry.get("providers", []) if isinstance(item, dict)]
    for provider in providers:
        if provider.get("exact_runtime_verified") is True and provider.get("runtime_family") == required_python:
            return {
                "status": "PASS",
                "decision": "verified_runtime_provider_selected",
                "selected_provider_id": provider.get("provider_id"),
                "selected_provider_type": provider.get("provider_type"),
                "required_python_family": required_python,
                "blocker": None,
                "target_replay_allowed": True,
            }
    return {
        "status": "BLOCK",
        "decision": "self_hosted_runtime_required",
        "selected_provider_id": "self_hosted_python37_plan",
        "selected_provider_type": "self_hosted_plan",
        "required_python_family": required_python,
        "blocker": "runtime_provider_exact_version_unavailable",
        "target_replay_allowed": False,
    }

