from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


NETWORK_MODES = {"none", "bounded_read_only", "forbidden"}


def execution_network_policy() -> dict[str, object]:
    """Retain the pre-H8 public helper for offline execution callers."""
    return {
        "network_mode": "none",
        "network_requests_allowed": False,
        "network_request_count_expected": 0,
        "phase": "offline_materialization_and_collection",
        "status": "PASS",
    }


def resolution_network_policy() -> dict[str, object]:
    """Retain the pre-H8 public helper for legacy provider-resolution records."""
    return {
        "network_mode": "bridge",
        "network_requests_allowed": True,
        "authorization_reason": "download declared provider archives into content-addressed wheelhouse",
        "candidate_test_execution_allowed": False,
        "phase": "controlled_dependency_resolution",
        "status": "PASS",
    }


def validate_network_policy(policy: dict[str, Any], *, phase_id: str) -> dict[str, Any]:
    errors: list[str] = []
    if policy.get("phase_id") != phase_id: errors.append("network_policy_phase_mismatch")
    mode = policy.get("network_mode")
    if mode not in NETWORK_MODES: errors.append("network_policy_mode_invalid")
    destinations = list(policy.get("allowed_network_destinations", []))
    protocols = list(policy.get("allowed_protocols", []))
    if mode == "bounded_read_only":
        if not destinations: errors.append("network_destination_allowlist_missing")
        if protocols != ["https"]: errors.append("network_protocol_policy_invalid")
        if int(policy.get("maximum_requests", 0)) <= 0: errors.append("network_request_budget_invalid")
        if int(policy.get("maximum_download_bytes", 0)) <= 0: errors.append("network_byte_budget_invalid")
        if policy.get("tls_verification_policy") != "required": errors.append("network_tls_policy_invalid")
        if policy.get("redirect_policy") not in {"same_host_only", "allowlisted_hosts_only"}: errors.append("network_redirect_policy_invalid")
    elif destinations or protocols or int(policy.get("maximum_requests", 0)) or int(policy.get("maximum_download_bytes", 0)):
        errors.append("network_none_policy_has_capability")
    return {"status": "PASS" if not errors else "BLOCK", "blocker": errors[0] if errors else None, "errors": errors}


def destination_allowed(url: str, policy: dict[str, Any]) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in set(policy.get("allowed_protocols", [])) and parsed.hostname in set(policy.get("allowed_network_destinations", []))


def docker_network_mode(policy: dict[str, Any]) -> str:
    return "bridge" if policy.get("network_mode") == "bounded_read_only" else "none"
