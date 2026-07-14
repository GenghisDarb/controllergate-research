from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from controllergate.state.integrity import canonical_hash

from .observation_schema import SCHEMA_VERSION, semantic_alias_hits


@dataclass(frozen=True)
class ProbeContract:
    candidate_id: str
    run_id: str
    probe_id: str
    prerequisite_tokens: tuple[str, ...]
    operation_type: str
    argv: tuple[str, ...]
    working_directory_identity: str
    runtime_attestation_hash: str
    network_policy: str
    maximum_requests: int
    maximum_bytes: int
    semantic_verifier_identity: str
    predicted_outcome_partitions: dict[str, tuple[str, ...]]
    outcome_matchers: dict[str, dict[str, Any]]
    cost: float
    risk: float
    replay_policy: str
    nonce_scope: str
    allowed_output_roots: tuple[str, ...]
    environment: dict[str, str] = field(default_factory=dict)
    calibrated_likelihoods: dict[str, dict[str, float]] | None = None
    likelihood_source: str | None = None
    output_schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        surface = {
            "argv": list(self.argv),
            "environment": self.environment,
            "output_matchers": self.outcome_matchers,
            "output_schema_version": self.output_schema_version,
            "probe_id": self.probe_id,
            "working_directory_identity": self.working_directory_identity,
        }
        hits = semantic_alias_hits(surface)
        if hits:
            raise ValueError(f"probe semantic alias leakage: {','.join(hits)}")
        if not self.predicted_outcome_partitions or not self.outcome_matchers:
            raise ValueError("predicted partitions and outcome matchers required")
        if set(self.predicted_outcome_partitions) != set(self.outcome_matchers):
            raise ValueError("outcome partitions and matchers must have identical keys")
        if self.cost < 0 or self.risk < 0:
            raise ValueError("nonnegative cost and risk required")
        if self.network_policy == "none" and (self.maximum_requests or self.maximum_bytes):
            raise ValueError("offline probe cannot receive network budget")
        if self.network_policy != "none" and (self.maximum_requests <= 0 or self.maximum_bytes <= 0):
            raise ValueError("network probe requires bounded budgets")
        if self.calibrated_likelihoods is not None and not self.likelihood_source:
            raise ValueError("calibrated likelihood source required")

    @property
    def contract_hash(self) -> str:
        return canonical_hash(self.record(include_hash=False))

    def record(self, *, include_hash: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "allowed_output_roots": list(self.allowed_output_roots),
            "argv": list(self.argv),
            "calibrated_likelihoods": self.calibrated_likelihoods,
            "candidate_id": self.candidate_id,
            "cost": self.cost,
            "environment": self.environment,
            "likelihood_source": self.likelihood_source,
            "maximum_bytes": self.maximum_bytes,
            "maximum_requests": self.maximum_requests,
            "network_policy": self.network_policy,
            "nonce_scope": self.nonce_scope,
            "operation_type": self.operation_type,
            "outcome_matchers": self.outcome_matchers,
            "output_schema_version": self.output_schema_version,
            "predicted_outcome_partitions": {
                key: list(value) for key, value in sorted(self.predicted_outcome_partitions.items())
            },
            "prerequisite_tokens": list(self.prerequisite_tokens),
            "probe_id": self.probe_id,
            "replay_policy": self.replay_policy,
            "risk": self.risk,
            "run_id": self.run_id,
            "runtime_attestation_hash": self.runtime_attestation_hash,
            "semantic_verifier_identity": self.semantic_verifier_identity,
            "working_directory_identity": self.working_directory_identity,
        }
        if include_hash:
            value["contract_hash"] = self.contract_hash
        return value
