from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .stable_identity import stable_hash


class VariantEffect(str, Enum):
    SEMANTIC_NO_OP = "SEMANTIC_NO_OP"
    BEHAVIOR_CHANGING = "BEHAVIOR_CHANGING"
    PACKAGING_ONLY = "PACKAGING_ONLY"
    TEST_ONLY_FORBIDDEN = "TEST_ONLY_FORBIDDEN"
    PROVIDER_ONLY = "PROVIDER_ONLY"
    DOCUMENTATION_ONLY = "DOCUMENTATION_ONLY"
    UNKNOWN_EFFECT = "UNKNOWN_EFFECT"


@dataclass(frozen=True)
class ConstitutionFrame:
    candidate_id: str
    run_id: str
    source_revision: str
    source_tree_hash: str
    test_tree_hash: str
    provider_graph_hash: str
    runtime_abi: str
    platform: str
    environment_hash: str
    command_hash: str
    target_hash: str
    harness_hash: str
    runner_hash: str
    network_policy: str
    workspace_layout_hash: str

    @property
    def frame_hash(self) -> str:
        return stable_hash(asdict(self))


@dataclass(frozen=True)
class ManifestationFrame:
    constitution_hash: str
    return_code: int | None
    exception_type: str | None
    structured_result_hash: str
    output_hash: str
    elapsed_ms: int
    resource_state_hash: str
    first_divergent_event: str | None
    affected_behaviors: tuple[str, ...]

    @property
    def frame_hash(self) -> str:
        return stable_hash(asdict(self))


def environmental_mimic_exclusions(observations: dict[str, bool]) -> dict[str, Any]:
    required = ("provider", "environment", "platform", "harness", "transport")
    unresolved = [name for name in required if not observations.get(name, False)]
    return {
        "required_exclusions": list(required),
        "unresolved": unresolved,
        "source_ownership_allowed": not unresolved,
        "status": "PASS" if not unresolved else "BLOCK",
    }


def conditional_manifestation(outcomes: list[bool]) -> dict[str, Any]:
    total = len(outcomes)
    reproduced = sum(outcomes)
    return {
        "compatible_environment_count": total,
        "reproduction_count": reproduced,
        "reliability": reproduced / total if total else 0.0,
        "causal_authority": False,
    }


def classify_variant(*, source_changed: bool, tests_changed: bool = False, provider_changed: bool = False,
                     packaging_changed: bool = False, documentation_changed: bool = False,
                     semantic_delta: bool = False) -> VariantEffect:
    if tests_changed:
        return VariantEffect.TEST_ONLY_FORBIDDEN
    if source_changed:
        return VariantEffect.BEHAVIOR_CHANGING if semantic_delta else VariantEffect.SEMANTIC_NO_OP
    if provider_changed:
        return VariantEffect.PROVIDER_ONLY
    if packaging_changed:
        return VariantEffect.PACKAGING_ONLY
    if documentation_changed:
        return VariantEffect.DOCUMENTATION_ONLY
    return VariantEffect.UNKNOWN_EFFECT


def deduplicate_symptoms(records: list[dict[str, str]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[str]] = {}
    for record in records:
        groups.setdefault((record["causal_event_hash"], record["patch_hash"]), []).append(record["symptom_id"])
    return {
        "causal_episode_count": len(groups),
        "symptom_count": len(records),
        "groups": [{"causal_event_hash": key[0], "patch_hash": key[1], "symptoms": sorted(value)} for key, value in sorted(groups.items())],
    }
