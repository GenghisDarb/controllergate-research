from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from controllergate.state.integrity import canonical_hash

from .branch_ledger import BranchLedger
from .constraint import Constraint
from .constraint_propagation import propagate_to_fixed_point
from .hypothesis import HypothesisNode, HypothesisStatus
from .meta_cell import MetaCellExpansion, expand_meta_cell
from .probe_contract import ProbeContract
from .probe_planner import ProbePlanningRecord, select_probe
from .semantic_verifier import SemanticVerification


FRAME_SCHEMA_VERSION = "causal-board-decision-frame-v1"


@dataclass(frozen=True)
class DecisionFrame:
    candidate_id: str
    run_id: str
    incident_snapshot_identity: str
    source_revision_identity: str
    source_tree_hash: str
    test_tree_hash: str
    provider_runtime_abi_identity: str
    target_reproducer_identity: str
    command_authority_identity: str
    harness_origin: str
    runner_origin: str
    proof_release_parent_identity: str
    hypothesis_registry: tuple[dict[str, object], ...]
    constraint_graph: tuple[dict[str, object], ...]
    probe_contracts: tuple[dict[str, object], ...]
    semantic_verifier_identities: tuple[str, ...]
    cost_budget: float
    risk_budget: float
    network_policy: str
    network_request_budget: int
    network_byte_budget: int
    allowed_output_roots: tuple[str, ...]
    single_use_authorization_scope: str
    memory_mode: str
    frame_schema_version: str = FRAME_SCHEMA_VERSION

    @property
    def frame_hash(self) -> str:
        return canonical_hash(self.record(include_hash=False))

    def record(self, *, include_hash: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "allowed_output_roots": list(self.allowed_output_roots),
            "candidate_id": self.candidate_id,
            "command_authority_identity": self.command_authority_identity,
            "constraint_graph": list(self.constraint_graph),
            "cost_budget": self.cost_budget,
            "frame_schema_version": self.frame_schema_version,
            "harness_origin": self.harness_origin,
            "hypothesis_registry": list(self.hypothesis_registry),
            "incident_snapshot_identity": self.incident_snapshot_identity,
            "memory_mode": self.memory_mode,
            "network_byte_budget": self.network_byte_budget,
            "network_policy": self.network_policy,
            "network_request_budget": self.network_request_budget,
            "probe_contracts": list(self.probe_contracts),
            "proof_release_parent_identity": self.proof_release_parent_identity,
            "provider_runtime_abi_identity": self.provider_runtime_abi_identity,
            "risk_budget": self.risk_budget,
            "run_id": self.run_id,
            "runner_origin": self.runner_origin,
            "semantic_verifier_identities": list(self.semantic_verifier_identities),
            "single_use_authorization_scope": self.single_use_authorization_scope,
            "source_revision_identity": self.source_revision_identity,
            "source_tree_hash": self.source_tree_hash,
            "target_reproducer_identity": self.target_reproducer_identity,
            "test_tree_hash": self.test_tree_hash,
        }
        if include_hash:
            value["frame_hash"] = self.frame_hash
        return value


def freeze_decision_frame(
    *,
    candidate_id: str,
    run_id: str,
    anchors: dict[str, str],
    hypotheses: list[HypothesisNode],
    constraints: list[Constraint],
    contracts: list[ProbeContract],
    budgets: dict[str, Any],
    allowed_output_roots: tuple[str, ...],
    memory_mode: str,
) -> DecisionFrame:
    required = {
        "command_authority_identity",
        "harness_origin",
        "incident_snapshot_identity",
        "proof_release_parent_identity",
        "provider_runtime_abi_identity",
        "runner_origin",
        "source_revision_identity",
        "source_tree_hash",
        "target_reproducer_identity",
        "test_tree_hash",
    }
    missing = sorted(required - anchors.keys())
    if missing:
        raise ValueError(f"candidate-specific anchors missing: {','.join(missing)}")
    for contract in contracts:
        if contract.candidate_id != candidate_id or contract.run_id != run_id:
            raise ValueError("probe contract candidate/run identity mismatch")
        contract.validate()
    for constraint in constraints:
        if constraint.candidate_id != candidate_id or constraint.run_id != run_id:
            raise ValueError("constraint candidate/run identity mismatch")
        constraint.validate()
    return DecisionFrame(
        candidate_id=candidate_id,
        run_id=run_id,
        incident_snapshot_identity=anchors["incident_snapshot_identity"],
        source_revision_identity=anchors["source_revision_identity"],
        source_tree_hash=anchors["source_tree_hash"],
        test_tree_hash=anchors["test_tree_hash"],
        provider_runtime_abi_identity=anchors["provider_runtime_abi_identity"],
        target_reproducer_identity=anchors["target_reproducer_identity"],
        command_authority_identity=anchors["command_authority_identity"],
        harness_origin=anchors["harness_origin"],
        runner_origin=anchors["runner_origin"],
        proof_release_parent_identity=anchors["proof_release_parent_identity"],
        hypothesis_registry=tuple(item.record() for item in hypotheses),
        constraint_graph=tuple(item.record() for item in constraints),
        probe_contracts=tuple(item.record() for item in contracts),
        semantic_verifier_identities=tuple(sorted({item.semantic_verifier_identity for item in contracts})),
        cost_budget=float(budgets["cost"]),
        risk_budget=float(budgets["risk"]),
        network_policy=str(budgets.get("network_policy", "none")),
        network_request_budget=int(budgets.get("network_requests", 0)),
        network_byte_budget=int(budgets.get("network_bytes", 0)),
        allowed_output_roots=allowed_output_roots,
        single_use_authorization_scope=str(budgets["authorization_scope"]),
        memory_mode=memory_mode,
    )


@dataclass
class CausalBoardController:
    frame: DecisionFrame
    hypotheses: dict[str, HypothesisNode]
    constraints: list[Constraint]
    contracts: list[ProbeContract]
    active_hypotheses: set[str] = field(default_factory=set)
    events: list[dict[str, object]] = field(default_factory=list)
    planning_records: list[ProbePlanningRecord] = field(default_factory=list)
    verifications: list[SemanticVerification] = field(default_factory=list)
    meta_cell_expansions: list[MetaCellExpansion] = field(default_factory=list)
    certain_facts: set[str] = field(default_factory=set)
    spent_contract_hashes: set[str] = field(default_factory=set)
    cost_spent: float = 0.0
    risk_spent: float = 0.0

    def __post_init__(self) -> None:
        if not self.active_hypotheses:
            self.active_hypotheses = set(self.hypotheses)
        self.branch_ledger = BranchLedger(self.frame.candidate_id, self.frame.run_id)
        self.branch_ledger.checkpoint(self.active_hypotheses, 0)

    def plan(self, prior: dict[str, float] | None = None) -> ProbePlanningRecord:
        legal = [
            item
            for item in self.contracts
            if self.cost_spent + item.cost <= self.frame.cost_budget
            and self.risk_spent + item.risk <= self.frame.risk_budget
        ]
        planning = select_probe(
            active_hypotheses=self.active_hypotheses,
            contracts=legal,
            spent_contract_hashes=self.spent_contract_hashes,
            prior=prior,
        )
        self.planning_records.append(planning)
        return planning

    def apply_verification(
        self, contract: ProbeContract, verification: SemanticVerification, nonce: str
    ) -> dict[str, object]:
        if contract.contract_hash in self.spent_contract_hashes:
            raise ValueError("single-use probe contract already spent")
        self.branch_ledger.spend_nonce(nonce)
        self.spent_contract_hashes.add(contract.contract_hash)
        self.cost_spent += contract.cost
        self.risk_spent += contract.risk
        self.verifications.append(verification)
        before = set(self.active_hypotheses)
        if verification.status != "DIRECT_VERIFIED" or verification.outcome_code is None:
            event = {
                "active_after": sorted(before),
                "active_before": sorted(before),
                "contract_hash": contract.contract_hash,
                "event_type": "observation_rejected",
                "verification_hash": verification.verification_hash,
            }
            event["event_hash"] = canonical_hash(event)
            self.events.append(event)
            return event
        supported = set(contract.predicted_outcome_partitions[verification.outcome_code])
        propagation = propagate_to_fixed_point(
            active_hypotheses=before,
            supported_partition=supported,
            constraints=self.constraints,
            evidence_hash=verification.verification_hash,
        )
        if propagation.contradiction:
            restored = self.branch_ledger.contradiction(
                assumptions=sorted(before),
                evidence_hashes=[verification.verification_hash],
                operation_identity=contract.contract_hash,
                reopen_condition="select the next unspent legal probe or abstain",
            )
            self.active_hypotheses = restored
            event_type = "contradiction_backtrack"
        else:
            self.active_hypotheses = set(propagation.active_hypotheses)
            self.certain_facts.update(verification.direct_facts)
            event_type = "constraint_fixed_point"
            eliminated = before - self.active_hypotheses
            for name in eliminated:
                self.hypotheses[name] = self.hypotheses[name].mark(
                    HypothesisStatus.ELIMINATED,
                    contradicting_evidence_hash=verification.verification_hash,
                )
            if len(self.active_hypotheses) == 1:
                remaining = next(iter(self.active_hypotheses))
                self.hypotheses[remaining] = self.hypotheses[remaining].mark(
                    HypothesisStatus.CERTAIN,
                    direct_evidence_hash=verification.verification_hash,
                    support=1.0,
                )
                self.branch_ledger.checkpoint(self.active_hypotheses, len(self.events) + 1)
        event = {
            "active_after": sorted(self.active_hypotheses),
            "active_before": sorted(before),
            "contract_hash": contract.contract_hash,
            "event_type": event_type,
            "propagation": propagation.record(),
            "verification_hash": verification.verification_hash,
        }
        event["event_hash"] = canonical_hash(event)
        self.events.append(event)
        return event

    def decompose(self, parent_name: str, child_names: tuple[str, ...], reason: str) -> MetaCellExpansion:
        parent = self.hypotheses[parent_name]
        expansion, children = expand_meta_cell(parent=parent, child_names=child_names, reason=reason)
        self.meta_cell_expansions.append(expansion)
        self.active_hypotheses.discard(parent_name)
        self.hypotheses[parent_name] = parent.mark(HypothesisStatus.WEAKENED)
        for child in children:
            self.hypotheses[child.name] = child
            self.active_hypotheses.add(child.name)
        self.branch_ledger.checkpoint(self.active_hypotheses, len(self.events))
        return expansion

    def snapshot(self) -> dict[str, object]:
        return {
            "active_hypotheses": sorted(self.active_hypotheses),
            "backtracks": self.branch_ledger.backtrack_count,
            "candidate_id": self.frame.candidate_id,
            "certain_facts": sorted(self.certain_facts),
            "contradictions": self.branch_ledger.contradiction_count,
            "cost_spent": self.cost_spent,
            "events": self.events,
            "failed_branches": self.branch_ledger.failed_branches,
            "frame_hash": self.frame.frame_hash,
            "hypotheses": [self.hypotheses[name].record() for name in sorted(self.hypotheses)],
            "meta_cell_expansions": [
                {
                    "child_hypotheses": list(item.child_hypotheses),
                    "expansion_hash": item.expansion_hash,
                    "parent_hypothesis": item.parent_hypothesis,
                    "reason": item.reason,
                }
                for item in self.meta_cell_expansions
            ],
            "planning_records": [item.record() for item in self.planning_records],
            "risk_spent": self.risk_spent,
            "run_id": self.frame.run_id,
            "spent_nonces": sorted(self.branch_ledger.spent_nonces),
            "verifications": [item.record() for item in self.verifications],
        }
