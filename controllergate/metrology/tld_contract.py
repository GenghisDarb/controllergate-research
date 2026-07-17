from __future__ import annotations

from dataclasses import asdict, dataclass

from controllergate.state.integrity import canonical_hash


@dataclass(frozen=True)
class MetricVersion:
    metric_id: str
    version: str
    operator: str
    window: tuple[int, ...]
    threshold: float

    @property
    def identity(self) -> str:
        return canonical_hash(asdict(self))


@dataclass(frozen=True)
class ParentNullPair:
    parent_id: str
    observed_pool_hash: str
    null_child_ids: tuple[str, ...]
    parent_count: int
    child_count: int

    def validate(self) -> None:
        if not self.null_child_ids or self.child_count != len(self.null_child_ids):
            raise ValueError("each parent requires matched null children")
        if self.parent_count != 1:
            raise ValueError("effective sample is counted by independent parent")


@dataclass(frozen=True)
class ThreeProjectionResult:
    candidate_id: str
    state_projection: str
    transition_projection: str
    control_projection: str
    baseline_parity: bool
    null_effective_sample: int
    t_e: str
    s_e: str
    winner_mode: str
    closure: str
    authority_allowed: str = "diagnostic negative regulation"
    authority_forbidden: tuple[str, ...] = ("source ownership", "repair", "count")

    def validate(self) -> None:
        if not self.baseline_parity:
            raise ValueError("baseline parity required before perturbation claims")
        if self.null_effective_sample < 1:
            raise ValueError("independent parent effective sample required")
        if self.t_e == self.s_e:
            raise ValueError("onset and persistence semantics must remain distinct")
