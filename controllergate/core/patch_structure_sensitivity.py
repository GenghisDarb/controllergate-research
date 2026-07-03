from __future__ import annotations

from typing import Any


def patch_structure_sensitivity_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "diagnostic_only": True,
        "requires_patch_candidate": True,
        "requires_target_intent_alignment": True,
        "requires_empirical_target_validation": True,
        "generic_patch_warning_if_nulls_also_pass": True,
        "can_replace_repair_validation": False,
    }


def patch_structure_sensitivity_result(patch_candidate_exists: bool, empirical_gates_passed: bool) -> dict[str, Any]:
    if not patch_candidate_exists:
        return {
            "status": "NOT_RUN_NO_PATCH_CANDIDATE",
            "structured_patch_sensitivity_detected": False,
            "generic_or_non_specific_patch_warning": False,
            "used_as_repair_evidence": False,
            "blocker": "structured_fragility_not_applicable",
        }
    if not empirical_gates_passed:
        return {
            "status": "BLOCK",
            "structured_patch_sensitivity_detected": False,
            "generic_or_non_specific_patch_warning": False,
            "used_as_repair_evidence": False,
            "blocker": "structured_fragility_not_applicable",
        }
    return {
        "status": "READY_DIAGNOSTIC_ONLY",
        "structured_patch_sensitivity_detected": None,
        "generic_or_non_specific_patch_warning": None,
        "used_as_repair_evidence": False,
    }
