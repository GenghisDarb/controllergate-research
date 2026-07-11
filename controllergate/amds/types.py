from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CellState(str, Enum):
    UNKNOWN = "UNKNOWN"
    SAFE = "SAFE"
    CAUSAL_MINE = "CAUSAL_MINE"
    BLOCKED = "BLOCKED"
    RESOLVED = "RESOLVED"
    CONFLICTED = "CONFLICTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class AmdsCell:
    cell_id: str
    cell_type: str
    candidate_id: str
    evidence_hashes: tuple[str, ...] = ()
    state: str = CellState.UNKNOWN.value
    confidence_classification: str = "structural_uniform_uncalibrated"
    associated_hypotheses: tuple[str, ...] = ()
    neighbors: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    allowed_probes: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ("source_patch",)
    reopen_conditions: tuple[str, ...] = ()
    last_update_event: str = "board_initialized"
    state_hash: str = ""


@dataclass(frozen=True)
class AmdsEdge:
    edge_id: str
    source: str
    target: str
    edge_type: str


@dataclass(frozen=True)
class AmdsConstraint:
    constraint_id: str
    constraint_type: str
    members: tuple[str, ...]
    source_evidence_hashes: tuple[str, ...] = ()


@dataclass(frozen=True)
class FailureHypothesis:
    hypothesis_id: str
    family: str
    applies_to: tuple[str, ...]
    prior_classification: str = "structural_uniform_uncalibrated"


@dataclass(frozen=True)
class HypothesisState:
    probabilities: dict[str, float]
    classification: str = "structural_uniform_uncalibrated"


@dataclass(frozen=True)
class ProbeCandidate:
    probe_id: str
    probe_type: str
    candidate_id: str
    targeted_hypotheses: tuple[str, ...]
    execution_cost: float = 1.0
    security_risk: float = 0.0
    mutation_risk: float = 0.0
    reversible: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProbeAuthorization:
    authorization_id: str
    probe_id: str
    candidate_id: str
    allowed: bool
    single_use: bool = True
    mutation_allowed: bool = False


@dataclass(frozen=True)
class ProbeObservation:
    probe_id: str
    status: str
    evidence_hash: str
    classifications: tuple[str, ...] = ()
    blocker: str | None = None


@dataclass(frozen=True)
class PosteriorState:
    probabilities: dict[str, float]
    entropy_nats: float
    classification: str


@dataclass(frozen=True)
class BoardUpdate:
    event_id: str
    changed_cells: tuple[str, ...]
    board_hash_before: str
    board_hash_after: str


@dataclass(frozen=True)
class PropagationResult:
    status: str
    cells: tuple[dict[str, Any], ...]
    deductions: tuple[dict[str, Any], ...]
    contradictions: tuple[dict[str, Any], ...]
    fixed_point: bool


@dataclass(frozen=True)
class BranchClosure:
    branch_id: str
    status: str
    evidence_hashes: tuple[str, ...]
    reopen_conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class AmdsStopDecision:
    stop: bool
    reason: str
    legal_probe_count: int


@dataclass(frozen=True)
class AmdsRunResult:
    status: str
    stop_reason: str
    probes_executed: int
    board_updates: int
    branches_closed: int


@dataclass(frozen=True)
class AmdsBoard:
    board_id: str
    candidate_id: str
    cells: tuple[dict[str, Any], ...]
    edges: tuple[dict[str, Any], ...]
    constraints: tuple[dict[str, Any], ...]
    board_hash: str = ""
