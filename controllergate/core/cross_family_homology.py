from __future__ import annotations

REQUIRED_HOMOLOGY_FIELDS = [
    "source_candidate",
    "target_candidate",
    "family",
    "shared_features",
    "non_shared_features",
    "evidence_files",
    "decision_time_safe",
    "routing_use_allowed",
    "patch_authority_allowed",
    "repair_proof_allowed",
    "memory_lift_evidence_allowed",
    "count_gate_evidence_allowed",
    "audit_status",
]


def validate_homology_record(record: dict[str, object]) -> dict[str, object]:
    missing = [field for field in REQUIRED_HOMOLOGY_FIELDS if field not in record]
    safety = (
        record.get("decision_time_safe") is True
        and record.get("routing_use_allowed") is True
        and record.get("patch_authority_allowed") is False
        and record.get("repair_proof_allowed") is False
        and record.get("memory_lift_evidence_allowed") is False
        and record.get("count_gate_evidence_allowed") is False
        and record.get("audit_status") == "PASS"
    )
    return {"status": "PASS" if not missing and safety else "FAIL", "missing": missing, "routing_memory_only": safety}


def cross_family_homology_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "routing_memory_only": True,
        "patch_authority_allowed": False,
        "repair_proof_allowed": False,
        "memory_lift_evidence_allowed": False,
        "count_gate_evidence_allowed": False,
    }
