from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record
from .board import build_board
from .types import AmdsCell, AmdsConstraint, AmdsEdge, CellState


REFERENCE_ROLES = ("incident", "source_identity", "environment", "command", "failure")
CONTACTS = (
    "artifact_custody", "candidate_identity", "source_revision", "failure_signature",
    "target_test", "command_authority", "harness_origin", "runner_origin",
    "target_import_origin", "provider_and_cofactor", "environment_compartment",
    "workspace_and_execution_boundary", "source_and_failure_topology", "rollback_and_proof_path",
)
ACTIVATION_GATES = (
    "baseline_preservation", "candidate_recovery", "evidence_firewall",
    "agent_state", "proof_ledger", "patch_license",
)
HYPOTHESES = ("source_owned", "environment_owned", "test_or_interpreter_owned")


def build_board_from_evidence(evidence_bundle: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(evidence_bundle.get("candidate_id") or "")
    candidate_sha = str(evidence_bundle.get("candidate_sha") or "")
    if not candidate_id or len(candidate_sha) != 40:
        raise ValueError("candidate_identity_incomplete")
    evidence_hash = hash_record(evidence_bundle)
    cells: list[AmdsCell] = []
    for role in REFERENCE_ROLES:
        cells.append(AmdsCell(f"role:{role}", "reference_role", candidate_id, (evidence_hash,), state=CellState.RESOLVED.value))
    for contact in CONTACTS:
        established = bool(evidence_bundle.get("contacts", {}).get(contact))
        cells.append(AmdsCell(f"contact:{contact}", "contact", candidate_id, (evidence_hash,), state=CellState.RESOLVED.value if established else CellState.UNKNOWN.value, allowed_probes=("metadata_inspection", "source_tree_inspection")))
    for gate in ACTIVATION_GATES:
        passed = evidence_bundle.get("activation_gates", {}).get(gate) == "PASS"
        cells.append(AmdsCell(f"gate:{gate}", "activation_gate", candidate_id, (evidence_hash,), state=CellState.RESOLVED.value if passed else CellState.BLOCKED.value))
    for hypothesis in HYPOTHESES:
        cells.append(AmdsCell(f"hypothesis:{hypothesis}", "failure_hypothesis", candidate_id, (evidence_hash,), associated_hypotheses=(hypothesis,), allowed_probes=("failure_signature_replay", "source_tree_inspection")))
    cells.append(AmdsCell("action:source_patch", "bounded_action", candidate_id, (evidence_hash,), state=CellState.BLOCKED.value, forbidden_actions=("source_patch",)))
    edges: list[AmdsEdge] = []
    ordered = [f"contact:{item}" for item in CONTACTS]
    for index in range(len(ordered) - 1):
        edges.append(AmdsEdge(f"contact-edge-{index:02d}", ordered[index], ordered[index + 1], "evidence_sequence"))
    constraints = [
        AmdsConstraint("ownership-exactly-one", "exactly_one", tuple(f"hypothesis:{item}" for item in HYPOTHESES), (evidence_hash,)),
        AmdsConstraint("source-requires-failure", "requires", ("hypothesis:source_owned", "contact:failure_signature"), (evidence_hash,)),
        AmdsConstraint("source-excludes-interpreter", "excludes", ("hypothesis:source_owned", "hypothesis:test_or_interpreter_owned"), (evidence_hash,)),
        AmdsConstraint("environment-implies-provider", "implies", ("hypothesis:environment_owned", "contact:provider_and_cofactor"), (evidence_hash,)),
        AmdsConstraint("ownership-mutual", "mutually_exclusive", tuple(f"hypothesis:{item}" for item in HYPOTHESES), (evidence_hash,)),
        AmdsConstraint("ownership-at-least-one", "at_least_one", tuple(f"hypothesis:{item}" for item in HYPOTHESES), (evidence_hash,)),
        AmdsConstraint("ownership-at-most-one", "at_most_one", tuple(f"hypothesis:{item}" for item in HYPOTHESES), (evidence_hash,)),
        AmdsConstraint("provider-boundary", "provider_dependency", ("action:source_patch", "contact:provider_and_cofactor"), (evidence_hash,)),
        AmdsConstraint("environment-boundary", "environment_dependency", ("action:source_patch", "contact:environment_compartment"), (evidence_hash,)),
        AmdsConstraint("source-ownership-boundary", "source_ownership", ("action:source_patch", "hypothesis:source_owned"), (evidence_hash,)),
        AmdsConstraint("provenance-boundary", "provenance_boundary", ("action:source_patch", "contact:artifact_custody", "contact:source_revision"), (evidence_hash,)),
        AmdsConstraint("interlock-boundary", "interlock_boundary", ("action:source_patch", "gate:evidence_firewall", "gate:agent_state"), (evidence_hash,)),
        AmdsConstraint("authorization-boundary", "authorization_boundary", ("action:source_patch", "gate:patch_license"), (evidence_hash,)),
        AmdsConstraint("rollback-boundary", "rollback_boundary", ("action:source_patch", "contact:rollback_and_proof_path", "gate:proof_ledger"), (evidence_hash,)),
    ]
    board = build_board(candidate_id, cells, edges, constraints)
    board["candidate_sha"] = candidate_sha
    board["reference_core"] = list(REFERENCE_ROLES)
    board["contact_ledger"] = list(CONTACTS)
    board["activation_gate_ledger"] = list(ACTIVATION_GATES)
    board["hypothesis_state"] = {
        "probabilities": {item: 1.0 / len(HYPOTHESES) for item in HYPOTHESES},
        "classification": "structural_uniform_uncalibrated",
        "events": [],
    }
    board.pop("board_hash", None)
    board["board_hash"] = hash_record(board)
    return board
