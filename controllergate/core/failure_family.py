from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FailureFamilyNode:
    family_id: str
    parent_family_id: str | None
    depth: int
    phase: str
    observed_evidence: tuple[str, ...]
    raw_log_references: tuple[str, ...]
    evidence_hashes: tuple[str, ...]
    candidate_causal_classification: str
    confidence: float
    known_confounders: tuple[str, ...]
    provider_involvement: bool
    harness_involvement: bool
    source_involvement: bool
    interpreter_involvement: bool
    environment_involvement: bool
    isolated: bool
    reproducible: bool
    intervention_authorized: bool
    reopen_conditions: tuple[str, ...]

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class FailureFamilyEdge:
    parent_family_id: str
    child_family_id: str
    evidence_hash: str

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class DiagnosticProbe:
    probe_id: str
    family_id: str
    command_manifest_hash: str
    authoritative: bool


@dataclass(frozen=True)
class ElbowDecision:
    classification: str
    isolated_family_id: str | None
    evidence_hashes: tuple[str, ...]
    intervention_authorized: bool
    next_action: str

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class RecoveryAuthorization:
    authorized: bool
    family_id: str | None
    scope: str
    rollback_hash: str | None
