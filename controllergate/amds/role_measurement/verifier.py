from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts import ROLE_CONTRACTS


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_role_measurement(receipt: dict[str, Any]) -> dict[str, Any]:
    role = str(receipt.get("semantic_role", ""))
    required = ROLE_CONTRACTS.get(role)
    if required is None:
        return {"status": "BLOCK", "blocker": "unknown_role", "semantic_role": role}
    measured = receipt.get("measurement", {})
    reasons = []
    if receipt.get("producer_identity") == f"controllergate.amds.role_measurement.verifier:{role}":
        reasons.append("producer_verifier_identity_collision")
    if receipt.get("measurement_hash") != _hash(measured):
        reasons.append("measurement_hash_mismatch")
    if receipt.get("status") == "PASS" and any(measured.get(key) in (None, "", [], {}) for key in required):
        reasons.append("semantic_role_incomplete")
    if receipt.get("status") == "PASS" and receipt.get("forbidden_fields"):
        reasons.append("forbidden_evidence_present")
    return {
        "status": "PASS" if not reasons and receipt.get("status") == "PASS" else "BLOCK",
        "blocker": None if not reasons and receipt.get("status") == "PASS" else (reasons[0] if reasons else receipt.get("blocker")),
        "candidate_id": receipt.get("candidate_id"),
        "semantic_role": role,
        "measurement_hash": receipt.get("measurement_hash"),
        "verifier_identity": f"controllergate.amds.role_measurement.verifier:{role}",
        "verifier_code_hash": _hash({"verifier": "controllergate.amds.role_measurement.verifier", "role": role}),
        "verifier_execution_receipt": _hash({"measurement_hash": receipt.get("measurement_hash"), "role": role}),
        "producer_identity": receipt.get("producer_identity"),
        "independent_identity": receipt.get("producer_identity") != f"controllergate.amds.role_measurement.verifier:{role}",
        "verification_reasons": reasons,
        "execution_depth": "independent_semantic_role_verification",
        "authority_allowed": "AMDS episode eligibility only",
        "authority_forbidden": ["terminal class", "repair authorization"],
    }
