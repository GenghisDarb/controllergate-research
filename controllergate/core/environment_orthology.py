from __future__ import annotations

ALLOWED_TRANSFER_CLASSES = [
    "same_project_same_environment",
    "same_project_different_environment",
    "same_project_different_runner",
    "same_project_different_provider",
    "same_project_different_command_shape",
    "cross_project_same_failure_family",
    "cross_project_similar_failure_family",
    "cross_family_hypothesis_only",
    "orthology_transfer_candidate",
]

ALLOWED_USES = [
    "routing_memory_only",
    "candidate_prioritization_only",
    "preflight_probe_selection",
    "provider_capsule_selection",
    "command_translation_hint",
    "manual_review_hint",
    "not_allowed_for_patch_generation",
    "not_allowed_for_count_gate",
    "not_allowed_for_memory_lift",
]

FORBIDDEN_USES = [
    "direct_patch_authorization",
    "repair_success_claim",
    "count_increment",
    "duplicate_replay_substitute",
    "memory_lift_claim",
    "full_scoring_claim",
    "self_maintaining_claim",
    "gold_patch_substitute",
    "future_evidence_substitute",
]

REQUIRED_ORTHOLOGY_FIELDS = [
    "source_failure_id",
    "target_failure_id",
    "source_candidate_id",
    "target_candidate_id",
    "source_project",
    "target_project",
    "source_environment",
    "target_environment",
    "source_python_version",
    "target_python_version",
    "source_os",
    "target_os",
    "source_runner",
    "target_runner",
    "source_command_manifest_hash",
    "target_command_manifest_hash",
    "source_provider_capsule_hash",
    "target_provider_capsule_hash",
    "source_harness_origin_hash",
    "target_harness_origin_hash",
    "source_failure_signature_hash",
    "target_failure_signature_hash",
    "shared_structural_features",
    "different_structural_features",
    "constraint_type",
    "transfer_class",
    "allowed_use",
    "forbidden_use",
    "decision_time_safe",
    "requires_manual_review",
    "reopen_condition",
    "audit_status",
]


def validate_orthology_record(record: dict[str, object]) -> dict[str, object]:
    missing = [field for field in REQUIRED_ORTHOLOGY_FIELDS if field not in record]
    errors: list[str] = []
    if record.get("transfer_class") not in ALLOWED_TRANSFER_CLASSES:
        errors.append("transfer_class_invalid")
    allowed = record.get("allowed_use") or []
    forbidden = record.get("forbidden_use") or []
    if not isinstance(allowed, list) or not set(allowed).issubset(ALLOWED_USES):
        errors.append("allowed_use_invalid")
    if not isinstance(forbidden, list) or not set(forbidden).issuperset(FORBIDDEN_USES):
        errors.append("forbidden_use_incomplete")
    if record.get("decision_time_safe") is not True:
        errors.append("decision_time_safe_false")
    if record.get("audit_status") != "PASS":
        errors.append("audit_status_not_pass")
    return {"status": "PASS" if not missing and not errors else "FAIL", "missing": missing, "errors": errors}
