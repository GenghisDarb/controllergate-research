from __future__ import annotations

import hashlib
import json
from typing import Any

REQUIRED_AST_HOMOLOGY_FIELDS = [
    "pattern_id",
    "source_candidate_id",
    "target_candidate_id",
    "source_repo_family",
    "target_repo_family",
    "source_language",
    "target_language",
    "source_ast_shape_hash",
    "target_ast_shape_hash",
    "source_symbol_roles",
    "target_symbol_roles",
    "control_flow_shape",
    "data_flow_shape",
    "exception_flow_shape",
    "import_dependency_shape",
    "test_to_source_contact_shape",
    "patch_shape_if_known",
    "source_repair_result",
    "target_repair_status",
    "transfer_allowed_use",
    "transfer_forbidden_use",
    "decision_time_safe",
    "memory_update_allowed",
    "memory_lift_evidence_allowed",
    "patch_authority_allowed",
    "count_gate_evidence_allowed",
    "audit_status",
]

ALLOWED_HOMOLOGY_USES = [
    "routing_memory_only",
    "candidate_prioritization",
    "preflight_probe_selection",
    "command_translation_review",
    "source_topology_search_prioritization",
    "future_memory_baseline_hypothesis",
]

FORBIDDEN_HOMOLOGY_USES = [
    "direct_patch_authorization",
    "count_increment",
    "duplicate_replay_substitute",
    "memory_lift_claim",
    "full_scoring_claim",
    "self_maintaining_claim",
    "gold_fixed_patch_substitute",
]


def shape_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def make_ast_homology_record(**fields: Any) -> dict[str, Any]:
    record = dict(fields)
    record.setdefault("transfer_allowed_use", ALLOWED_HOMOLOGY_USES)
    record.setdefault("transfer_forbidden_use", FORBIDDEN_HOMOLOGY_USES)
    record.setdefault("decision_time_safe", True)
    record.setdefault("memory_update_allowed", True)
    record.setdefault("memory_lift_evidence_allowed", False)
    record.setdefault("patch_authority_allowed", False)
    record.setdefault("count_gate_evidence_allowed", False)
    record.setdefault("audit_status", "PASS")
    return record


def validate_ast_homology_record(record: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_AST_HOMOLOGY_FIELDS if field not in record]
    errors: list[str] = []
    if record.get("patch_authority_allowed") is not False:
        errors.append("blocked_cross_family_homology_used_as_patch_authority")
    if record.get("count_gate_evidence_allowed") is not False:
        errors.append("homology_count_gate_evidence_forbidden")
    if record.get("memory_lift_evidence_allowed") is not False:
        errors.append("homology_memory_lift_evidence_forbidden")
    if record.get("decision_time_safe") is not True:
        errors.append("homology_not_decision_time_safe")
    return {"status": "PASS" if not missing and not errors else "FAIL", "missing": missing, "errors": errors}


def ast_homology_schema() -> dict[str, Any]:
    return {
        "status": "PASS",
        "required_fields": REQUIRED_AST_HOMOLOGY_FIELDS,
        "allowed_uses": ALLOWED_HOMOLOGY_USES,
        "forbidden_uses": FORBIDDEN_HOMOLOGY_USES,
        "patch_authority_allowed": False,
    }
