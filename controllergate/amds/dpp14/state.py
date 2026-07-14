from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


HYPOTHESES = (
    "source_owned_behavior_defect", "provider_owned", "environment_owned",
    "platform_owned", "network_or_transport_owned", "harness_owned",
    "test_or_expectation_fragility", "mixed_failure", "insufficient_evidence",
)


@dataclass
class DPP14State:
    candidate_id: str
    frozen_frame: dict[str, Any]
    hypotheses: list[str] = field(default_factory=lambda: list(HYPOTHESES))
    observations: list[dict[str, Any]] = field(default_factory=list)
    certain_facts: list[dict[str, Any]] = field(default_factory=list)
    contradictions: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    terminal: str = "insufficient_evidence"

    def record(self) -> dict[str, Any]:
        return {key: value for key, value in vars(self).items()}
