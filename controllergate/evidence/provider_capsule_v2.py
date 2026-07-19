"""Provider capsule identities with exact-versus-series scope."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any


PROVIDER_PARITY = {"EXACT", "SERIES_LIMITED", "MICRO_UNRESOLVED", "PLATFORM_UNAVAILABLE"}


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class ProviderCapsuleV2:
    capsule_id: str
    candidate_id: str
    implementation: str
    requested_version: str
    observed_version: str | None
    version_parity: str
    os: str
    architecture: str
    abi: str
    soabi: str | None
    setup_python_identity: str
    dependency_lock_hash: str
    dependency_graph_hash: str
    environment_hash: str
    locale: str
    timezone: str
    git_version: str | None
    runner_image: str
    resource_budget: dict[str, int]
    acquisition_phase_network: str
    offline_execution_network: str
    authority_allowed: str = "provider identity and scoped sensitivity execution"
    authority_forbidden: tuple[str, ...] = (
        "exact incident parity when not exact",
        "causal ownership without counterfactual evidence",
        "patch authority",
        "release promotion",
    )

    def __post_init__(self) -> None:
        if self.version_parity not in PROVIDER_PARITY:
            raise ValueError(f"invalid provider parity: {self.version_parity}")
        if self.version_parity == "EXACT" and self.observed_version != self.requested_version:
            raise ValueError("exact provider requires exact observed version")
        if self.offline_execution_network not in {"none", "loopback_only"}:
            raise ValueError("paired execution must be offline or loopback only")

    def record(self) -> dict[str, Any]:
        row = asdict(self)
        row["capsule_hash"] = canonical_hash(row)
        return row


def verify_provider_capsule(row: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if row.get("version_parity") not in PROVIDER_PARITY:
        blockers.append("invalid_version_parity")
    if row.get("offline_execution_network") not in {"none", "loopback_only"}:
        blockers.append("offline_network_policy_invalid")
    if row.get("version_parity") == "EXACT" and row.get("observed_version") != row.get("requested_version"):
        blockers.append("exact_version_mismatch")
    expected = canonical_hash({key: value for key, value in row.items() if key != "capsule_hash"})
    if row.get("capsule_hash") != expected:
        blockers.append("capsule_hash_mismatch")
    return blockers
