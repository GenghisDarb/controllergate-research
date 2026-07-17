from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable


class ProviderSourceClass(str, Enum):
    SOURCE_DECLARED = "SOURCE_DECLARED"
    HISTORICAL_DECISION_TIME_SAFE = "HISTORICAL_DECISION_TIME_SAFE"
    ORTHOLOGY_TRANSFER_VERIFIED = "ORTHOLOGY_TRANSFER_VERIFIED"
    NEWLY_RECONSTRUCTED_EQUIVALENT = "NEWLY_RECONSTRUCTED_EQUIVALENT"
    UNAVAILABLE = "UNAVAILABLE"


FORBIDDEN_PROVIDER_EVIDENCE = frozenset(
    {
        "post_repair_result",
        "post_validation_result",
        "fixed_revision",
        "gold_patch",
        "terminal_class",
        "count_outcome",
        "target_incident_reproduced",
    }
)


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class ProviderRecipe:
    candidate_id: str
    source_commit: str
    supported_runtime_range: str
    supported_platforms: tuple[str, ...]
    historical_provider_evidence: tuple[str, ...]
    provider_source_class: ProviderSourceClass
    interpreter_identity: str
    abi_tags: tuple[str, ...]
    platform_tags: tuple[str, ...]
    dependency_lock_identity: str
    secondary_cofactor_lock_identity: str | None
    install_argv: tuple[str, ...]
    working_directory_policy: str
    environment_allowlist: tuple[str, ...]
    network_acquisition_policy: str
    target_argv: tuple[str, ...]
    semantic_outcome_contract_id: str
    positive_control_id: str
    negative_control_id: str
    selection_evidence_hashes: tuple[str, ...]
    selected_before_target_execution: bool
    orthology_source_environment: str
    orthology_target_environment: str
    preserved_invariants: tuple[str, ...]
    allowed_adaptations: tuple[str, ...]
    forbidden_adaptations: tuple[str, ...]
    producer_identity: str
    verifier_identity: str

    def validate(self) -> None:
        if len(self.source_commit) != 40 or any(value not in "0123456789abcdef" for value in self.source_commit.lower()):
            raise ValueError("exact source commit is required")
        if not self.selected_before_target_execution:
            raise ValueError("provider selection must be frozen before target execution")
        if self.provider_source_class is ProviderSourceClass.UNAVAILABLE:
            raise ValueError("unavailable provider cannot execute a target")
        if self.producer_identity == self.verifier_identity:
            raise ValueError("provider producer/verifier identity collision")
        if not self.interpreter_identity or not self.abi_tags or not self.platform_tags:
            raise ValueError("measured interpreter, ABI, and platform identities are required")
        if not self.dependency_lock_identity or not self.selection_evidence_hashes:
            raise ValueError("dependency lock and selection evidence are required")
        if not self.preserved_invariants:
            raise ValueError("orthology invariants are required")

    @property
    def recipe_hash(self) -> str:
        return _canonical_hash(self.record(include_hash=False))

    @property
    def provider_identity(self) -> str:
        return _canonical_hash(
            {
                "interpreter": self.interpreter_identity,
                "abi": self.abi_tags,
                "platform": self.platform_tags,
                "dependency_lock": self.dependency_lock_identity,
                "cofactor_lock": self.secondary_cofactor_lock_identity,
            }
        )

    def record(self, *, include_hash: bool = True) -> dict[str, Any]:
        value = {
            "candidate_id": self.candidate_id,
            "source_commit": self.source_commit,
            "source_declared_supported_runtime_range": self.supported_runtime_range,
            "source_declared_platform_assumptions": list(self.supported_platforms),
            "historical_decision_time_safe_provider_evidence": list(self.historical_provider_evidence),
            "provider_source_class": self.provider_source_class.value,
            "provider_image_or_interpreter_identity": self.interpreter_identity,
            "abi_tags": list(self.abi_tags),
            "platform_tags": list(self.platform_tags),
            "dependency_lock_identity": self.dependency_lock_identity,
            "secondary_cofactor_lock_identity": self.secondary_cofactor_lock_identity,
            "install_command": list(self.install_argv),
            "working_directory_policy": self.working_directory_policy,
            "environment_allowlist": list(self.environment_allowlist),
            "network_acquisition_policy": self.network_acquisition_policy,
            "project_target_command": list(self.target_argv),
            "semantic_outcome_contract_id": self.semantic_outcome_contract_id,
            "positive_control_id": self.positive_control_id,
            "negative_control_id": self.negative_control_id,
            "selection_evidence_hashes": list(self.selection_evidence_hashes),
            "selection_frozen_before_target_execution": self.selected_before_target_execution,
            "orthology_source_environment": self.orthology_source_environment,
            "orthology_target_environment": self.orthology_target_environment,
            "preserved_invariants": list(self.preserved_invariants),
            "allowed_adaptations": list(self.allowed_adaptations),
            "forbidden_adaptations": list(self.forbidden_adaptations),
            "producer_identity": self.producer_identity,
            "independent_verifier_identity": self.verifier_identity,
            "provider_identity": self.provider_identity,
        }
        if include_hash:
            value["recipe_hash"] = self.recipe_hash
        return value


def scan_provider_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else key
                if key.lower() in FORBIDDEN_PROVIDER_EVIDENCE and child not in (None, False, "", [], {}):
                    findings.append(child_path)
                visit(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(evidence, "")
    return {"status": "PASS" if not findings else "BLOCK", "forbidden_paths": sorted(findings)}


def verify_orthology_transfer(recipe: ProviderRecipe, observed: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    recipe.validate()
    expected_version = re.search(r"(\d+)\.(\d+)", recipe.interpreter_identity)
    observed_version = re.search(r"(\d+)\.(\d+)", str(observed.get("interpreter_identity", "")))
    observed_platform = str(observed.get("interpreter_identity", "")).lower()
    version_invariant = bool(expected_version and observed_version and expected_version.groups() == observed_version.groups())
    platform_invariant = any(platform_name.lower() in observed_platform for platform_name in recipe.supported_platforms)
    verified_transfer = observed.get("orthology_invariants_verified") is True and version_invariant and platform_invariant
    if observed.get("candidate_id") != recipe.candidate_id:
        reasons.append("candidate_relabeling_detected")
    if observed.get("source_commit") != recipe.source_commit:
        reasons.append("source_commit_mismatch")
    if observed.get("interpreter_identity") != recipe.interpreter_identity and not verified_transfer:
        reasons.append("unproven_interpreter_change")
    if tuple(observed.get("abi_tags", ())) != recipe.abi_tags and not verified_transfer:
        reasons.append("unproven_abi_change")
    if tuple(observed.get("platform_tags", ())) != recipe.platform_tags and not verified_transfer:
        reasons.append("unproven_platform_change")
    if observed.get("dependency_lock_identity") != recipe.dependency_lock_identity:
        reasons.append("dependency_lock_mismatch")
    if observed.get("selected_after_target_outcome") is True:
        reasons.append("provider_selected_after_target_outcome")
    scan = scan_provider_evidence(observed)
    if scan["status"] != "PASS":
        reasons.append("future_or_outcome_provider_evidence")
    return {
        "status": "PASS" if not reasons else "BLOCK",
        "candidate_id": recipe.candidate_id,
        "recipe_hash": recipe.recipe_hash,
        "provider_identity": recipe.provider_identity,
        "reasons": reasons,
        "future_outcome_scan": scan,
        "orthology_invariants_verified": verified_transfer,
        "observed_interpreter_identity": observed.get("interpreter_identity"),
        "observed_abi_tags": list(observed.get("abi_tags", ())),
        "observed_platform_tags": list(observed.get("platform_tags", ())),
        "producer_identity": "controllergate.amds.provider_orthology.verify_orthology_transfer",
        "authority_allowed": "candidate provider materialization",
        "authority_forbidden": ["target classification", "repair authority"],
    }


def audit_provider_identity_uniqueness(recipes: Iterable[ProviderRecipe]) -> dict[str, Any]:
    rows = list(recipes)
    identities = [row.provider_identity for row in rows]
    collisions = sorted({value for value in identities if identities.count(value) > 1})
    return {
        "status": "PASS" if not collisions else "BLOCK",
        "recipe_count": len(rows),
        "provider_identity_count": len(set(identities)),
        "collision_count": len(collisions),
        "collisions": collisions,
    }
