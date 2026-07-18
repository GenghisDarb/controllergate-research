from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts import ROLE_CONTRACTS


FORBIDDEN_EVIDENCE_KEYS = frozenset(
    {
        "post_repair", "post_validation", "gold_patch", "future_revision", "fixed_revision",
        "repair_outcome", "count_outcome", "terminal_class", "expected_terminal", "patch_text",
    }
)


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def measure_role(candidate_id: str, role: str, raw_measurement: dict[str, Any]) -> dict[str, Any]:
    """Produce a role-specific decision-time receipt or an exact block."""
    if role not in ROLE_CONTRACTS:
        raise ValueError(f"unknown role: {role}")
    required = ROLE_CONTRACTS[role]
    missing = [key for key in required if raw_measurement.get(key) in (None, "", [], {})]
    forbidden = sorted(key for key in FORBIDDEN_EVIDENCE_KEYS if raw_measurement.get(key) not in (None, False, "", [], {}))
    freshness = (
        raw_measurement.get("fresh_batch093_measurement") is True
        or raw_measurement.get("fresh_measurement_epoch") in {"batch095", "batch097"}
    )
    status = "PASS" if not missing and not forbidden and freshness else "BLOCK"
    blocker = None
    if not freshness:
        blocker = "fresh_batch093_role_measurement_missing"
    elif forbidden:
        blocker = "future_or_outcome_evidence_detected"
    elif missing:
        blocker = "role_semantic_fields_missing"
    measured = {key: raw_measurement.get(key) for key in required if key in raw_measurement}
    return {
        "status": status,
        "blocker": blocker,
        "candidate_id": candidate_id,
        "semantic_role": role,
        "required_fields": list(required),
        "missing_fields": missing,
        "forbidden_fields": forbidden,
        "measurement": measured,
        "measurement_hash": _hash(measured),
        "producer_identity": f"controllergate.amds.role_measurement.producer:{role}",
        "producer_code_hash": _hash({"producer": "controllergate.amds.role_measurement.producer", "role": role}),
        "producer_execution_receipt": raw_measurement.get("producer_execution_receipt"),
        "raw_operation_hash": raw_measurement.get("raw_operation_hash"),
        "raw_output_hashes": raw_measurement.get("raw_output_hashes", []),
        "freshness": raw_measurement.get("fresh_measurement_epoch", "batch093"),
        "decision_time_safe": not forbidden,
        "revocation_state": "CURRENT",
        "parent_evidence": raw_measurement.get("parent_evidence", []),
        "execution_depth": "fresh_role_specific_measurement" if status == "PASS" else "role_precondition_audit",
        "semantic_scope": role,
        "authority_allowed": "AMDS episode eligibility only",
        "authority_forbidden": ["terminal class", "repair authorization", "truth join"],
    }
