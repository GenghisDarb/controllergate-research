from __future__ import annotations

REQUIRED_FIELDS = [
    "candidate_id",
    "repo_url",
    "source_environment",
    "target_environment",
    "python_version_constraints",
    "os_constraints",
    "runner_constraints",
    "provider_constraints",
    "fixture_constraints",
    "known_family_homology",
    "known_failure_signature",
    "translated_failure_signature",
    "ast_contact_topology_hints",
    "allowed_use",
    "forbidden_use",
    "decision_time_safe",
    "audit_status",
]

ALLOWED_USE = [
    "routing",
    "provider_planning",
    "command_boundary_risk_prediction",
    "source_topology_search_prioritization",
    "manual_artifact_request_planning",
]

FORBIDDEN_USE = ["patch_authority", "count_gate_evidence", "memory_lift_evidence", "repair_success_claim"]


def build_cross_environment_record(
    *,
    candidate_id: str,
    repo_url: str,
    provider_constraints: list[str],
    runner_constraints: list[str],
    known_failure_signature: str,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "repo_url": repo_url,
        "source_environment": "candidate_sha_checkout_metadata",
        "target_environment": "controllergate_isolated_probe_runtime",
        "python_version_constraints": ["candidate_metadata_only", "no_unbounded_latest_resolution"],
        "os_constraints": ["ubuntu-latest_probe_expected", "host_local_probe_recorded_when_used"],
        "runner_constraints": runner_constraints,
        "provider_constraints": provider_constraints,
        "fixture_constraints": ["no_fixture_mutation", "manual_artifact_required_if_target_fixture_missing"],
        "known_family_homology": "command_boundary_recovery_family",
        "known_failure_signature": known_failure_signature,
        "translated_failure_signature": known_failure_signature,
        "ast_contact_topology_hints": ["metadata_only_no_patch_topology_authority"],
        "allowed_use": ALLOWED_USE,
        "forbidden_use": FORBIDDEN_USE,
        "decision_time_safe": True,
        "audit_status": "PASS",
    }


def validate_cross_environment_record(record: dict[str, object]) -> dict[str, object]:
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    forbidden = set(record.get("forbidden_use") or [])
    allowed = set(record.get("allowed_use") or [])
    errors: list[str] = []
    if not set(FORBIDDEN_USE).issubset(forbidden):
        errors.append("forbidden_use_incomplete")
    if not allowed.issubset(ALLOWED_USE):
        errors.append("allowed_use_invalid")
    if record.get("decision_time_safe") is not True:
        errors.append("decision_time_safe_false")
    if record.get("audit_status") != "PASS":
        errors.append("audit_status_not_pass")
    return {"status": "PASS" if not missing and not errors else "FAIL", "missing": missing, "errors": errors}
