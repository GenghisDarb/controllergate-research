from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


OWNERSHIP_CLASSES = {"source_owned", "provider_owned", "environment_owned", "platform_owned", "network_or_transport_owned", "harness_owned", "test_or_expectation_fragility", "mixed_failure", "insufficient_evidence"}


@dataclass(frozen=True)
class Diagnosis:
    classification: str
    direct_evidence: tuple[str, ...]
    patch_authorized: bool


def diagnose(observations: Iterable[dict[str, object]], *, memory_enabled: bool = True) -> Diagnosis:
    rows = list(observations)
    direct = [str(row["classification"]) for row in rows if row.get("direct") is True and row.get("classification") in OWNERSHIP_CLASSES]
    if not direct:
        return Diagnosis("insufficient_evidence", (), False)
    unique = set(direct)
    classification = next(iter(unique)) if len(unique) == 1 else "mixed_failure"
    patch = classification == "source_owned" and any(row.get("source_contact_verified") is True for row in rows)
    return Diagnosis(classification, tuple(direct), patch)


def quality_gate(diagnoses: Iterable[Diagnosis], truths: Iterable[str]) -> dict[str, object]:
    pairs = list(zip(diagnoses, truths))
    wrong_authorizations = sum(item.patch_authorized and truth != "source_owned" for item, truth in pairs)
    return {"status": "PASS" if wrong_authorizations == 0 else "FAIL", "episode_count": len(pairs), "wrong_authorization_count": wrong_authorizations}
