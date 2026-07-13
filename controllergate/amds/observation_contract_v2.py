from __future__ import annotations

from typing import Any

REQUIRED = (
    "probe_id", "probe_type", "registry_generation", "authorization_id", "executor_id",
    "input_evidence_hashes", "observation_class", "operation_status", "semantic_fact",
    "semantic_evidence_hash", "custody_verification", "semantic_verification",
    "supported_hypotheses", "refuted_hypotheses", "unchanged_hypotheses", "likelihood_basis",
    "prior_state_hash", "posterior_state_hash", "board_state_hash", "event_hash",
)


def validate_observation(record: dict[str, Any], *, expected_probe_id: str | None = None, expected_executor_id: str | None = None) -> dict[str, Any]:
    missing = [key for key in REQUIRED if record.get(key) is None]
    reasons: list[str] = []
    if missing:
        reasons.append("missing:" + ",".join(missing))
    if expected_probe_id is not None and record.get("probe_id") != expected_probe_id:
        reasons.append("probe_id_mismatch")
    if expected_executor_id is not None and record.get("executor_id") != expected_executor_id:
        reasons.append("executor_mismatch")
    if record.get("custody_verification") != "PASS":
        reasons.append("custody_verification_failed")
    if record.get("semantic_verification") != "PASS":
        reasons.append("semantic_verifier_failed")
    accepted = not reasons
    return {"status": "PASS" if accepted else "REJECT", "accepted": accepted, "reasons": reasons, "missing_fields": missing}
