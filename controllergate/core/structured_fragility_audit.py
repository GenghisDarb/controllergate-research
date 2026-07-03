from __future__ import annotations

from typing import Any


def structured_fragility_audit_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "diagnostic_only": True,
        "empirical_target_validation_required_first": True,
        "duplicate_replay_required_first": True,
        "no_overreach_required_first": True,
        "byte_custody_required_first": True,
        "can_increment_repair_count": False,
        "can_support_memory_lift_alone": False,
    }


def structured_fragility_status(patch_candidate_exists: bool, target_intent_passed: bool) -> dict[str, Any]:
    if not patch_candidate_exists:
        return {
            "status": "NOT_RUN_NO_PATCH_CANDIDATE",
            "diagnostic_only": True,
            "blocker": "structured_fragility_not_applicable",
            "used_as_repair_evidence": False,
        }
    if not target_intent_passed:
        return {
            "status": "BLOCK",
            "diagnostic_only": True,
            "blocker": "structured_fragility_not_applicable",
            "used_as_repair_evidence": False,
        }
    return {
        "status": "READY_DIAGNOSTIC_ONLY",
        "diagnostic_only": True,
        "used_as_repair_evidence": False,
    }


def adapter_mapping(psa82_present: bool) -> dict[str, Any]:
    return {
        "status": "PASS" if psa82_present else "POLICY_ONLY",
        "source_package_present": psa82_present,
        "adapter_scope": "diagnostic inspiration only",
        "controllergate_terms": [
            "Structured Fragility Audit",
            "Permutation Null Audit",
            "Patch-Structure Sensitivity",
        ],
        "not_controllergate_repair_evidence": True,
    }
