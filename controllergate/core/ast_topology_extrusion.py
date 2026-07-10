from __future__ import annotations

TOPOLOGY_STATES = {
    "no_materialized_failure_topology",
    "flat_or_unavailable_topology",
    "interior_elbow_candidate",
}


def build_ast_topology_record(
    *,
    candidate_id: str,
    source_file_count: int,
    test_file_count: int,
    materialized_failure: bool,
) -> dict[str, object]:
    topology_state = "interior_elbow_candidate" if materialized_failure and source_file_count > 0 else "no_materialized_failure_topology"
    authorization = (
        "elbow_open_patch_license_precondition_satisfied"
        if topology_state == "interior_elbow_candidate"
        else "elbow_closed_or_flatline_no_patch_license"
    )
    return {
        "candidate_id": candidate_id,
        "source_file_count": source_file_count,
        "test_file_count": test_file_count,
        "materialized_failure": materialized_failure,
        "winner_N_argmin": None,
        "winner_N_elbow": None,
        "topology_state": topology_state,
        "patch_authorization_precondition": authorization,
        "batch069b_patch_generation_allowed": False,
        "audit_status": "PASS",
    }


def validate_ast_topology_record(record: dict[str, object]) -> dict[str, object]:
    errors: list[str] = []
    if record.get("topology_state") not in TOPOLOGY_STATES:
        errors.append("topology_state_invalid")
    if record.get("batch069b_patch_generation_allowed") is not False:
        errors.append("batch069b_patch_generation_allowed")
    if record.get("audit_status") != "PASS":
        errors.append("audit_status_not_pass")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}
