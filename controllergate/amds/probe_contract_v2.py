from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ProbeContractV2:
    probe_id: str
    evidence_contact: str
    required_inputs: tuple[str, ...]
    possible_observation_classes: tuple[str, ...]
    hypotheses_distinguished: tuple[str, ...]
    expected_information_value: float | None
    execution_cost: float
    manual_review_cost: float
    security_risk: float
    provider_rebuild_requirement: bool
    platform_requirement: str | None
    authorization_requirement: str
    direct_evidence_produced: tuple[str, ...]
    forbidden_evidence: tuple[str, ...]
    stop_conditions: tuple[str, ...]

    def validate(self) -> dict[str, object]:
        errors: list[str] = []
        if not self.probe_id or not self.evidence_contact:
            errors.append("probe_identity_missing")
        if len(self.possible_observation_classes) < 2:
            errors.append("observation_classes_insufficient")
        if not self.hypotheses_distinguished:
            errors.append("hypothesis_distinction_missing")
        if min(self.execution_cost, self.manual_review_cost, self.security_risk) < 0:
            errors.append("negative_cost")
        if not self.direct_evidence_produced:
            errors.append("direct_evidence_missing")
        return {"status": "PASS" if not errors else "FAIL", "errors": errors, "probe": asdict(self)}

    @property
    def total_cost(self) -> float:
        return self.execution_cost + self.manual_review_cost + self.security_risk
