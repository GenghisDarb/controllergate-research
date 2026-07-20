"""Exact provider identity and historical-provider availability semantics."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import sysconfig
from typing import Any


PROVIDER_STATUSES = {"EXACT_PROVIDER", "SERIES_LIMITED_PROVIDER", "NEAREST_REPRODUCIBLE_PROVIDER", "UNAVAILABLE_PROVIDER"}


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def observed_provider_identity() -> dict[str, Any]:
    info = sys.version_info
    prerelease = None if info.releaselevel == "final" else {"level": info.releaselevel, "serial": info.serial}
    return {
        "implementation": platform.python_implementation(), "version": platform.python_version(),
        "version_tuple": [info.major, info.minor, info.micro], "prerelease": prerelease,
        "os": platform.system().lower(), "architecture": platform.machine().lower(),
        "ABI": str(sysconfig.get_config_var("SOABI") or "unknown"),
        "SOABI": str(sysconfig.get_config_var("SOABI") or "unknown"),
    }


def classify_provider_exactness(requested: dict[str, Any], observed: dict[str, Any], available: bool = True) -> str:
    if not available:
        return "UNAVAILABLE_PROVIDER"
    keys = ("implementation", "version_tuple", "prerelease", "os", "architecture", "ABI", "SOABI")
    if all(requested.get(key) == observed.get(key) for key in keys):
        return "EXACT_PROVIDER"
    if requested.get("implementation") == observed.get("implementation") and requested.get("version_tuple", [])[:2] == observed.get("version_tuple", [])[:2]:
        return "SERIES_LIMITED_PROVIDER"
    return "NEAREST_REPRODUCIBLE_PROVIDER"


def build_provider_capsule_v4(*, capsule_id: str, candidate_id: str, requested: dict[str, Any], observed: dict[str, Any],
                              materialization_receipt: dict[str, Any], runner_image: str, dependency_graph_hash: str,
                              wheel_hashes: list[str], compiler_identity: dict[str, Any] | None = None,
                              available: bool = True) -> dict[str, Any]:
    status = classify_provider_exactness(requested, observed, available)
    row: dict[str, Any] = {
        "capsule_version": "Batch102ProviderCapsuleV4", "capsule_id": capsule_id, "candidate_id": candidate_id,
        "requested_identity": requested, "observed_identity": observed, "provider_exactness_status": status,
        "runner_image": runner_image, "compiler_build_identity": compiler_identity,
        "dependency_graph_hash": dependency_graph_hash, "wheel_hashes": sorted(wheel_hashes),
        "locale": "C.UTF-8", "timezone": "UTC", "git_version": None,
        "environment_hash": canonical_hash({"requested": requested, "observed": observed, "runner_image": runner_image}),
        "materialization_receipt": materialization_receipt,
        "authority_allowed": "provider identity at observed exactness",
        "authority_forbidden": ["prefix-based exact parity", "causal ownership", "patch", "repair count", "release promotion"],
    }
    row["provider_capsule_hash"] = canonical_hash(row)
    return row


def verify_provider_capsule_v4(row: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    status = row.get("provider_exactness_status")
    if status not in PROVIDER_STATUSES: blockers.append("provider_status_invalid")
    expected_status = classify_provider_exactness(row.get("requested_identity", {}), row.get("observed_identity", {}), status != "UNAVAILABLE_PROVIDER")
    if status != expected_status: blockers.append("provider_exactness_misclassified")
    if not row.get("materialization_receipt", {}).get("operation_id"): blockers.append("materialization_receipt_missing")
    expected = canonical_hash({key: value for key, value in row.items() if key != "provider_capsule_hash"})
    if row.get("provider_capsule_hash") != expected: blockers.append("provider_capsule_hash_mismatch")
    return blockers
