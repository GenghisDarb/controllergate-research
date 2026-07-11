from __future__ import annotations

from typing import Any

from .network_policy import destination_allowed, validate_network_policy


def authorize_network_operation(*, phase_id: str, policy: dict[str, Any], destination: str | None, requested_mode: str, tls_verification: bool = True, projected_requests: int = 1, projected_bytes: int = 0) -> dict[str, Any]:
    checked = validate_network_policy(policy, phase_id=phase_id)
    if checked["status"] != "PASS": return checked
    if requested_mode != policy.get("network_mode"): return {"status": "BLOCK", "blocker": "network_mode_not_authorized"}
    if requested_mode in {"none", "forbidden"}:
        return {"status": "PASS" if destination is None else "BLOCK", "blocker": None if destination is None else "network_use_from_network_none_phase"}
    if not tls_verification: return {"status": "BLOCK", "blocker": "network_tls_verification_disabled"}
    if not destination or not destination_allowed(destination, policy): return {"status": "BLOCK", "blocker": "network_destination_not_allowlisted"}
    if projected_requests > int(policy["maximum_requests"]): return {"status": "BLOCK", "blocker": "network_request_budget_exceeded"}
    if projected_bytes > int(policy["maximum_download_bytes"]): return {"status": "BLOCK", "blocker": "network_byte_budget_exceeded"}
    return {"status": "PASS", "blocker": None, "phase_id": phase_id, "destination": destination}
