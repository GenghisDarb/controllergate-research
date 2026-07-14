from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from controllergate.state.integrity import canonical_hash

from .observation_schema import NeutralObservation
from .probe_contract import ProbeContract


@dataclass(frozen=True)
class SemanticVerification:
    broker_record_hash: str
    contract_hash: str
    direct_facts: tuple[str, ...]
    observation_hash: str
    outcome_code: str | None
    status: str
    verifier_identity: str
    verifier_reason: str

    @property
    def verification_hash(self) -> str:
        return canonical_hash(self.record(include_hash=False))

    def record(self, *, include_hash: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "broker_record_hash": self.broker_record_hash,
            "contract_hash": self.contract_hash,
            "direct_facts": list(self.direct_facts),
            "observation_hash": self.observation_hash,
            "outcome_code": self.outcome_code,
            "status": self.status,
            "verifier_identity": self.verifier_identity,
            "verifier_reason": self.verifier_reason,
        }
        if include_hash:
            value["verification_hash"] = self.verification_hash
        return value


def _matches(values: dict[str, Any], matcher: dict[str, Any]) -> bool:
    for key, expected in matcher.items():
        observed = values.get(key)
        if isinstance(expected, dict):
            if "equals" in expected and observed != expected["equals"]:
                return False
            if "not_equals" in expected and observed == expected["not_equals"]:
                return False
            if "minimum" in expected and (not isinstance(observed, (int, float)) or observed < expected["minimum"]):
                return False
            if "nonempty" in expected and bool(observed) is not bool(expected["nonempty"]):
                return False
        elif observed != expected:
            return False
    return True


def verify_observation(
    *,
    contract: ProbeContract,
    observation: NeutralObservation,
    broker_record: dict[str, Any],
) -> SemanticVerification:
    if broker_record.get("record_hash") is None:
        return SemanticVerification(
            broker_record_hash="missing",
            contract_hash=contract.contract_hash,
            direct_facts=(),
            observation_hash=observation.observation_hash,
            outcome_code=None,
            status="REJECTED_UNUSABLE",
            verifier_identity=contract.semantic_verifier_identity,
            verifier_reason="broker record hash missing",
        )
    if broker_record.get("candidate_id") != contract.candidate_id or broker_record.get("run_id") != contract.run_id:
        return SemanticVerification(
            broker_record_hash=str(broker_record["record_hash"]),
            contract_hash=contract.contract_hash,
            direct_facts=(),
            observation_hash=observation.observation_hash,
            outcome_code=None,
            status="REJECTED_UNUSABLE",
            verifier_identity=contract.semantic_verifier_identity,
            verifier_reason="candidate or run identity mismatch",
        )
    if broker_record.get("source_tree_hash_before") != broker_record.get("source_tree_hash_after"):
        return SemanticVerification(
            broker_record_hash=str(broker_record["record_hash"]),
            contract_hash=contract.contract_hash,
            direct_facts=(),
            observation_hash=observation.observation_hash,
            outcome_code=None,
            status="REJECTED_UNUSABLE",
            verifier_identity=contract.semantic_verifier_identity,
            verifier_reason="diagnostic probe changed source tree",
        )
    if broker_record.get("test_tree_hash_before") != broker_record.get("test_tree_hash_after"):
        return SemanticVerification(
            broker_record_hash=str(broker_record["record_hash"]),
            contract_hash=contract.contract_hash,
            direct_facts=(),
            observation_hash=observation.observation_hash,
            outcome_code=None,
            status="REJECTED_UNUSABLE",
            verifier_identity=contract.semantic_verifier_identity,
            verifier_reason="diagnostic probe changed test tree",
        )
    matches = [code for code, matcher in contract.outcome_matchers.items() if _matches(observation.values, matcher)]
    if len(matches) != 1:
        return SemanticVerification(
            broker_record_hash=str(broker_record["record_hash"]),
            contract_hash=contract.contract_hash,
            direct_facts=(),
            observation_hash=observation.observation_hash,
            outcome_code=None,
            status="CONTRADICTORY" if len(matches) > 1 else "REJECTED_UNUSABLE",
            verifier_identity=contract.semantic_verifier_identity,
            verifier_reason="neutral observation must match exactly one registered outcome",
        )
    outcome = matches[0]
    facts = (
        f"verified_outcome:{contract.contract_hash}:{outcome}",
        f"broker_record:{broker_record['record_hash']}",
        f"observation:{observation.observation_hash}",
    )
    return SemanticVerification(
        broker_record_hash=str(broker_record["record_hash"]),
        contract_hash=contract.contract_hash,
        direct_facts=facts,
        observation_hash=observation.observation_hash,
        outcome_code=outcome,
        status="DIRECT_VERIFIED",
        verifier_identity=contract.semantic_verifier_identity,
        verifier_reason="raw broker record and neutral structured observation satisfy one registered matcher",
    )
