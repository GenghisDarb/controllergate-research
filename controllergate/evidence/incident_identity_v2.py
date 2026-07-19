"""Decision-time incident and provider identity contracts for Batch100.

The records in this module distinguish the environment used by a prior
execution from the environment reported by the issue.  They never infer
parity from a matching candidate identifier.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any


PARITY_STATUSES = {
    "EXACT_INCIDENT_PARITY",
    "PROVIDER_SERIES_ONLY",
    "PROVIDER_MICRO_UNRESOLVED",
    "PLATFORM_MISMATCH",
    "TARGET_NODE_MISMATCH",
    "COMMAND_MISMATCH",
    "INPUT_MISMATCH",
    "SOURCE_COMMIT_MISMATCH",
    "INCIDENT_NOT_MATERIALIZED",
}


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class IssueEpisodeIdentityV2:
    candidate_id: str
    repository: str
    issue_number: int
    issue_created_at: str
    issue_snapshot_cutoff: str
    frozen_source_commit: str
    issue_reported_command: list[str]
    issue_reported_input: dict[str, Any]
    issue_reported_expected_behavior: dict[str, Any]
    issue_reported_actual_behavior: dict[str, Any]
    issue_reported_exact_nodes: list[str]
    issue_reported_secondary_source: dict[str, Any] | None
    authority_allowed: str = "candidate-specific incident contract construction"
    authority_forbidden: tuple[str, ...] = (
        "causal ownership without execution",
        "patch generation",
        "repair count mutation",
        "release promotion",
    )

    def record(self) -> dict[str, Any]:
        row = asdict(self)
        row["identity_hash"] = canonical_hash(row)
        return row


@dataclass(frozen=True)
class IncidentProviderIdentityV2:
    candidate_id: str
    batch098_execution_provider: str
    batch098_execution_platform: str
    issue_reported_provider: str
    issue_reported_platform: str
    parity_status: str
    parity_failures: list[str]
    superseded_target_contract: str
    new_incident_contract: str
    authority_allowed: str = "provider-parity and sensitivity classification"
    authority_forbidden: tuple[str, ...] = (
        "exact parity when microrelease is unresolved",
        "causal ownership",
        "patch generation",
        "release promotion",
    )

    def __post_init__(self) -> None:
        if self.parity_status not in PARITY_STATUSES:
            raise ValueError(f"unsupported parity status: {self.parity_status}")
        if self.parity_status == "EXACT_INCIDENT_PARITY" and self.parity_failures:
            raise ValueError("exact parity cannot retain parity failures")

    def record(self) -> dict[str, Any]:
        row = asdict(self)
        row["provider_identity_hash"] = canonical_hash(row)
        return row


def validate_supersession(record: dict[str, Any]) -> None:
    required = {
        "candidate_id",
        "historical_contract_hash",
        "historical_contract_preserved",
        "supersession_reason",
        "incident_contract",
        "provenance",
        "authority_allowed",
        "authority_forbidden",
    }
    missing = sorted(required - record.keys())
    if missing:
        raise ValueError(f"missing supersession fields: {missing}")
    if record["historical_contract_preserved"] is not True:
        raise ValueError("historical contract must remain preserved")
    forbidden = json.dumps(record["incident_contract"], sort_keys=True).lower()
    for marker in ("gold_patch", "accepted_fix", "future_revision", "sealed_truth"):
        if marker in forbidden:
            raise ValueError(f"forbidden incident-contract field: {marker}")
