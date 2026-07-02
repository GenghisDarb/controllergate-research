from __future__ import annotations

from typing import Any

LOCKS = ["provenance", "null", "perturbation", "projection"]
LOCK_PAIR_CLASSES = {
    "structural_pair": ["null", "perturbation"],
    "information_pair": ["provenance", "projection"],
}

OPERATIONS = {
    "evidence_admission": ["provenance", "projection"],
    "causal_stress_test": ["provenance", "null", "perturbation"],
    "dual_projection_consistency": ["provenance", "projection", "null"],
    "repair_candidate_admission": ["provenance", "projection", "perturbation", "null"],
    "memory_separation_claim": ["provenance", "null", "perturbation", "projection"],
    "runtime_action_compilation": ["provenance", "projection", "perturbation", "null", "projection"],
    "rollback_required": ["provenance", "projection"],
    "degradation_monitoring": ["provenance", "projection", "perturbation"],
    "dependency_drift_classification": ["provenance", "projection", "perturbation"],
    "safe_stop": ["provenance", "projection"],
}


def registry_records() -> dict[str, Any]:
    return {
        "status": "PASS",
        "locks": LOCKS,
        "lock_pair_classes": LOCK_PAIR_CLASSES,
        "operations": {
            name: {
                "sequence": sequence,
                "required_artifacts": [f"{lock}_evidence" for lock in dict.fromkeys(sequence)],
                "audit_assertions": ["required_locks_present", "claim_boundary_present"],
                "blockers": [f"{name}_required_lock_missing"],
                "claim_boundary": "operation cannot exceed passed lock evidence",
            }
            for name, sequence in OPERATIONS.items()
        },
        "rules": {
            "curvature_replaces_evidence": False,
            "state_mutation_requires_provenance": True,
            "runtime_action_requires_projection": True,
            "memory_separation_requires_null_and_perturbation": True,
        },
    }


def validate_operation(operation: str, available_locks: list[str]) -> dict[str, Any]:
    if operation not in OPERATIONS:
        return {"status": "BLOCK", "blocker": "unknown_operation"}
    required = OPERATIONS[operation]
    missing = [lock for lock in dict.fromkeys(required) if lock not in available_locks]
    return {
        "status": "PASS" if not missing else "BLOCK",
        "operation": operation,
        "required_locks": required,
        "available_locks": available_locks,
        "missing_locks": missing,
        "blocker": None if not missing else f"{operation}_required_lock_missing",
    }
