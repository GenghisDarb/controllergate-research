from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


def identity(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


class CellState(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    VERIFIED_TRUE = "VERIFIED_TRUE"
    VERIFIED_FALSE = "VERIFIED_FALSE"
    INFERRED_TRUE = "INFERRED_TRUE"
    INFERRED_FALSE = "INFERRED_FALSE"
    CONTRADICTED = "CONTRADICTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


CELL_CLASSES = (
    "ENVIRONMENT_BOUNDARY", "SOURCE_ARTIFACT", "SOURCE_CONTACT", "PROVIDER_CONTACT", "RUNNER_CONTACT",
    "HARNESS_FIXTURE_CONTACT", "SERVICE_TRANSPORT_CONTACT", "EXPECTATION_ORACLE_CONTACT", "PROCESS_PRODUCT_CONTACT",
    "MODALITY_OBSERVATION", "OWNERSHIP_SOURCE", "OWNERSHIP_PROVIDER", "OWNERSHIP_ENVIRONMENT_PLATFORM",
    "OWNERSHIP_RUNNER", "OWNERSHIP_HARNESS_FIXTURE", "OWNERSHIP_SERVICE_TRANSPORT", "OWNERSHIP_TEST_EXPECTATION",
    "OWNERSHIP_MIXED", "INSUFFICIENT_EVIDENCE", "MODALITY_CONFLICT", "STAGNATION",
)
RELATIONS = (
    "REQUIRES", "PRODUCES", "CALLS", "IMPORTS", "LOADS_PLUGIN", "USES_FIXTURE", "WRAPS", "CONFIGURES", "EXECUTES",
    "EMITS", "ASSERTS", "MODIFIES", "TRANSLOCATES", "DIRECT_CONTACT", "INFERRED_CONTACT", "COUNTERFACTUAL_OF",
    "PROJECTION_COUPLED", "SUPPORTS", "NEGATES", "MUTUALLY_EXCLUSIVE", "CO_DEPENDENT", "CONTRADICTS", "RECOVERS_TO",
)


@dataclass(frozen=True)
class BoardCellV1:
    candidate_id: str
    run_id: str
    frame_id: str
    cell_class: str
    subject: str
    state: CellState
    parent_evidence: tuple[str, ...]
    producer_execution_receipt: str
    verifier_execution_receipt: str
    semantic_scope: str
    authority_allowed: str
    authority_forbidden: tuple[str, ...]
    reopen_condition: str
    cell_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.cell_class not in CELL_CLASSES:
            raise ValueError(f"unknown BoardCell class {self.cell_class}")
        if self.state != CellState.UNRESOLVED and (not self.parent_evidence or not self.producer_execution_receipt or not self.verifier_execution_receipt):
            raise ValueError("resolved BoardCell requires specific producer, verifier, and evidence")
        value = [self.candidate_id, self.run_id, self.frame_id, self.cell_class, self.subject, self.parent_evidence]
        object.__setattr__(self, "cell_id", f"cell:{identity(value)}")

    def record(self) -> dict[str, Any]:
        value = asdict(self); value["state"] = self.state.value; return value


@dataclass(frozen=True)
class BoardEdgeV1:
    candidate_id: str
    run_id: str
    frame_id: str
    source_cell_id: str
    target_cell_id: str
    relation: str
    parent_evidence: tuple[str, ...]
    producer_execution_receipt: str
    verifier_execution_receipt: str
    semantic_scope: str
    authority_allowed: str
    authority_forbidden: tuple[str, ...]
    reopen_condition: str
    edge_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.relation not in RELATIONS:
            raise ValueError(f"unknown BoardEdge relation {self.relation}")
        if not self.parent_evidence or not self.producer_execution_receipt or not self.verifier_execution_receipt:
            raise ValueError("BoardEdge requires raw parents and independently executed verification")
        if self.producer_execution_receipt == self.verifier_execution_receipt:
            raise ValueError("BoardEdge producer and verifier receipts must differ")
        object.__setattr__(self, "edge_id", f"edge:{identity([self.source_cell_id, self.target_cell_id, self.relation, self.parent_evidence])}")

    def record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CausalRegionV1:
    candidate_id: str
    region_id: str
    cell_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    unresolved_cell_ids: tuple[str, ...]
    structural_parent_hash: str
    reopen_condition: str

    def record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectionPairV1:
    candidate_id: str
    pair_id: str
    side_a_operation: str
    side_b_operation: str
    side_a_observation: str
    side_b_observation: str
    side_a_verification: str
    side_b_verification: str
    matched_invariants: tuple[str, ...]
    conflicting_dimensions: tuple[str, ...]
    unresolved_dimensions: tuple[str, ...]
    invalid_comparison_reasons: tuple[str, ...]
    narrow_probe_reuse_allowed: bool
    terminal_transfer_allowed: bool = False

    def __post_init__(self) -> None:
        if self.side_a_operation == self.side_b_operation or self.side_a_observation == self.side_b_observation:
            raise ValueError("ProjectionPair requires two executed sides")
        if self.terminal_transfer_allowed:
            raise ValueError("terminal transfer is forbidden")

    def record(self) -> dict[str, Any]:
        return asdict(self)


def connected_regions(candidate_id: str, cells: Iterable[BoardCellV1], edges: Iterable[BoardEdgeV1]) -> list[CausalRegionV1]:
    cell_rows = list(cells); edge_rows = list(edges); adjacency: dict[str, set[str]] = {row.cell_id: set() for row in cell_rows}
    for edge in edge_rows:
        adjacency.setdefault(edge.source_cell_id, set()).add(edge.target_cell_id)
        adjacency.setdefault(edge.target_cell_id, set()).add(edge.source_cell_id)
    by_id = {row.cell_id: row for row in cell_rows}; remaining = set(by_id); regions = []
    while remaining:
        seed = min(remaining); stack = [seed]; component: set[str] = set()
        while stack:
            current = stack.pop()
            if current in component: continue
            component.add(current); stack.extend(sorted(adjacency.get(current, set()).difference(component)))
        remaining.difference_update(component)
        region_edges = [edge.edge_id for edge in edge_rows if edge.source_cell_id in component and edge.target_cell_id in component]
        unresolved = [cell_id for cell_id in component if by_id[cell_id].state in {CellState.UNRESOLVED, CellState.CONTRADICTED}]
        regions.append(CausalRegionV1(candidate_id, f"region:{identity(sorted(component))}", tuple(sorted(component)), tuple(sorted(region_edges)), tuple(sorted(unresolved)), identity([sorted(component), sorted(region_edges)]), "execute a legal source-bound probe for unresolved contacts"))
    return regions


def compile_boundary_cells(candidate: Mapping[str, Any], measurement_receipts: Iterable[Mapping[str, Any]], verification_receipts: Iterable[Mapping[str, Any]]) -> list[BoardCellV1]:
    measurements = {row["dimension"]: row for row in measurement_receipts if row.get("candidate_id") == candidate["candidate_id"]}
    verifications = {row["dimension"]: row for row in verification_receipts if row.get("candidate_id") == candidate["candidate_id"]}
    rows = []
    for dimension in sorted(set(measurements) | set(verifications)):
        measurement = measurements.get(dimension, {}); verification = verifications.get(dimension, {})
        verified = verification.get("status") == "PASS" and verification.get("measurement_receipt") == measurement.get("receipt_id") and verification.get("verifier_receipt") != measurement.get("receipt_id")
        rows.append(BoardCellV1(
            candidate_id=str(candidate["candidate_id"]), run_id=str(candidate["run_id"]), frame_id=str(candidate["frame_id"]),
            cell_class="ENVIRONMENT_BOUNDARY", subject=dimension, state=CellState.VERIFIED_TRUE if verified else CellState.UNRESOLVED,
            parent_evidence=tuple(filter(None, (measurement.get("raw_evidence_hash"),))), producer_execution_receipt=str(measurement.get("receipt_id", "")), verifier_execution_receipt=str(verification.get("verifier_receipt", "")),
            semantic_scope=f"boundary dimension {dimension}", authority_allowed="environment uncertainty only", authority_forbidden=("source ownership", "repair authority"), reopen_condition=str(verification.get("reopen_condition", f"remeasure {dimension}")),
        ))
    return rows


def board_authority_audit(cells: Iterable[BoardCellV1], edges: Iterable[BoardEdgeV1]) -> dict[str, Any]:
    cell_rows = list(cells); edge_rows = list(edges)
    lacking_specific = [row.cell_id for row in cell_rows if row.state != CellState.UNRESOLVED and (not row.parent_evidence or not row.producer_execution_receipt or not row.verifier_execution_receipt)]
    graph_hash_verifiers = [row.edge_id for row in edge_rows if row.verifier_execution_receipt.startswith("graph:") or row.verifier_execution_receipt == row.producer_execution_receipt]
    empty_derivation_ownership = [row.cell_id for row in cell_rows if row.cell_class.startswith("OWNERSHIP_") and not row.parent_evidence]
    return {"status": "PASS" if not (lacking_specific or graph_hash_verifiers or empty_derivation_ownership) else "BLOCK", "boundary_cells_lacking_specific_evidence": lacking_specific, "graph_hash_as_verifier_edges": graph_hash_verifiers, "empty_derivation_ownership_cells": empty_derivation_ownership}
