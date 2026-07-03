from __future__ import annotations

from typing import Any


BOUNDARY_CLASSES = [
    "dependency_precondition_boundary",
    "target_intent_boundary",
    "source_commit_boundary",
    "command_manifest_boundary",
    "workspace_purity_boundary",
    "runtime_exception_boundary",
    "semantic_behavior_boundary",
    "null_comparability_boundary",
    "patch_generation_boundary",
    "post_patch_constraint_boundary",
    "no_overreach_boundary",
    "unknown_boundary",
]


def structural_defect_boundary_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "boundary_classes": BOUNDARY_CLASSES,
        "dependency_precondition_boundary_is_code_defect": False,
        "target_intent_boundary_is_repair_success": False,
        "unknown_boundary_can_license_patch": False,
    }


def boundary_schema() -> dict[str, Any]:
    return {
        "status": "PASS",
        "fields": ["boundary_class", "required_evidence", "allowed_probes", "forbidden_actions", "next_allowed_action", "rollback_requirement", "claim_boundary"],
    }


def classify_boundary(*, dependency_lock_status: str, target_intent_alignment: bool | None) -> dict[str, Any]:
    if dependency_lock_status != "PASS":
        boundary = "dependency_precondition_boundary"
        next_action = "dependency_lock_probe"
    elif target_intent_alignment is not True:
        boundary = "target_intent_boundary"
        next_action = "target_intent_probe"
    else:
        boundary = "semantic_behavior_boundary"
        next_action = "issue_derived_harness_firewall_probe"
    return {
        "status": "PASS",
        "boundary_class": boundary,
        "required_evidence": ["dependency lock", "target-intent alignment", "runtime incident record"],
        "allowed_probes": [next_action],
        "forbidden_actions": ["patch_generation_without_empirical_gate", "repair_success_claim_without_validation"],
        "next_allowed_action": next_action,
        "rollback_requirement": True,
        "claim_boundary": "diagnostic_only_until_empirical_validation",
    }
