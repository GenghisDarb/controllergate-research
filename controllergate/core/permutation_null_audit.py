from __future__ import annotations

from typing import Any


ALLOWED_NULLS = [
    "patch_fragment_order_null",
    "evidence_to_fragment_mapping_null",
    "source_route_label_permutation_null",
    "context_order_perturbation_null",
    "dependency_overlap_grouping_null",
]


FORBIDDEN_NULLS = [
    "invalid_syntax_ast_scramble",
    "evidence_class_mutation",
    "future_gold_fixed_pr_evidence",
    "target_evidence_removal",
    "environment_degradation",
    "unregistered_null",
]


def permutation_null_audit_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "diagnostic_only": True,
        "preregistration_required": True,
        "allowed_nulls": ALLOWED_NULLS,
        "forbidden_nulls": FORBIDDEN_NULLS,
        "invalid_by_construction_blocks": True,
    }


def permutation_null_audit_result(patch_candidate_exists: bool) -> dict[str, Any]:
    return {
        "status": "NOT_RUN_NO_PATCH_CANDIDATE" if not patch_candidate_exists else "READY_DIAGNOSTIC_ONLY",
        "registered_null_count": 0,
        "invalid_by_construction_null_count": 0,
        "used_as_repair_evidence": False,
        "blocker": "structured_fragility_not_applicable" if not patch_candidate_exists else None,
    }
