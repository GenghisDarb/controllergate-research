from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from controllergate.amds.dpp14.constraint import Constraint
from controllergate.amds.dpp14.hypothesis import HypothesisNode
from controllergate.amds.dpp14.probe_contract import ProbeContract
from controllergate.state.integrity import canonical_hash
from controllergate.topology.canonical_v2 import CoupledTotBrotGraphV2, LocalBrotGraphV2, ObserverStateContractV1, TotBulbBoundaryVolumeV2


@dataclass(frozen=True)
class TopologyCompiledDecisionFrameV1:
    candidate_id: str
    run_id: str
    role_receipt_hashes: tuple[str, ...]
    observer_state_hash: str
    local_brot_graph_hash: str
    coupled_tot_brot_graph_hash: str
    tot_bulb_boundary_volume_hash: str
    alignment_plan_hash: str
    tld_projection_identities: tuple[str, ...]
    tld_metric_version_identity: str
    provisional_buffer_root: str
    modality_contract_identities: tuple[str, ...]
    hypotheses: tuple[dict[str, object], ...]
    constraints: tuple[dict[str, object], ...]
    probe_contracts: tuple[dict[str, object], ...]
    cost_budget: float
    risk_budget: float
    network_budget: int
    allowed_output_roots: tuple[str, ...]
    authorization_scope: str
    sealed_truth_custody_identity: str
    proof_release_parent_identity: str

    @property
    def frame_hash(self) -> str:
        return canonical_hash(asdict(self))


def compile_topology_frame(*, candidate_id: str, run_id: str, role_receipt_hashes: Iterable[str], observer: ObserverStateContractV1, local_graph: LocalBrotGraphV2, coupled_graph: CoupledTotBrotGraphV2, boundary: TotBulbBoundaryVolumeV2, alignment_plan_hash: str, tld_projection_identities: Iterable[str], tld_metric_version_identity: str, provisional_buffer_root: str, modality_contract_identities: Iterable[str], hypotheses: Iterable[HypothesisNode], constraints: Iterable[Constraint], probes: Iterable[ProbeContract], budgets: Mapping[str, object], allowed_output_roots: Iterable[str], authorization_scope: str, sealed_truth_custody_identity: str, proof_release_parent_identity: str) -> TopologyCompiledDecisionFrameV1:
    observer.validate()
    probe_rows = []
    for probe in probes:
        probe.validate(); probe_rows.append(probe.record())
    if local_graph.candidate_id != candidate_id or boundary.candidate_id != candidate_id:
        raise ValueError("topology candidate binding mismatch")
    if candidate_id not in coupled_graph.candidate_ids:
        raise ValueError("candidate absent from coupled topology")
    return TopologyCompiledDecisionFrameV1(candidate_id, run_id, tuple(role_receipt_hashes), observer.state_hash, local_graph.graph_hash, coupled_graph.graph_hash, boundary.volume_hash, alignment_plan_hash, tuple(tld_projection_identities), tld_metric_version_identity, provisional_buffer_root, tuple(modality_contract_identities), tuple(item.record() for item in hypotheses), tuple(item.record() for item in constraints), tuple(probe_rows), float(budgets["cost"]), float(budgets["risk"]), int(budgets.get("network", 0)), tuple(allowed_output_roots), authorization_scope, sealed_truth_custody_identity, proof_release_parent_identity)
