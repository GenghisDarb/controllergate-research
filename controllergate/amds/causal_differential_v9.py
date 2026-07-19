"""Causal-evidence hierarchy and matched-intervention analysis for Batch099."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


EVIDENCE_LEVELS = (
    "PRESENCE_VERIFIED",
    "CONTACT_VERIFIED",
    "CORRELATION_VERIFIED",
    "DIMENSION_SENSITIVITY_VERIFIED",
    "NECESSITY_SUPPORTED",
    "SUFFICIENCY_SUPPORTED",
    "INTERACTION_SUPPORTED",
    "OWNERSHIP_SUPPORTED",
)

OWNERSHIP_CLASSES = (
    "SOURCE_OWNED_BEHAVIOR_DEFECT",
    "PROVIDER_OWNED",
    "ENVIRONMENT_PLATFORM_OWNED",
    "RUNNER_OWNED",
    "HARNESS_FIXTURE_OWNED",
    "SERVICE_TRANSPORT_OWNED",
    "TEST_EXPECTATION_FRAGILITY",
    "MIXED_FAILURE",
)

ROOT_CLASSES = (
    "false_mutual_exclusion",
    "contact_mistaken_for_causation",
    "two_legitimate_co_causes",
    "insufficiently_controlled_counterfactual",
    "probe_semantic_overreach",
    "duplicated_evidence_expressed_as_separate_classes",
    "real_mixed_failure",
    "genuine_logical_contradiction",
)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class CausalEvidenceFact:
    fact_id: str
    candidate_id: str
    arm_id: str
    causal_class_proposal: str
    evidence_level: str
    relation_established: str
    observation_id: str
    operation_id: str
    probe_id: str
    partition_key: str
    evidence_parent_hash: str
    ownership_supported: bool
    authority_allowed: str = "constraint update at the recorded evidence level only"
    authority_forbidden: tuple[str, ...] = ("ownership escalation", "repair", "repair count", "release")


@dataclass(frozen=True)
class MatchedCounterfactualPair:
    pair_id: str
    candidate_id: str
    proposed_causal_family: str
    changed_dimension: str
    held_invariants: tuple[str, ...]
    incident_operation_id: str
    control_operation_id: str
    incident_observation: dict[str, Any]
    control_observation: dict[str, Any]
    incident_semantic_verification: str
    control_semantic_verification: str
    outcome_difference: bool
    typed_incident_materialized: bool
    single_dimension_change: bool
    necessity_supported: bool
    sufficiency_supported: bool
    interaction_supported: bool
    alternative_explanations: tuple[str, ...]
    cleanup_status: str
    evidence_level: str
    ownership_supported: bool
    status: str
    authority_allowed: str = "causal sensitivity evidence at the verified level"
    authority_forbidden: tuple[str, ...] = ("sealed-truth inference", "repair", "repair count", "release")


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def classify_existing_facts(facts: list[dict[str, Any]], observations: list[dict[str, Any]]) -> list[CausalEvidenceFact]:
    observation_by_id = {row["operation_id"]: row for row in observations}
    classified: list[CausalEvidenceFact] = []
    for fact in facts:
        observation = observation_by_id[fact["observation_id"]]
        # Batch098 observations assert only that a kind/subject pair was emitted.
        # No held-invariant paired intervention is present in these records.
        classified.append(CausalEvidenceFact(
            fact_id=fact["fact_id"], candidate_id=fact["candidate_id"], arm_id=fact["arm_id"],
            causal_class_proposal=fact["causal_class"], evidence_level="CONTACT_VERIFIED",
            relation_established="contact", observation_id=fact["observation_id"],
            operation_id=observation["operation_id"], probe_id=observation["probe_id"],
            partition_key=observation["partition_key"], evidence_parent_hash=observation["structured_product_hash"],
            ownership_supported=False,
        ))
    return classified


def reconstruct_contradiction_roots(
    branches: list[dict[str, Any]], classified_facts: list[CausalEvidenceFact], observations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fact_index: dict[tuple[str, str, str], list[CausalEvidenceFact]] = defaultdict(list)
    for fact in classified_facts:
        fact_index[(fact.candidate_id, fact.arm_id, fact.causal_class_proposal)].append(fact)
    roots: list[dict[str, Any]] = []
    for branch in branches:
        parents = []
        for causal_class in branch["mutually_exclusive_classes"]:
            matching = fact_index[(branch["candidate_id"], branch["arm_id"], causal_class)]
            if matching:
                parent = matching[0]
                parents.append({
                    "causal_class": causal_class, "fact_id": parent.fact_id,
                    "evidence_level": parent.evidence_level, "relation_established": parent.relation_established,
                    "probe_id": parent.probe_id, "operation_id": parent.operation_id,
                    "observation_id": parent.observation_id, "evidence_parent_hash": parent.evidence_parent_hash,
                    "ownership_supported": False,
                })
        root = {
            "contradiction_id": branch["failed_branch_id"], "candidate_id": branch["candidate_id"],
            "arm_id": branch["arm_id"], "round": branch["round"],
            "original_classes": branch["mutually_exclusive_classes"], "evidence_parents": parents,
            "root_classification": "false_mutual_exclusion",
            "secondary_classification": "contact_mistaken_for_causation",
            "reason": "multiple contact-level facts may coexist; none is a matched differential ownership fact",
            "genuine_logical_contradiction": False, "ownership_fact_survives": False,
            "corrected_constraint_action": "retain contacts as compatible provisional evidence and require matched intervention",
        }
        root["root_receipt"] = f"contradiction-root:{canonical_hash(root)}"
        roots.append(root)
    by_candidate = Counter(row["candidate_id"] for row in roots)
    by_arm = Counter(row["arm_id"] for row in roots)
    by_class = Counter(row["root_classification"] for row in roots)
    summary = {
        "status": "PASS",
        "contradiction_count": len(roots),
        "classified_count": len(roots),
        "classification_distribution": dict(by_class),
        "candidate_distribution": dict(sorted(by_candidate.items())),
        "arm_distribution": dict(sorted(by_arm.items())),
        "genuine_logical_contradiction_count": sum(row["genuine_logical_contradiction"] for row in roots),
        "false_mutual_exclusion_count": sum(row["root_classification"] == "false_mutual_exclusion" for row in roots),
        "ownership_facts_surviving_contact_only": sum(row["ownership_fact_survives"] for row in roots),
        "symmetric_54_per_candidate_detected": set(by_candidate.values()) == {54},
        "official_ingest_binding_required": True,
    }
    return roots, summary


def _candidate_directories(decision_root: Path) -> list[Path]:
    return sorted((decision_root / "evidence").glob("batch098-public-candidate-*"))


def _proposed_family(candidate_id: str, control_kind: str) -> str:
    if "service" in control_kind or "openbb" in candidate_id:
        return "SERVICE_TRANSPORT_OWNED"
    if "datetime" in control_kind or "warning" in candidate_id:
        return "TEST_EXPECTATION_FRAGILITY"
    if "import" in control_kind or "audioread" in candidate_id:
        return "ENVIRONMENT_PLATFORM_OWNED"
    if "source" in control_kind or "darker" in candidate_id or "bugger" in candidate_id:
        return "SOURCE_OWNED_BEHAVIOR_DEFECT"
    if "precondition" in control_kind:
        return "HARNESS_FIXTURE_OWNED"
    return "UNRESOLVED"


def _changed_dimension(candidate_id: str, control_kind: str, control_id: str) -> str:
    if "git-dir" in control_id:
        return "environment.GIT_DIR"
    if "service" in control_id:
        return "service_availability"
    if "datetime" in control_kind or "runtime_behavior" in control_kind:
        return "runner_harness_route"
    if "import" in control_kind:
        return "import_target"
    if "collect" in control_kind:
        return "collection_vs_execution"
    if "precondition" in control_kind:
        return "execution_precondition"
    return "command_or_input_route"


def build_existing_counterfactual_audit(decision_root: Path) -> list[MatchedCounterfactualPair]:
    pairs: list[MatchedCounterfactualPair] = []
    for directory in _candidate_directories(decision_root):
        lane = json.loads((directory / "candidate_lane_result_v2.json").read_text(encoding="utf-8"))
        target = json.loads((directory / "neutral_observation_v2.json").read_text(encoding="utf-8"))
        real_controls = [row for row in lane["controls"] if row["control_kind"] != "copied_evidence_semantic_mutation"]
        for control in real_controls:
            changed = _changed_dimension(lane["candidate_id"], control["control_kind"], control["control_id"])
            family = _proposed_family(lane["candidate_id"], control["control_kind"])
            incident = {"return_code": target["return_code"], "stdout_sha256": target["stdout_sha256"], "stderr_sha256": target["stderr_sha256"]}
            comparison = {"return_code": control.get("return_code"), "stdout_sha256": str(control.get("raw_stdout_object", "")).removeprefix("sha256:"), "stderr_sha256": str(control.get("raw_stderr_object", "")).removeprefix("sha256:")}
            outcome_difference = incident != comparison
            typed_materialized = bool(lane["typed_incident"].get("typed_incident_materialized"))
            single_dimension = changed in {"environment.GIT_DIR", "service_availability"}
            alternative_explanations = []
            if not typed_materialized:
                alternative_explanations.append("registered incident was not independently materialized")
            if not single_dimension:
                alternative_explanations.append("command, input, runner, or harness changed with the proposed dimension")
            if not outcome_difference:
                alternative_explanations.append("paired outcomes are identical")
            sensitivity = typed_materialized and outcome_difference
            evidence_level = "DIMENSION_SENSITIVITY_VERIFIED" if sensitivity else "CONTACT_VERIFIED"
            pair_seed = [lane["candidate_id"], target["operation_id"], control["operation_id"]]
            pair = MatchedCounterfactualPair(
                pair_id=f"counterfactual:{canonical_hash(pair_seed)}", candidate_id=lane["candidate_id"],
                proposed_causal_family=family, changed_dimension=changed,
                held_invariants=(f"source_commit:{lane['source_commit']}", f"frame_id:{lane['frame_id']}", "provider_capsule", "candidate_contract"),
                incident_operation_id=target["operation_id"], control_operation_id=control["operation_id"],
                incident_observation=incident, control_observation=comparison,
                incident_semantic_verification=lane["typed_incident"].get("verification_receipt", ""),
                control_semantic_verification=control.get("semantic_verification_receipt", ""),
                outcome_difference=outcome_difference, typed_incident_materialized=typed_materialized,
                single_dimension_change=single_dimension, necessity_supported=False, sufficiency_supported=False,
                interaction_supported=False, alternative_explanations=tuple(alternative_explanations),
                cleanup_status=lane["cleanup"]["status"], evidence_level=evidence_level,
                ownership_supported=False,
                status="SENSITIVITY_ONLY" if sensitivity else "BLOCKED_INADEQUATE_COUNTERFACTUAL",
            )
            pairs.append(pair)
    return pairs


def counterfactual_contracts(ingest_receipt_sha256: str) -> list[dict[str, Any]]:
    definitions = (
        ("PROVIDER_OWNED", "provider identity", "compatible provider A/B"),
        ("ENVIRONMENT_PLATFORM_OWNED", "environment/platform", "environment A/B"),
        ("RUNNER_OWNED", "runner", "direct/runner invocation"),
        ("HARNESS_FIXTURE_OWNED", "harness/fixture", "fixture present/absent"),
        ("SERVICE_TRANSPORT_OWNED", "service/transport", "available/unavailable"),
        ("TEST_EXPECTATION_FRAGILITY", "authoritative oracle", "actual behavior/oracle"),
        ("SOURCE_OWNED_BEHAVIOR_DEFECT", "implicated source contact", "implicated/control route"),
        ("MIXED_FAILURE", "two-factor interaction", "2x2 factorial comparison"),
    )
    rows = []
    for family, dimension, comparison in definitions:
        row = {
            "contract_id": f"batch099-counterfactual-{family.lower()}", "causal_family": family,
            "changed_dimension": dimension, "required_comparison": comparison,
            "held_invariants_required": ["source revision", "provider unless changed", "command unless changed", "runner unless changed", "harness unless changed", "incident input", "resource budget"],
            "required_records": ["both operation IDs", "both observations", "both semantic verifications", "outcome difference", "alternative explanations", "cleanup"],
            "ownership_requirements": ["typed incident materialized", "single relevant dimension changed", "necessity or sufficiency supported", "alternative ownership excluded"],
            "official_ingest_receipt_sha256": ingest_receipt_sha256,
            "authority_allowed": "future narrow counterfactual execution",
            "authority_forbidden": ["ownership from contact", "repair", "repair count", "release"],
        }
        row["contract_hash"] = canonical_hash(row)
        rows.append(row)
    return rows


def corrected_constraint_replay(classified_facts: list[CausalEvidenceFact], candidates: Iterable[str], policies: Iterable[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    terminals = []
    for candidate in sorted(set(candidates)):
        for policy in policies:
            relevant = [fact for fact in classified_facts if fact.candidate_id == candidate and fact.arm_id == policy]
            ownership = [fact for fact in relevant if fact.ownership_supported]
            terminal = {
                "candidate_id": candidate, "policy_id": policy,
                "terminal_class": ownership[0].causal_class_proposal if len(ownership) == 1 else "INSUFFICIENT_EVIDENCE",
                "contact_fact_count": len(relevant), "ownership_fact_count": len(ownership),
                "genuine_contradiction_count": 0,
                "legal_counterfactual_exhaustion": "BLOCKED_NARROW_COUNTERFACTUAL_EXECUTION_REQUIRED",
                "authority_allowed": "historical diagnostic terminal only",
                "authority_forbidden": ["repair", "repair count", "release"],
            }
            terminal["terminal_seal"] = canonical_hash(terminal)
            terminals.append(terminal)
    distribution = Counter(row["terminal_class"] for row in terminals)
    summary = {
        "status": "PASS_WITH_SCIENTIFIC_BLOCK",
        "terminal_count": len(terminals), "terminal_distribution": dict(distribution),
        "contact_fact_count": len(classified_facts), "ownership_fact_count": sum(fact.ownership_supported for fact in classified_facts),
        "genuine_contradiction_count": 0, "false_mutual_exclusion_count_after_correction": 0,
        "nonbaseline_causal_coverage": 0.0, "false_attribution_count": 0,
        "active_blocker": "matched_counterfactual_execution_not_available_in_frozen_artifact",
    }
    return terminals, summary
