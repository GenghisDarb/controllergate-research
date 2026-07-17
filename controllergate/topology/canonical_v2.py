from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from controllergate.state.integrity import canonical_hash


TEN_ROLES = ("source_revision", "source_tree", "test_tree", "provider_runtime_abi", "target_reproducer", "command", "runner", "harness", "incident_snapshot", "proof_release_parent")


@dataclass(frozen=True)
class EnvironmentAlignmentPlanV1:
    candidate_id: str
    frame_id: str
    frozen_before_target: bool
    dimensions: Mapping[str, str]
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    evidence_hashes: tuple[str, ...]

    @property
    def plan_hash(self) -> str:
        return canonical_hash(asdict(self))


@dataclass(frozen=True)
class TotBulbBoundaryVolumeV2:
    candidate_id: str
    cells: tuple[dict[str, Any], ...]
    alignment_plan_hash: str
    outcome_dependent_alignment_count: int = 0

    @property
    def volume_hash(self) -> str:
        return canonical_hash(asdict(self))


@dataclass(frozen=True)
class LocalBrotGraphV2:
    candidate_id: str
    nodes: tuple[dict[str, Any], ...]
    edges: tuple[dict[str, Any], ...]
    unresolved_cells: tuple[str, ...]
    legal_next_probes: tuple[str, ...]
    prohibited_actions: tuple[str, ...]

    @property
    def graph_hash(self) -> str:
        return canonical_hash(asdict(self))


@dataclass(frozen=True)
class CoupledTotBrotGraphV2:
    candidate_ids: tuple[str, ...]
    edges: tuple[dict[str, Any], ...]
    false_transfer_count: int

    @property
    def graph_hash(self) -> str:
        return canonical_hash(asdict(self))


def build_environment_boundary(candidate_id: str, frame_id: str, dimensions: Mapping[str, str], evidence_hashes: Iterable[str]) -> tuple[EnvironmentAlignmentPlanV1, TotBulbBoundaryVolumeV2]:
    plan = EnvironmentAlignmentPlanV1(candidate_id, frame_id, True, dict(sorted(dimensions.items())), ("materialize_verified_provider", "redirect_generated_outputs", "materialize_declared_cofactor"), ("source_mutation", "test_mutation", "candidate_replacement", "outcome_driven_retry", "future_evidence"), tuple(sorted(evidence_hashes)))
    cells = tuple({"dimension": key, "observed": value, "status": "VERIFIED" if value else "UNRESOLVED"} for key, value in sorted(dimensions.items()))
    return plan, TotBulbBoundaryVolumeV2(candidate_id, cells, plan.plan_hash)


def build_local_graph(candidate_id: str, role_receipts: Mapping[str, Mapping[str, Any]], contacts: Iterable[Mapping[str, Any]]) -> LocalBrotGraphV2:
    missing = tuple(role for role in TEN_ROLES if role not in role_receipts)
    nodes = tuple({"node_id": role, "node_class": "SEMANTIC_ROLE", "evidence_hash": role_receipts.get(role, {}).get("measurement_hash"), "status": "VERIFIED" if role in role_receipts else "UNRESOLVED"} for role in TEN_ROLES)
    edges = []
    for contact in contacts:
        if not contact.get("producer_receipt") or not contact.get("verifier_receipt"):
            continue
        edges.append({"source": contact["source"], "target": contact["target"], "contact_type": contact.get("contact_type", "executed_contact"), "producer_receipt": contact["producer_receipt"], "verifier_receipt": contact["verifier_receipt"], "direct": bool(contact.get("direct", False))})
    probes = tuple(f"measure_{role}" for role in missing)
    return LocalBrotGraphV2(candidate_id, nodes, tuple(edges), missing, probes, ("patch", "count", "truth_read", "candidate_substitution"))


def couple_graphs(graphs: Iterable[LocalBrotGraphV2], dimensions: Mapping[str, Mapping[str, str]]) -> CoupledTotBrotGraphV2:
    graphs = tuple(graphs); edges = []; false = 0
    for left, right in zip(graphs, graphs[1:]):
        left_dimensions = dimensions.get(left.candidate_id, {}); right_dimensions = dimensions.get(right.candidate_id, {})
        shared = sorted(set(left_dimensions) & set(right_dimensions))
        matched = [key for key in shared if left_dimensions[key] == right_dimensions[key]]
        conflicts = [key for key in shared if left_dimensions[key] != right_dimensions[key]]
        allowed = bool(matched) and not conflicts
        if not allowed: false += 1
        edges.append({"source_candidate": left.candidate_id, "target_candidate": right.candidate_id, "matched_dimensions": matched, "conflicting_dimensions": conflicts, "transfer_allowed": allowed, "authority_allowed": "provider hypothesis" if allowed else "none", "authority_forbidden": ["terminal", "repair", "count"], "positive_control": "executed_dimension_match" if matched else "NOT_RUN", "negative_control": "conflict_blocks_transfer" if conflicts else "PASS"})
    return CoupledTotBrotGraphV2(tuple(graph.candidate_id for graph in graphs), tuple(edges), false)


class ObserverPhase(str, Enum):
    INTAKE = "INTAKE"
    MATERIALIZATION = "MATERIALIZATION"
    DIAGNOSIS = "DIAGNOSIS"
    TERMINAL = "TERMINAL"


@dataclass(frozen=True)
class ObserverStateContractV1:
    candidate_id: str
    run_id: str
    frame_id: str
    phase: ObserverPhase
    allowed_inputs: tuple[str, ...]
    forbidden_inputs: tuple[str, ...]
    truth_access: bool = False
    patch_access: bool = False

    def validate(self) -> None:
        if self.truth_access or self.patch_access:
            raise ValueError("observer state cannot read truth or patches")

    @property
    def state_hash(self) -> str:
        self.validate(); return canonical_hash({**asdict(self), "phase": self.phase.value})


@dataclass
class ProvisionalEvidenceBufferV1:
    candidate_id: str
    frame_id: str
    branches: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    canonical_facts: list[dict[str, Any]] = field(default_factory=list)

    def add(self, branch_id: str, fact: Mapping[str, Any]) -> None:
        self.branches.setdefault(branch_id, []).append(dict(fact))

    def promote(self, branch_id: str, fact_index: int, controller_audit_receipt: str | None) -> dict[str, Any]:
        if not controller_audit_receipt:
            raise ValueError("ControllerAudit receipt required for promotion")
        fact = dict(self.branches[branch_id][fact_index]); fact["controller_audit_receipt"] = controller_audit_receipt
        self.canonical_facts.append(fact); return fact


def verify_modalities(observations: Iterable[Mapping[str, Any]]) -> dict[str, object]:
    rows = tuple(observations); required = {"STRUCTURAL", "RUNTIME", "SEMANTIC", "PROVENANCE", "COUNTERFACTUAL"}
    present = {str(row.get("modality")) for row in rows if row.get("producer") and row.get("verifier") and row.get("producer") != row.get("verifier")}
    values = {str(row.get("value")) for row in rows}
    conflicts = max(0, len(values) - 1)
    return {"observation_count": len(rows), "missing_modalities": sorted(required - present), "conflict_count": conflicts, "uncalibrated_averaging_count": 0, "status": "PASS" if required <= present else "BLOCK"}
