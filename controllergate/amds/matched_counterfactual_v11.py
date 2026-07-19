"""Semantic pair validation for Batch101 and later counterfactual programs."""

from __future__ import annotations

from typing import Any


PAIR_STATUSES = {
    "INCIDENT_NOT_EXECUTED",
    "CONTROL_NOT_EXECUTED",
    "INCIDENT_NOT_MATERIALIZED",
    "CONTROL_NOT_MATERIALIZED",
    "REPLAY_NONREPRODUCIBLE",
    "HELD_INVARIANT_FAILURE",
    "VALID_SINGLE_FACTOR_PAIR",
    "VALID_FACTORIAL_PAIR",
    "VALID_LIMITED_PROVIDER_PAIR",
    "PROVIDER_UNAVAILABLE",
}


def validate_pair(
    program: dict[str, Any],
    incident: dict[str, Any] | None,
    control: dict[str, Any] | None,
    *,
    held_invariants_verified: bool,
    factorial_complete: bool,
) -> dict[str, Any]:
    """Classify a pair using executed semantic facts, never receipt presence alone."""

    if incident is None or incident.get("execution_status") != "EXECUTED":
        status = "INCIDENT_NOT_EXECUTED"
    elif control is None or control.get("execution_status") != "EXECUTED":
        status = "CONTROL_NOT_EXECUTED"
    elif incident.get("provider_mode") == "UNAVAILABLE_PROVIDER" or control.get("provider_mode") == "UNAVAILABLE_PROVIDER":
        status = "PROVIDER_UNAVAILABLE"
    elif not incident.get("predicate_result", False):
        status = "INCIDENT_NOT_MATERIALIZED"
    elif not control.get("predicate_result", False):
        status = "CONTROL_NOT_MATERIALIZED"
    elif not incident.get("semantically_reproducible", False) or not control.get("semantically_reproducible", False):
        status = "REPLAY_NONREPRODUCIBLE"
    elif not held_invariants_verified:
        status = "HELD_INVARIANT_FAILURE"
    elif program.get("pair_kind") in {"factorial", "factorial_diagnostic"}:
        status = "VALID_FACTORIAL_PAIR" if factorial_complete else "HELD_INVARIANT_FAILURE"
    elif any(row.get("provider_mode") != "EXACT_PROVIDER" for row in (incident, control)):
        status = "VALID_LIMITED_PROVIDER_PAIR"
    else:
        status = "VALID_SINGLE_FACTOR_PAIR"
    return {
        "program_id": program["program_id"],
        "candidate_id": program["candidate_id"],
        "status": status,
        "incident_cell_id": program["incident_cell"]["cell_id"],
        "control_cell_id": program["control_cell"]["cell_id"],
        "held_invariants_verified": held_invariants_verified,
        "factorial_complete": factorial_complete,
        "ownership_supported": False,
        "authority_allowed": "pair validity at observed execution depth",
        "authority_forbidden": ["ownership without necessity and alternative exclusion", "patch", "repair count"],
    }
