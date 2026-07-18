from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Any

from .causal_hypergraph import BoardCellV1, CellState


RESOLVED_ENVIRONMENT_STATES = {CellState.VERIFIED_TRUE, CellState.VERIFIED_FALSE, CellState.NOT_APPLICABLE}
UNRESOLVED_CAUSAL_STATES = {CellState.UNRESOLVED, CellState.CONTRADICTED}


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class EnvironmentExhaustedHandoffV1:
    candidate_id: str
    run_id: str
    frame_hash: str
    boundary_cell_ids: tuple[str, ...]
    measurement_receipts: tuple[str, ...]
    verifier_receipts: tuple[str, ...]
    environment_alignment_plan_hash: str
    observer_state_hash: str
    creation_transition: str
    invalidation_condition: str
    handoff_hash: str
    authority_allowed: tuple[str, ...]
    authority_forbidden: tuple[str, ...]

    def record(self) -> dict[str, Any]:
        return asdict(self)


def emit_environment_exhausted_handoff(
    *,
    environment_cells: Iterable[BoardCellV1],
    causal_cells: Iterable[BoardCellV1],
    environment_alignment_plan_hash: str,
    observer_state_hash: str,
) -> EnvironmentExhaustedHandoffV1:
    environment = list(environment_cells); causal = list(causal_cells)
    if not environment:
        raise ValueError("environment handoff requires an enumerated applicable boundary")
    identity = {(row.candidate_id, row.run_id, row.frame_id) for row in environment + causal}
    if len(identity) != 1:
        raise ValueError("candidate/run/frame identities do not match")
    if any(row.state not in RESOLVED_ENVIRONMENT_STATES for row in environment):
        raise ValueError("applicable environment cells are unresolved or contradicted")
    if any(not row.producer_execution_receipt or not row.verifier_execution_receipt for row in environment):
        raise ValueError("environment cells require executed producer and verifier receipts")
    if any(row.producer_execution_receipt == row.verifier_execution_receipt for row in environment):
        raise ValueError("environment producer and verifier receipts must be distinct")
    if any(not row.parent_evidence for row in environment):
        raise ValueError("environment receipt hashes must resolve to raw evidence")
    unresolved = [row for row in causal if row.state in UNRESOLVED_CAUSAL_STATES and (row.cell_class.endswith("CONTACT") or row.cell_class.startswith("OWNERSHIP_"))]
    if not unresolved:
        raise ValueError("handoff requires unresolved causal ownership or contact")
    candidate_id, run_id, frame_hash = next(iter(identity))
    payload = {
        "candidate_id": candidate_id,
        "run_id": run_id,
        "frame_hash": frame_hash,
        "boundary_cell_ids": sorted(row.cell_id for row in environment),
        "measurement_receipts": sorted(row.producer_execution_receipt for row in environment),
        "verifier_receipts": sorted(row.verifier_execution_receipt for row in environment),
        "environment_alignment_plan_hash": environment_alignment_plan_hash,
        "observer_state_hash": observer_state_hash,
    }
    return EnvironmentExhaustedHandoffV1(
        candidate_id, run_id, frame_hash, tuple(payload["boundary_cell_ids"]), tuple(payload["measurement_receipts"]),
        tuple(payload["verifier_receipts"]), environment_alignment_plan_hash, observer_state_hash,
        "all_applicable_environment_dimensions_independently_verified_with_unresolved_causal_contact",
        "invalidate_on_any_bound_environment_or_observer_identity_change", f"environment-handoff:{_hash(payload)}",
        ("stop generic environment hypotheses", "handoff to local causal-contact topology", "compile causal-contact probes"),
        ("cell state transition", "verified causal fact", "ownership terminal", "source ownership", "repair license", "patch", "count mutation", "release mutation"),
    )


def validate_handoff(handoff: EnvironmentExhaustedHandoffV1, current_identity: Mapping[str, object]) -> dict[str, object]:
    bound = {
        "frame_hash": handoff.frame_hash,
        "environment_alignment_plan_hash": handoff.environment_alignment_plan_hash,
        "observer_state_hash": handoff.observer_state_hash,
        "boundary_cell_ids": list(handoff.boundary_cell_ids),
        "measurement_receipts": list(handoff.measurement_receipts),
        "verifier_receipts": list(handoff.verifier_receipts),
    }
    changed = sorted(key for key, value in bound.items() if current_identity.get(key) != value)
    return {"status": "INVALIDATED" if changed else "PASS", "changed_identities": changed, "handoff_hash": handoff.handoff_hash}


def environment_probe_allowed_after_handoff(reason: str) -> bool:
    return reason in {"new_raw_boundary_cell", "verified_modality_conflict", "bound_cell_invalidated_or_contradicted", "omitted_source_declared_prerequisite"}
