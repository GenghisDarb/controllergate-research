from __future__ import annotations

from typing import Any


PROBE_TYPES = [
    "dependency_lock_probe",
    "issue_timestamp_probe",
    "target_intent_probe",
    "command_variant_probe",
    "source_commit_window_probe",
    "native_test_presence_probe",
    "issue_derived_harness_firewall_probe",
    "runtime_incident_probe",
    "ast_excision_probe",
    "null_comparability_probe",
    "curvature_route_diversity_probe",
    "interlock_invariant_probe",
    "seed_replacement_probe",
]


def probe_selection_formula() -> dict[str, Any]:
    return {
        "status": "PASS",
        "formula_id": "deterministic_expected_probe_utility_v1",
        "formula": "expected_information_gain - expected_probe_cost - expected_probe_risk - provenance_uncertainty_penalty - dependency_uncertainty_penalty - claim_boundary_penalty",
        "deterministic": True,
        "frozen_before_candidate_evaluation": True,
    }


def score_probe(probe: dict[str, Any]) -> float:
    return float(probe.get("expected_information_gain", 0)) - float(probe.get("expected_probe_cost", 0)) - float(probe.get("expected_probe_risk", 0)) - float(probe.get("provenance_uncertainty_penalty", 0)) - float(probe.get("dependency_uncertainty_penalty", 0)) - float(probe.get("claim_boundary_penalty", 0))


def select_probe(probes: list[dict[str, Any]]) -> dict[str, Any]:
    allowed = [probe for probe in probes if probe.get("probe_type") in PROBE_TYPES and probe.get("forbidden_evidence_used") is not True]
    if not allowed:
        return {"status": "BLOCK", "blocker": "probe_selection_policy_missing", "selected_probe": None}
    scored = [{**probe, "expected_probe_utility": score_probe(probe)} for probe in allowed]
    scored.sort(key=lambda item: (-float(item["expected_probe_utility"]), str(item.get("probe_id", ""))))
    selected = scored[0]
    return {
        "status": "PASS",
        "selected_probe": selected,
        "all_scored_probes": scored,
        "formula": probe_selection_formula(),
        "forbidden_evidence_used": False,
    }


def probe_budget_policy(max_probes: int = 8) -> dict[str, Any]:
    return {
        "status": "PASS",
        "max_probes": max_probes,
        "external_network_calls_allowed_by_default": False,
        "source_mutation_allowed": False,
        "future_fixed_gold_pr_evidence_allowed": False,
        "blocker": "probe_budget_exceeded",
    }
