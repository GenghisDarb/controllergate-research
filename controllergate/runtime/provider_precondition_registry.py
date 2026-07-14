from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .cofactor_requirement import CofactorRequirement


ALLOWED_STATES = {
    "DECLARED_PINNED_VERIFIED", "DECLARED_PINNED_MISSING", "DECLARED_UNPINNED", "OPTIONAL_ABSENT",
    "TEST_ONLY_VERIFIED", "PLATFORM_INCOMPATIBLE", "PROVIDER_DRIFT_DETECTED", "NOT_APPLICABLE",
}


@dataclass
class ProviderPreconditionRegistry:
    rows: list[dict[str, object]] = field(default_factory=list)

    def add(self, candidate_id: str, requirement: CofactorRequirement, state: str, materialization_state: str, verification_state: str) -> dict[str, object]:
        if state not in ALLOWED_STATES:
            raise ValueError("provider_precondition_state_invalid")
        blocker = None
        if requirement.requirement_class == "required" and state in {"DECLARED_UNPINNED", "DECLARED_PINNED_MISSING"}:
            blocker = "declared_secondary_cofactor_unpinned_lock_required"
        row = {
            "candidate_id": candidate_id, **asdict(requirement), "lock_status": state,
            "materialization_state": materialization_state, "verification_state": verification_state,
            "failure_classification": blocker, "reopen_condition": "reviewed pinned provider lock" if blocker else None,
        }
        self.rows.append(row)
        return row
