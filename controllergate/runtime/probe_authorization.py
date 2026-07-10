from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record


REQUIRED_AUTHORIZATION_FIELDS = {
    "candidate_id", "candidate_sha", "candidate_state_hash", "source_identity",
    "command_argv", "target_path", "provider_policy_hash", "container_policy_hash",
    "allowed_graph_steps", "patch_authority", "scope",
}


def build_probe_authorization(**values: Any) -> dict[str, Any]:
    record = dict(values)
    record.setdefault("patch_authority", False)
    record.setdefault("scope", "one_run_batch068h_collection_only")
    record["authorization_hash"] = hash_record(record)
    return record


def verify_probe_authorization(record: dict[str, Any], candidate_state: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_AUTHORIZATION_FIELDS - set(record))
    errors = [f"missing:{name}" for name in missing]
    if record.get("candidate_id") != candidate_state.get("candidate_id"): errors.append("candidate_id_mismatch")
    if record.get("candidate_sha") != candidate_state.get("candidate_sha"): errors.append("candidate_sha_mismatch")
    if record.get("candidate_state_hash") != candidate_state.get("state_hash"): errors.append("candidate_state_hash_mismatch")
    if record.get("patch_authority") is not False: errors.append("patch_authority_must_be_false")
    expected_hash = hash_record({key: value for key, value in record.items() if key != "authorization_hash"})
    if record.get("authorization_hash") != expected_hash: errors.append("authorization_hash_invalid")
    return {"status": "PASS" if not errors else "BLOCK", "errors": errors, "probe_authorized": not errors}
