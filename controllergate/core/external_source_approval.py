from __future__ import annotations

ALLOWED_EXTERNAL_SOURCE_USES = [
    "source_custody",
    "command_boundary_recovery",
    "manual_artifact_provenance",
    "runtime_connector_planning",
    "readiness_backlog",
]

FORBIDDEN_EXTERNAL_SOURCE_USES = [
    "patch_guidance",
    "future_fix_leakage",
    "gold_patch_substitute",
    "repair_proof",
    "count_gate",
    "memory_lift",
]


def external_source_approval_schema() -> dict[str, object]:
    return {
        "status": "PASS",
        "required_fields": [
            "candidate_id",
            "source_url",
            "source_type",
            "why_source_is_needed",
            "decision_time_safety_concern",
            "hash_provenance_needed",
            "allowed_use",
            "forbidden_use",
            "approval_condition",
        ],
        "allowed_use": ALLOWED_EXTERNAL_SOURCE_USES,
        "forbidden_use": FORBIDDEN_EXTERNAL_SOURCE_USES,
    }


def build_external_source_request(
    *,
    candidate_id: str,
    source_url: str,
    source_type: str,
    why_source_is_needed: str,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "source_url": source_url,
        "source_type": source_type,
        "why_source_is_needed": why_source_is_needed,
        "decision_time_safety_concern": "must be tied to candidate-era source or manually verified artifact; no future fix content",
        "hash_provenance_needed": ["sha256", "retrieval_or_manual_handoff_path", "observed_at_or_before"],
        "allowed_use": ALLOWED_EXTERNAL_SOURCE_USES,
        "forbidden_use": FORBIDDEN_EXTERNAL_SOURCE_USES,
        "approval_condition": "hash_and_provenance_verified_without_forbidden_evidence",
        "audit_status": "PASS",
    }
