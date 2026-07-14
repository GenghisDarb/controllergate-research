from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from controllergate.state.integrity import canonical_hash


class ConstraintType(str, Enum):
    MUTUAL_EXCLUSION = "mutual_exclusion"
    IMPLICATION = "implication"
    EXACTLY_K = "exactly_k"
    AT_MOST_K = "at_most_k"
    AT_LEAST_K = "at_least_k"
    PROVIDER_BEFORE_TARGET = "provider_before_target"
    VALID_COLLECTION_BEFORE_FAILURE_CLASSIFICATION = "valid_collection_before_failure_classification"
    FAILURE_REPRODUCED_BEFORE_OWNERSHIP = "failure_reproduced_before_ownership"
    OWNERSHIP_BEFORE_LICENSE = "ownership_before_license"
    VALIDATION_BEFORE_DUPLICATE_REPLAY = "validation_before_duplicate_replay"
    DUPLICATE_REPLAY_AND_ROLLBACK_BEFORE_PROOF = "duplicate_replay_and_rollback_before_proof"
    PROOF_BEFORE_COUNT = "proof_before_count"
    IDENTITY_EQUALITY = "candidate_run_token_identity_equality"
    SOURCE_TEST_IMMUTABILITY = "source_test_immutability"
    SHARED_FRAME = "normal_incident_shared_frame"


@dataclass(frozen=True)
class Constraint:
    constraint_type: ConstraintType
    members: tuple[str, ...]
    candidate_id: str
    run_id: str
    k: int | None = None
    antecedent: str | None = None
    consequent: str | None = None
    hard: bool = True
    source_evidence_hashes: tuple[str, ...] = ()

    @property
    def constraint_identity(self) -> str:
        return canonical_hash(self.record(include_identity=False))

    def record(self, *, include_identity: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "antecedent": self.antecedent,
            "candidate_id": self.candidate_id,
            "consequent": self.consequent,
            "constraint_type": self.constraint_type.value,
            "hard": self.hard,
            "k": self.k,
            "members": list(self.members),
            "run_id": self.run_id,
            "source_evidence_hashes": list(self.source_evidence_hashes),
        }
        if include_identity:
            value["constraint_identity"] = self.constraint_identity
        return value

    def validate(self) -> None:
        if not self.members and self.constraint_type not in {
            ConstraintType.PROVIDER_BEFORE_TARGET,
            ConstraintType.VALID_COLLECTION_BEFORE_FAILURE_CLASSIFICATION,
            ConstraintType.FAILURE_REPRODUCED_BEFORE_OWNERSHIP,
            ConstraintType.OWNERSHIP_BEFORE_LICENSE,
            ConstraintType.VALIDATION_BEFORE_DUPLICATE_REPLAY,
            ConstraintType.DUPLICATE_REPLAY_AND_ROLLBACK_BEFORE_PROOF,
            ConstraintType.PROOF_BEFORE_COUNT,
            ConstraintType.IDENTITY_EQUALITY,
            ConstraintType.SOURCE_TEST_IMMUTABILITY,
            ConstraintType.SHARED_FRAME,
        }:
            raise ValueError("constraint members required")
        if self.constraint_type in {
            ConstraintType.EXACTLY_K,
            ConstraintType.AT_MOST_K,
            ConstraintType.AT_LEAST_K,
        } and (self.k is None or self.k < 0):
            raise ValueError("nonnegative k required")
        if self.constraint_type is ConstraintType.IMPLICATION and not (self.antecedent and self.consequent):
            raise ValueError("implication endpoints required")
