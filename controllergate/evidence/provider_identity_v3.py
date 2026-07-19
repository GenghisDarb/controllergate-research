"""Exact provider identity and explicitly bounded approximation modes."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


PROVIDER_MODES = {
    "EXACT_PROVIDER",
    "SERIES_LIMITED_PROVIDER",
    "NEAREST_REPRODUCIBLE_PROVIDER",
    "UNAVAILABLE_PROVIDER",
}


@dataclass(frozen=True)
class ProviderIdentityV3:
    implementation: str
    major: int
    minor: int
    micro: int
    prerelease: str | None
    operating_system: str
    architecture: str
    abi: str
    soabi: str

    def record(self) -> dict[str, Any]:
        return asdict(self)


def classify_provider(required: ProviderIdentityV3, observed: ProviderIdentityV3 | None) -> dict[str, Any]:
    if observed is None:
        mode = "UNAVAILABLE_PROVIDER"
        mismatches = ["provider_not_materialized"]
    else:
        fields = tuple(required.record())
        mismatches = [name for name in fields if getattr(required, name) != getattr(observed, name)]
        if not mismatches:
            mode = "EXACT_PROVIDER"
        elif all(name in {"micro", "prerelease"} for name in mismatches):
            mode = "SERIES_LIMITED_PROVIDER"
        else:
            mode = "NEAREST_REPRODUCIBLE_PROVIDER"
    return {
        "mode": mode,
        "required": required.record(),
        "observed": observed.record() if observed else None,
        "mismatches": mismatches,
        "exact_incident_authority": mode == "EXACT_PROVIDER",
        "authority_allowed": "provider-parity classification",
        "authority_forbidden": ["exact parity from prefix match", "causal ownership", "patch", "repair count"],
    }
