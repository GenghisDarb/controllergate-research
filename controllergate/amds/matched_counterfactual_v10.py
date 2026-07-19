"""Candidate-bound matched counterfactual contracts and evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any


PAIR_CLASSIFICATIONS = {
    "VALID_SINGLE_FACTOR_PAIR",
    "VALID_FACTORIAL_INTERACTION",
    "SENSITIVITY_ONLY",
    "CONFOUNDED_PAIR",
    "INCIDENT_NOT_MATERIALIZED",
    "CONTROL_NOT_MATERIALIZED",
    "NONREPRODUCIBLE",
    "BLOCKED_PROVIDER_UNAVAILABLE",
}

EVIDENCE_LEVELS = {
    "PRESENCE_VERIFIED",
    "CONTACT_VERIFIED",
    "CORRELATION_VERIFIED",
    "DIMENSION_SENSITIVITY_VERIFIED",
    "NECESSITY_SUPPORTED",
    "SUFFICIENCY_SUPPORTED",
    "INTERACTION_SUPPORTED",
    "OWNERSHIP_SUPPORTED",
}


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_program(program: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    required = {
        "program_id", "candidate_id", "sub_incident_id", "source_capsule_hash",
        "provider_capsule_ids", "incident_cell", "control_cell", "additional_exclusion_cells",
        "factor_names", "factor_values", "held_invariants", "changed_dimensions",
        "incident_predicate", "control_predicate", "replay_count", "execution_order",
        "resource_budget", "authority_allowed", "authority_forbidden", "program_hash",
    }
    missing = sorted(required - program.keys())
    if missing:
        blockers.append("missing_fields:" + ",".join(missing))
    without_hash = {key: value for key, value in program.items() if key != "program_hash"}
    if program.get("program_hash") != canonical_hash(without_hash):
        blockers.append("program_hash_mismatch")
    if program.get("replay_count", 0) < 2:
        blockers.append("insufficient_clean_replays")
    if not program.get("changed_dimensions"):
        blockers.append("changed_dimension_missing")
    if any(marker in json.dumps(program).lower() for marker in ("sealed_truth", "gold_patch", "accepted_fix")):
        blockers.append("forbidden_execution_input")
    return blockers


@dataclass(frozen=True)
class MatchedCounterfactualEvidenceV2:
    pair_id: str
    program_id: str
    candidate_id: str
    sub_incident_id: str
    factor_registry: dict[str, Any]
    incident_cell_id: str
    control_cell_id: str
    source_capsule_hashes: list[str]
    provider_capsule_hashes: list[str]
    fixture_hashes: list[str]
    command_hashes: list[str]
    environment_hashes: list[str]
    held_invariants: list[str]
    changed_dimensions: list[str]
    single_factor_status: str
    factorial_status: str
    incident_materialized: bool
    control_materialized: bool
    incident_predicate: dict[str, Any]
    control_predicate: dict[str, Any]
    incident_observation_ids: list[str]
    control_observation_ids: list[str]
    semantic_verifier_receipts: list[str]
    outcome_difference: bool
    effect_direction: str
    replay_consistency: str
    necessity_supported: bool
    sufficiency_supported: bool
    interaction_supported: bool
    alternative_exclusions: list[str]
    unresolved_alternatives: list[str]
    evidence_level: str
    ownership_class_proposal: str
    ownership_supported: bool
    authority_allowed: str
    authority_forbidden: list[str]

    def __post_init__(self) -> None:
        if self.single_factor_status not in PAIR_CLASSIFICATIONS:
            raise ValueError("invalid pair classification")
        if self.evidence_level not in EVIDENCE_LEVELS:
            raise ValueError("invalid evidence level")
        if self.ownership_supported:
            if self.evidence_level != "OWNERSHIP_SUPPORTED":
                raise ValueError("ownership requires ownership evidence level")
            if not (self.necessity_supported or self.sufficiency_supported):
                raise ValueError("ownership requires necessity or sufficiency")
            if self.unresolved_alternatives:
                raise ValueError("ownership cannot retain unresolved alternatives")
            if not (self.incident_materialized and self.control_materialized):
                raise ValueError("ownership requires materialized incident and control")

    def record(self) -> dict[str, Any]:
        row = asdict(self)
        row["record_hash"] = canonical_hash(row)
        return row


def conservative_evidence_from_cells(
    *, program: dict[str, Any], incident: dict[str, Any] | None, control: dict[str, Any] | None,
) -> MatchedCounterfactualEvidenceV2:
    incident_materialized = bool(incident and incident.get("predicate_satisfied"))
    control_materialized = bool(control and control.get("predicate_satisfied"))
    if not incident:
        pair_status = "INCIDENT_NOT_MATERIALIZED"
    elif not control:
        pair_status = "CONTROL_NOT_MATERIALIZED"
    elif incident.get("provider_unavailable") or control.get("provider_unavailable"):
        pair_status = "BLOCKED_PROVIDER_UNAVAILABLE"
    elif incident.get("reproducibility_status") != "REPRODUCIBLE" or control.get("reproducibility_status") != "REPRODUCIBLE":
        pair_status = "NONREPRODUCIBLE"
    elif len(program["changed_dimensions"]) == 1:
        pair_status = "VALID_SINGLE_FACTOR_PAIR"
    else:
        pair_status = "VALID_FACTORIAL_INTERACTION"
    outcome_difference = bool(incident and control and incident.get("semantic_observation") != control.get("semantic_observation"))
    sensitivity = pair_status in {"VALID_SINGLE_FACTOR_PAIR", "VALID_FACTORIAL_INTERACTION"} and outcome_difference
    evidence_level = "DIMENSION_SENSITIVITY_VERIFIED" if sensitivity else "PRESENCE_VERIFIED"
    unresolved = [] if sensitivity else ["matched incident/control outcome difference not established"]
    return MatchedCounterfactualEvidenceV2(
        pair_id=f"pair:{canonical_hash([program['program_id'], 'primary'])}",
        program_id=program["program_id"], candidate_id=program["candidate_id"],
        sub_incident_id=program["sub_incident_id"], factor_registry=dict(program["factor_values"]),
        incident_cell_id=program["incident_cell"]["cell_id"], control_cell_id=program["control_cell"]["cell_id"],
        source_capsule_hashes=[program["source_capsule_hash"]],
        provider_capsule_hashes=list(program["provider_capsule_ids"]),
        fixture_hashes=[program["incident_cell"]["fixture_hash"], program["control_cell"]["fixture_hash"]],
        command_hashes=[program["incident_cell"]["command_hash"], program["control_cell"]["command_hash"]],
        environment_hashes=[program["incident_cell"]["environment_hash"], program["control_cell"]["environment_hash"]],
        held_invariants=list(program["held_invariants"]), changed_dimensions=list(program["changed_dimensions"]),
        single_factor_status=pair_status, factorial_status=pair_status if len(program["changed_dimensions"]) > 1 else "NOT_APPLICABLE",
        incident_materialized=incident_materialized, control_materialized=control_materialized,
        incident_predicate=dict(program["incident_predicate"]), control_predicate=dict(program["control_predicate"]),
        incident_observation_ids=[incident["operation_id"]] if incident else [],
        control_observation_ids=[control["operation_id"]] if control else [],
        semantic_verifier_receipts=[row["semantic_verifier_receipt"] for row in (incident, control) if row],
        outcome_difference=outcome_difference, effect_direction="incident_to_control" if outcome_difference else "not_established",
        replay_consistency="REPRODUCIBLE" if incident and control and all(row.get("reproducibility_status") == "REPRODUCIBLE" for row in (incident, control)) else "NOT_ESTABLISHED",
        necessity_supported=False, sufficiency_supported=False, interaction_supported=False,
        alternative_exclusions=[], unresolved_alternatives=unresolved,
        evidence_level=evidence_level, ownership_class_proposal="INSUFFICIENT_EVIDENCE",
        ownership_supported=False,
        authority_allowed="sensitivity evidence at the recorded level",
        authority_forbidden=["ownership escalation", "repair", "repair count", "release"],
    )
