#!/usr/bin/env python3
"""Audit the v1.9 organic-style replay pilot plan."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_JSON_PATH = REPO_ROOT / "outputs" / "v1_9_organic_style_replay_pilot_plan.json"
PLAN_MD_PATH = REPO_ROOT / "outputs" / "v1_9_organic_style_replay_pilot_plan.md"
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)
V18_CAMPAIGN_ASSESSMENT_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
)
V18_CAMPAIGN_RESULTS_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "campaign_results.json"
)
EPISODE_003_RESULT_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json"
)
BETA_REPLAY_PLAN_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
)
ALPHA_CLASSIFICATION_PATH = (
    REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"
)

TARGET_CLASSES = {
    "user_owned_repo_discovered_failure",
    "user_owned_repo_semi_organic_failure",
    "forked_public_repo_discovered_failure",
    "forked_public_repo_issue_replay",
    "archived_public_repo_dependency_drift",
    "synthetic_seeded_fallback_only_if_no_discovered_failure",
}

REQUIRED_ARTIFACTS = {
    "episode_metadata.json",
    "target_repo_snapshot.json",
    "candidate_selection_record.json",
    "environment_snapshot.txt",
    "failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "pre_repair_replay_transcript.txt",
    "no_memory_decision_time_inputs.json",
    "no_memory_action_trace.json",
    "no_memory_repair_patch.diff",
    "no_memory_post_repair_log_raw.txt",
    "no_memory_outcome.json",
    "memory_enabled_decision_time_inputs.json",
    "memory_enabled_action_trace.json",
    "memory_evidence_used.json",
    "memory_enabled_repair_patch.diff",
    "memory_enabled_post_repair_log_raw.txt",
    "memory_enabled_outcome.json",
    "post_repair_comparison.json",
    "corruption_check_result.json",
    "decision_time_outcome_overlap_check.json",
    "limited_scoring_result.json",
    "proof_obligations_ledger.json",
    "SHA256SUMS.txt",
}

CLASSIFICATIONS = {
    "positive_evidence_memory_lift_organic_style_episode",
    "negative_evidence_no_memory_lift_organic_style_episode",
    "negative_evidence_memory_harm_or_corruption_organic_style_episode",
    "blocked_replay_gate_failed",
    "blocked_missing_baseline",
    "blocked_artifact_custody_failure",
    "blocked_decision_time_outcome_overlap",
    "inconclusive_equal_performance",
    "not_executed_resource_limit",
}


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return {}, [f"{path}: expected object"]
    return data, []


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


def require_list_contains(data: dict[str, Any], field: str, required: set[str], errors: list[str]) -> None:
    value = data.get(field)
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return
    observed = set(value)
    for item in sorted(required - observed):
        errors.append(f"{field} missing {item!r}")


def main() -> int:
    errors: list[str] = []
    plan, plan_errors = load_json(PLAN_JSON_PATH)
    v18_assessment, v18_assessment_errors = load_json(V18_CAMPAIGN_ASSESSMENT_PATH)
    v18_results, v18_results_errors = load_json(V18_CAMPAIGN_RESULTS_PATH)
    episode_003, episode_003_errors = load_json(EPISODE_003_RESULT_PATH)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY_PLAN_PATH)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING_PATH)
    alpha_classification, alpha_classification_errors = load_json(ALPHA_CLASSIFICATION_PATH)
    errors.extend(
        plan_errors
        + v18_assessment_errors
        + v18_results_errors
        + episode_003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_classification_errors
    )

    if plan.get("plan_id") != "v1_9_organic_style_replay_pilot_plan":
        errors.append("plan_id must be v1_9_organic_style_replay_pilot_plan")
    if plan.get("plan_status") != "planning_only_no_execution":
        errors.append("plan_status must be planning_only_no_execution")
    if plan.get("execution_status") != "not_executed":
        errors.append("execution_status must be not_executed")
    if plan.get("full_scoring_allowed") is not False:
        errors.append("v1.9 plan must keep full_scoring_allowed false")
    if plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v1.9 plan must keep ControllerGate full scoring NOT_RUN")
    if plan.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("v1.9 plan must not claim self-maintaining software")
    if plan.get("organic_external_memory_lift_claim_allowed") is not False:
        errors.append("v1.9 plan must not allow organic external memory-lift claim yet")
    if plan.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v1.9 plan must not demonstrate organic external memory lift yet")

    prior = plan.get("prior_evidence_summary")
    if not isinstance(prior, dict):
        errors.append("prior_evidence_summary must be an object")
        prior = {}
    if prior.get("seeded_controlled_memory_lift_supported_within_limited_scope") is not True:
        errors.append("v1.9 plan must preserve v1.8 seeded limited memory-lift support")
    if prior.get("organic_external_memory_lift_remains_undemonstrated") is not True:
        errors.append("v1.9 plan must state organic external memory lift remains undemonstrated")
    if prior.get("self_maintaining_software_remains_undemonstrated") is not True:
        errors.append("v1.9 plan must state self-maintaining software remains undemonstrated")
    episode_003_prior = prior.get("episode_003_result_preserved") if isinstance(prior.get("episode_003_result_preserved"), dict) else {}
    if episode_003_prior.get("classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("v1.9 plan must preserve Episode 003 negative result")

    require_list_contains(plan, "v1_9_target_classes", TARGET_CLASSES, errors)
    require_list_contains(plan, "required_per_episode_artifacts", REQUIRED_ARTIFACTS, errors)
    require_list_contains(plan, "evidence_classifications", CLASSIFICATIONS, errors)

    acceptance = "\n".join(str(item) for item in plan.get("acceptance_criteria") or [])
    for required in [
        "failure can be reproduced from clean checkout",
        "deterministic validator command exists",
        "no-memory and memory-enabled paths can run under identical replay conditions",
        "corruption/downstream checks can be defined",
        "all logs and artifacts can be captured and hashed",
        "decision-time/outcome separation can be enforced",
    ]:
        if required not in acceptance:
            errors.append(f"acceptance_criteria missing {required!r}")

    rejection = "\n".join(str(item) for item in plan.get("rejection_criteria") or [])
    for required in [
        "failure depends only on expired CI logs",
        "local replay cannot reproduce it",
        "setup requires private services or secrets",
        "validator is subjective",
        "artifact custody cannot be preserved",
        "baseline comparison cannot be run",
    ]:
        if required not in rejection:
            errors.append(f"rejection_criteria missing {required!r}")

    pilot = plan.get("pilot_design")
    if not isinstance(pilot, dict):
        errors.append("pilot_design must be an object")
        pilot = {}
    if pilot.get("episode_count_target") != "3_to_5":
        errors.append("pilot episode count target must be 3_to_5")
    if pilot.get("avoid_overfitting_to_v1_8_seeded_manifest_tasks") is not True:
        errors.append("pilot must avoid overfitting to v1.8 seeded manifest tasks")
    if pilot.get("full_scoring_allowed") is not False:
        errors.append("pilot full scoring must be false")
    if pilot.get("allowed_scoring_mode") != "limited_replay_scoring_only_if_all_gates_pass":
        errors.append("pilot allowed scoring mode must be limited_replay_scoring_only_if_all_gates_pass")

    aggregate = plan.get("aggregate_v1_9_rule")
    if not isinstance(aggregate, dict):
        errors.append("aggregate_v1_9_rule must be an object")
        aggregate = {}
    aggregate_rule = "\n".join(str(item) for item in aggregate.get("organic_style_memory_lift_demonstrated_only_if") or [])
    for required in [
        "at least 3 v1.9 episodes become deterministic replay-ready limited scoring episodes",
        "memory-enabled outperforms no-memory in at least 2 episodes",
        "no positive memory episode has corruption",
        "decision-time/outcome overlap remains 0",
        "replay/custody passes for all positive episodes",
    ]:
        if required not in aggregate_rule:
            errors.append(f"aggregate rule missing {required!r}")
    if aggregate.get("if_fewer_than_3_scoreable") != "insufficient_episode_count_for_organic_style_memory_lift":
        errors.append("aggregate insufficient-count classification mismatch")
    if aggregate.get("if_memory_never_outperforms_no_memory") != "negative_evidence_no_organic_style_memory_lift":
        errors.append("aggregate no-lift classification mismatch")
    if aggregate.get("if_all_candidates_blocked_by_replay_or_custody") != "blocked_candidate_acquisition_failure":
        errors.append("aggregate blocked acquisition classification mismatch")

    boundaries = plan.get("claim_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("claim_boundaries must be an object")
        boundaries = {}
    for field in [
        "full_scoring_remains_NOT_RUN",
        "self_maintaining_software_remains_not_demonstrated",
        "v1_8_seeded_controlled_memory_lift_does_not_imply_organic_external_memory_lift",
        "v1_9_organic_style_success_would_still_be_limited_replay_evidence_not_full_self_maintenance",
        "external_public_repo_results_must_be_labeled_separately_from_user_owned_repo_results",
    ]:
        if boundaries.get(field) is not True:
            errors.append(f"claim_boundaries.{field} must be true")

    distinctions = plan.get("evidence_type_distinctions")
    if not isinstance(distinctions, dict):
        errors.append("evidence_type_distinctions must be an object")
        distinctions = {}
    for key in [
        "seeded_controlled_evidence",
        "user_owned_discovered_or_semi_organic_evidence",
        "forked_public_repo_evidence",
        "organic_style_evidence",
    ]:
        if key not in distinctions:
            errors.append(f"evidence_type_distinctions missing {key}")

    if v18_assessment.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 campaign aggregate result must remain preserved")
    if v18_assessment.get("limited_seeded_controlled_memory_lift_criteria_met") is not True:
        errors.append("v1.8 limited seeded memory-lift criteria must remain true")
    if v18_assessment.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v1.8 must not demonstrate organic external memory lift")
    if v18_assessment.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v1.8 must not demonstrate self-maintaining software")
    if v18_results.get("decision_time_outcome_overlap_count") != 0:
        errors.append("v1.8 decision-time/outcome overlap must remain 0")

    if episode_003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 negative result must remain preserved")
    if episode_003.get("memory_lift_demonstrated") is not False:
        errors.append("Episode 003 memory lift must remain false")

    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper deterministic replay-ready count must remain 0")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    if beta_scoring.get("scoring_mode") != "limited_pilot_only":
        errors.append("beta must remain limited-pilot only")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(
        require_text(
            PLAN_MD_PATH,
            [
                "v1.8 is a real positive milestone",
                "v1.8 positive result is limited to seeded controlled replay tasks",
                "v1.9 should test whether the v1.8 memory advantage survives",
                "Organic-style memory lift remains undemonstrated unless",
                "Full scoring remains `NOT_RUN`.",
                "Self-maintaining software remains undemonstrated.",
                "Organic external memory lift remains undemonstrated.",
            ],
        )
    )
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v1.9 Organic-Style Replay Pilot Plan",
                "v1.8 met limited seeded controlled memory-lift criteria.",
                "v1.9 is designed to test organic-style replay evidence.",
                "Organic external memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )

    if errors:
        print("v1.9 organic-style replay pilot plan audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.9 organic-style replay pilot plan audit: PASS")
    print("plan status: planning_only_no_execution")
    print("v1.8 seeded result preserved: true")
    print("organic external memory lift demonstrated: false")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
