from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from controllergate.state.integrity import canonical_hash


class HypothesisStatus(str, Enum):
    UNRESOLVED = "unresolved"
    WEAKENED = "weakened"
    ELIMINATED = "eliminated"
    CERTAIN = "certain"
    CONTRADICTED = "contradicted"


@dataclass(frozen=True)
class HypothesisNode:
    name: str
    candidate_id: str
    run_id: str
    prior_mode: str
    prior_source: str
    current_support: float | None = None
    status: HypothesisStatus = HypothesisStatus.UNRESOLVED
    supporting_direct_evidence_hashes: tuple[str, ...] = ()
    supporting_inferred_evidence_hashes: tuple[str, ...] = ()
    contradicting_evidence_hashes: tuple[str, ...] = ()
    parent_meta_cell_identity: str | None = None
    allowed_terminal_mapping: str | None = None
    hypothesis_identity: str = field(init=False)

    def __post_init__(self) -> None:
        identity = canonical_hash(
            {
                "candidate_id": self.candidate_id,
                "name": self.name,
                "parent_meta_cell_identity": self.parent_meta_cell_identity,
                "prior_mode": self.prior_mode,
                "prior_source": self.prior_source,
                "run_id": self.run_id,
            }
        )
        object.__setattr__(self, "hypothesis_identity", identity)

    def record(self) -> dict[str, object]:
        return {
            "allowed_terminal_mapping": self.allowed_terminal_mapping,
            "candidate_id": self.candidate_id,
            "contradicting_evidence_hashes": list(self.contradicting_evidence_hashes),
            "current_support": self.current_support,
            "hypothesis_identity": self.hypothesis_identity,
            "name": self.name,
            "parent_meta_cell_identity": self.parent_meta_cell_identity,
            "prior_mode": self.prior_mode,
            "prior_source": self.prior_source,
            "run_id": self.run_id,
            "status": self.status.value,
            "supporting_direct_evidence_hashes": list(self.supporting_direct_evidence_hashes),
            "supporting_inferred_evidence_hashes": list(self.supporting_inferred_evidence_hashes),
        }

    def mark(
        self,
        status: HypothesisStatus,
        *,
        direct_evidence_hash: str | None = None,
        inferred_evidence_hash: str | None = None,
        contradicting_evidence_hash: str | None = None,
        support: float | None = None,
    ) -> "HypothesisNode":
        direct = self.supporting_direct_evidence_hashes
        inferred = self.supporting_inferred_evidence_hashes
        contradicting = self.contradicting_evidence_hashes
        if direct_evidence_hash and direct_evidence_hash not in direct:
            direct = (*direct, direct_evidence_hash)
        if inferred_evidence_hash and inferred_evidence_hash not in inferred:
            inferred = (*inferred, inferred_evidence_hash)
        if contradicting_evidence_hash and contradicting_evidence_hash not in contradicting:
            contradicting = (*contradicting, contradicting_evidence_hash)
        return replace(
            self,
            status=status,
            current_support=self.current_support if support is None else support,
            supporting_direct_evidence_hashes=direct,
            supporting_inferred_evidence_hashes=inferred,
            contradicting_evidence_hashes=contradicting,
        )


CANONICAL_HYPOTHESES = (
    "source_owned_behavior_defect",
    "provider_owned",
    "environment_owned",
    "platform_owned",
    "network_or_transport_owned",
    "harness_owned",
    "test_or_expectation_fragility",
    "mixed_failure",
    "insufficient_evidence",
)
