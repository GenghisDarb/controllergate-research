from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReferenceCoreState:
    role_id: str
    role: str
    evidence_hash: str
    verifier: str
    state_hash: str
    immutable: bool = True
    reopen_condition: str = "new_decision_time_safe_evidence"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContactRecord:
    contact_id: str
    canonical_role: str
    candidate_id: str
    evidence_inputs: tuple[str, ...]
    evidence_hashes: tuple[str, ...]
    handler_result: str
    verifier_result: str
    operation_status: str
    evidence_status: str
    gate_decision: str
    contact_state: str
    confidence: float
    unresolved_dimensions: tuple[str, ...] = ()
    interlocks: tuple[str, ...] = ()
    blocker: str | None = None
    reopen_conditions: tuple[str, ...] = ()
    prior_state_hash: str = ""
    post_state_hash: str = ""
    authority_class: str = "decision_time_repository_evidence"
    decision_time_status: str = "safe"
    missing_evidence: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContactLedger14:
    candidate_id: str
    contacts: tuple[ContactRecord, ...]
    ledger_hash: str

    def as_dict(self) -> dict[str, Any]:
        return {"candidate_id": self.candidate_id, "contacts": [item.as_dict() for item in self.contacts], "ledger_hash": self.ledger_hash}


@dataclass(frozen=True)
class LocalBrotNode:
    node_id: str
    node_class: str
    region: str
    evidence_hash: str


@dataclass(frozen=True)
class LocalBrotEdge:
    source: str
    target: str
    edge_class: str
    evidence_hash: str
    authority_class: str
    confidence: float
    interlock_status: str
    decision_time_safe: bool


@dataclass(frozen=True)
class LocalBrotGraph:
    candidate_id: str
    nodes: tuple[LocalBrotNode, ...]
    edges: tuple[LocalBrotEdge, ...]
    current_legal_recovery: str

    def as_dict(self) -> dict[str, Any]:
        return {"candidate_id": self.candidate_id, "nodes": [asdict(item) for item in self.nodes], "edges": [asdict(item) for item in self.edges], "current_legal_recovery": self.current_legal_recovery}


@dataclass(frozen=True)
class CouplingEdge:
    source_candidate: str
    target_candidate: str
    coupling_type: str
    evidence_hashes: tuple[str, ...]
    orthology_dimensions: tuple[str, ...]
    matched_dimensions: tuple[str, ...]
    conflicting_dimensions: tuple[str, ...]
    confidence: float
    transfer_allowed: bool
    transfer_forbidden_reason: str | None
    negative_transfer_risk: str
    interlock_verification: str


@dataclass(frozen=True)
class TotBrotGraph:
    candidate_ids: tuple[str, ...]
    edges: tuple[CouplingEdge, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"candidate_ids": list(self.candidate_ids), "edges": [asdict(item) for item in self.edges]}


@dataclass(frozen=True)
class BoundaryCoordinate:
    contact_role: str
    environment_dimension: str
    runtime_phase: str
    evidence_epoch: str = "decision_time"


@dataclass(frozen=True)
class BasinRecord:
    basin_id: str
    seed_edge_hash: str
    selected_by_evidence: bool
    dimensions: tuple[str, ...]


@dataclass(frozen=True)
class BoundaryVolume:
    candidate_id: str
    global_mask: dict[str, Any]
    candidate_mask: dict[str, Any]
    basins: tuple[BasinRecord, ...]
    cells: tuple[dict[str, Any], ...]
    claim_bearing: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {"candidate_id": self.candidate_id, "global_mask": self.global_mask, "candidate_mask": self.candidate_mask, "basins": [asdict(item) for item in self.basins], "cells": list(self.cells), "claim_bearing": self.claim_bearing}


@dataclass(frozen=True)
class TldLadderRecord:
    ladder_id: str
    candidate_id: str
    kind: str
    parent_ladder_id: str | None
    omega: tuple[str, ...]
    adjacency_topology: str
    is_null: bool
    eligible: bool
    seed: int
    source_evidence_hash: str
    contact_topology_size: int = 14
    tld_recursion_depth_N: int = 1
    notes: str = ""


@dataclass(frozen=True)
class TldNullRecord(TldLadderRecord):
    null_family: str = "role_permutation"


@dataclass(frozen=True)
class TldMetricRecord:
    ladder_id: str
    UI: str
    NSS: str
    SEP: str
    T_e: str
    S_e: str
    winner_N: str


@dataclass(frozen=True)
class ActivationLicense6:
    gates: tuple[dict[str, Any], ...]
    status: str
    patch_authority: bool = False


@dataclass(frozen=True)
class ProofObligationCell:
    source_contact: str
    destination_contact: str
    required_invariant: str
    allowed_change: str
    forbidden_change: str
    pre_state_evidence: str
    planned_post_state_evidence: str
    verification_method: str
    current_status: str
    blocker: str
    reopen_condition: str


@dataclass(frozen=True)
class ProofMatrix196:
    cells: tuple[ProofObligationCell, ...]
    status: str


@dataclass(frozen=True)
class TwistHolonomyRecord:
    origin_state_hash: str
    terminal_state_hash: str
    return_state_hash: str
    orientation_parity: int
    pre_post_role_mapping: dict[str, str]
    rollback_identity: str
    proof_ledger_identity: str
    information_preserved: tuple[str, ...]
    information_intentionally_reversed: tuple[str, ...]
    information_forbidden_from_transfer: tuple[str, ...]
    status: str
