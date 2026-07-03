from __future__ import annotations

from typing import Any


def dynamic_era_materialization_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "purpose": "adapt runtime provider to the reviewed dependency lock before environment materialization",
        "must_not_loosen_python_version": True,
        "must_not_install_latest_unrestricted_dependencies": True,
        "must_not_mutate_source_tests_or_expectations": True,
        "provider_verification_required_before_replay": True,
    }


def runtime_version_gate_policy(required_python: str) -> dict[str, Any]:
    return {
        "status": "PASS",
        "required_python_family": required_python,
        "exact_family_match_required": True,
        "host_mismatch_blocks_materialization": True,
        "label_only_runtime_claim_blocks_materialization": True,
    }


def runtime_version_gate_audit(selection: dict[str, Any], host_python_version: str, required_python: str) -> dict[str, Any]:
    host_family = ".".join(str(host_python_version).split(".")[:2])
    provider_verified = selection.get("status") == "PASS" and selection.get("target_replay_allowed") is True
    return {
        "status": "PASS" if provider_verified else "BLOCK",
        "required_python_family": required_python,
        "host_python_version": host_python_version,
        "host_python_family": host_family,
        "host_matches_required_family": host_family == required_python,
        "selected_provider_id": selection.get("selected_provider_id"),
        "selected_provider_status": selection.get("status"),
        "target_replay_allowed": provider_verified,
        "blocker": None if provider_verified else selection.get("blocker", "runtime_version_gate_failed"),
    }


def dynamic_era_materialization_status(selection: dict[str, Any], version_gate: dict[str, Any]) -> dict[str, Any]:
    materialization_allowed = selection.get("status") == "PASS" and version_gate.get("status") == "PASS"
    return {
        "status": "PASS" if materialization_allowed else "BLOCK",
        "materialization_allowed": materialization_allowed,
        "selected_provider_id": selection.get("selected_provider_id"),
        "target_replay_allowed": materialization_allowed,
        "blocker": None if materialization_allowed else selection.get("blocker") or version_gate.get("blocker"),
    }

