from __future__ import annotations

from hashlib import sha256
from typing import Any


FEATURE_VECTOR_FIELDS = [
    "candidate_id",
    "candidate_class",
    "source_type",
    "repo_url",
    "source_commit_sha",
    "issue_url",
    "issue_timestamp_status",
    "evidence_class",
    "native_or_issue_derived",
    "dependency_lock_status",
    "environment_lock_status",
    "command_manifest_status",
    "workspace_purity_status",
    "baseline_drift_status",
    "target_intent_alignment_status",
    "runtime_incident_status",
    "stack_trace_depth",
    "stack_trace_module_count",
    "source_file_count_in_trace",
    "source_function_count_in_trace",
    "import_graph_width",
    "ast_closure_width",
    "patchable_source_file_count",
    "alternative_route_count",
    "interlock_invariant_count",
    "precondition_friction_score",
    "dependency_era_risk_score",
    "issue_text_specificity_score",
    "reproduction_command_specificity_score",
    "expected_information_gain",
    "expected_probe_cost",
    "expected_probe_risk",
    "stable_region_score",
    "failure_boundary_score",
    "recovery_path_score",
    "curvature_route_diversity_score",
    "null_comparability_status",
    "claim_boundary_status",
    "recommended_next_probe",
    "blocker_if_not_probeable",
]


def stable_record_hash(record: dict[str, Any]) -> str:
    import json

    return sha256(json.dumps(record, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def active_search_space_geometry_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "purpose": "probe_selection_and_candidate_routing",
        "may_propose_probes": True,
        "may_prioritize_candidate_leads": True,
        "may_classify_candidate_risk": True,
        "may_score_expected_information_gain": True,
        "may_identify_failure_boundaries": True,
        "may_suggest_recovery_candidate_paths": True,
        "may_claim_repair": False,
        "may_validate_repair": False,
        "may_replace_commit_verification": False,
        "may_replace_environment_lock": False,
        "may_replace_target_replay": False,
        "may_replace_null_ensemble": False,
        "may_replace_target_validation": False,
        "may_replace_duplicate_replay": False,
        "may_replace_post_patch_constraint_revalidation": False,
        "may_replace_no_overreach_validation": False,
        "may_replace_artifact_custody": False,
    }


def search_space_geometry_schema() -> dict[str, Any]:
    return {
        "status": "PASS",
        "schema_name": "search_space_feature_vector_v1",
        "fields": FEATURE_VECTOR_FIELDS,
        "missing_evidence_must_be_explicit": True,
        "blocked_feature_vectors_license_repair": False,
    }


def build_search_space_feature_vector(
    *,
    candidate_id: str,
    candidate_class: str,
    source_type: str,
    repo_url: str,
    issue_url: str,
    source_commit_sha: str | None,
    issue_timestamp_status: str,
    dependency_lock_status: str,
    target_intent_alignment_status: str,
    blocker_if_not_probeable: str | None,
) -> dict[str, Any]:
    missing = []
    if not source_commit_sha:
        missing.append("source_commit_sha")
    if dependency_lock_status not in {"PASS", "VALID", "AVAILABLE"}:
        missing.append("dependency_lock_validation")
    vector = {
        "candidate_id": candidate_id,
        "candidate_class": candidate_class,
        "source_type": source_type,
        "repo_url": repo_url,
        "source_commit_sha": source_commit_sha,
        "issue_url": issue_url,
        "issue_timestamp_status": issue_timestamp_status,
        "evidence_class": "issue_derived" if candidate_class == "issue_derived_reproduction_candidate" else "native",
        "native_or_issue_derived": "issue_derived" if candidate_class == "issue_derived_reproduction_candidate" else "native",
        "dependency_lock_status": dependency_lock_status,
        "environment_lock_status": "NOT_RUN",
        "command_manifest_status": "NOT_RUN",
        "workspace_purity_status": "NOT_RUN",
        "baseline_drift_status": "NOT_RUN",
        "target_intent_alignment_status": target_intent_alignment_status,
        "runtime_incident_status": "RECORDED",
        "stack_trace_depth": "unknown",
        "stack_trace_module_count": "unknown",
        "source_file_count_in_trace": "unknown",
        "source_function_count_in_trace": "unknown",
        "import_graph_width": "unknown",
        "ast_closure_width": "unknown",
        "patchable_source_file_count": 0,
        "alternative_route_count": 0,
        "interlock_invariant_count": 0,
        "precondition_friction_score": 5,
        "dependency_era_risk_score": 5 if dependency_lock_status != "PASS" else 1,
        "issue_text_specificity_score": 4,
        "reproduction_command_specificity_score": 4,
        "expected_information_gain": 8 if dependency_lock_status != "PASS" else 4,
        "expected_probe_cost": 2,
        "expected_probe_risk": 1,
        "stable_region_score": 1,
        "failure_boundary_score": 5,
        "recovery_path_score": 8,
        "curvature_route_diversity_score": 0,
        "null_comparability_status": "NOT_RUN",
        "claim_boundary_status": "PASS",
        "recommended_next_probe": "dependency_lock_probe" if dependency_lock_status != "PASS" else "target_intent_probe",
        "blocker_if_not_probeable": blocker_if_not_probeable,
        "missing_evidence": missing,
    }
    vector["feature_vector_hash"] = stable_record_hash(vector)
    return vector


def stable_candidate_region_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "stable_region_score_is_diagnostic": True,
        "stable_region_score_can_license_repair": False,
        "missing_evidence_penalized": True,
    }


def active_search_space_geometry_status(vector: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "PASS",
        "feature_vector_hash": vector.get("feature_vector_hash"),
        "repair_claimed": False,
        "repair_validated": False,
        "empirical_gates_replaced": False,
        "recommended_next_probe": vector.get("recommended_next_probe"),
    }
