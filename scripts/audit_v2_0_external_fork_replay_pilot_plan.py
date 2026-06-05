#!/usr/bin/env python3
"""Audit the v2.0 external-fork replay pilot plan."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_JSON_PATH = REPO_ROOT / "outputs" / "v2_0_external_fork_replay_pilot_plan.json"
PLAN_MD_PATH = REPO_ROOT / "outputs" / "v2_0_external_fork_replay_pilot_plan.md"
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)
V19_COMPLETION_PATH = (
    REPO_ROOT / "outputs" / "v1_9_organic_style_replay_pilot_completion_pass" / "aggregate_v1_9_updated_memory_lift_assessment.json"
)
V19_PILOT_PATH = REPO_ROOT / "outputs" / "v1_9_episodes_011_013_organic_style_replay_pilot" / "pilot_results.json"
V18_CAMPAIGN_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
)
EPISODE_003_PATH = REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json"
BETA_REPLAY_PLAN_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
)
ALPHA_CLASSIFICATION_PATH = (
    REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"
)

TARGET_CLASSES = {
    "forked_public_repo_discovered_failure",
    "forked_public_repo_issue_replay",
    "archived_public_repo_dependency_drift",
    "public_benchmark_repo_realistic_failure",
    "user_owned_repo_fallback_only_if_external_acquisition_fails",
}

REQUIRED_ARTIFACTS = {
    "episode_metadata.json",
    "source_repo_metadata.json",
    "license_summary.txt",
    "candidate_selection_record.json",
    "target_repo_snapshot.json",
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
    "positive_evidence_memory_lift_external_fork_episode",
    "negative_evidence_no_memory_lift_external_fork_episode",
    "negative_evidence_memory_harm_or_corruption_external_fork_episode",
    "blocked_external_candidate_acquisition_failure",
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
    v19_completion, v19_completion_errors = load_json(V19_COMPLETION_PATH)
    v19_pilot, v19_pilot_errors = load_json(V19_PILOT_PATH)
    v18_campaign, v18_campaign_errors = load_json(V18_CAMPAIGN_PATH)
    episode_003, episode_003_errors = load_json(EPISODE_003_PATH)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY_PLAN_PATH)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING_PATH)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION_PATH)
    errors.extend(
        plan_errors
        + v19_completion_errors
        + v19_pilot_errors
        + v18_campaign_errors
        + episode_003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    if plan.get("plan_id") != "v2_0_external_fork_replay_pilot_plan":
        errors.append("plan_id must be v2_0_external_fork_replay_pilot_plan")
    if plan.get("plan_status") != "planning_only_no_execution":
        errors.append("plan_status must be planning_only_no_execution")
    if plan.get("execution_status") != "not_executed":
        errors.append("execution_status must be not_executed")
    if plan.get("full_scoring_allowed") is not False:
        errors.append("v2.0 plan must keep full_scoring_allowed false")
    if plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.0 plan must keep ControllerGate full scoring NOT_RUN")
    if plan.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("v2.0 plan must not claim self-maintaining software")
    if plan.get("external_memory_lift_claim_allowed") is not False:
        errors.append("v2.0 plan must not allow external memory-lift claim yet")
    if plan.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v2.0 plan must not demonstrate organic external memory lift")

    prior = plan.get("prior_evidence_summary") if isinstance(plan.get("prior_evidence_summary"), dict) else {}
    if prior.get("organic_external_memory_lift_remains_undemonstrated") is not True:
        errors.append("prior evidence must state organic external memory lift remains undemonstrated")
    if prior.get("self_maintaining_software_remains_undemonstrated") is not True:
        errors.append("prior evidence must state self-maintaining software remains undemonstrated")
    if prior.get("full_scoring_remains_disallowed") is not True:
        errors.append("prior evidence must state full scoring remains disallowed")
    episode_003_prior = prior.get("episode_003_result_preserved") if isinstance(prior.get("episode_003_result_preserved"), dict) else {}
    if episode_003_prior.get("classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("prior evidence must preserve Episode 003 negative result")
    v18_prior = prior.get("v1_8_seeded_campaign_result_preserved") if isinstance(prior.get("v1_8_seeded_campaign_result_preserved"), dict) else {}
    if v18_prior.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("prior evidence must preserve v1.8 seeded aggregate")
    v19_prior = prior.get("v1_9_user_owned_organic_style_result_preserved") if isinstance(prior.get("v1_9_user_owned_organic_style_result_preserved"), dict) else {}
    if v19_prior.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("prior evidence must preserve v1.9 user-owned organic-style aggregate")

    require_list_contains(plan, "target_classes", TARGET_CLASSES, errors)
    require_list_contains(plan, "required_per_episode_artifacts", REQUIRED_ARTIFACTS, errors)
    require_list_contains(plan, "evidence_classifications", CLASSIFICATIONS, errors)

    ethics = "\n".join(str(item) for item in plan.get("ethical_constraints") or [])
    for required in [
        "Do not open spam PRs or issues upstream.",
        "Do not exploit security vulnerabilities.",
        "Do not access secrets, private credentials, tokens, or private services.",
        "Use local fork/clone replay.",
        "Preserve license information.",
        "Attribute source repo metadata.",
        "Do not disrupt upstream maintainers.",
    ]:
        if required not in ethics:
            errors.append(f"ethical_constraints missing {required!r}")

    acceptance = "\n".join(str(item) for item in plan.get("candidate_acceptance_criteria") or [])
    for required in [
        "repo is public and forkable or locally cloneable",
        "failure can be reproduced from clean checkout",
        "deterministic test/build/lint/check command exists or can be locally defined without altering the claim",
        "logs can be captured locally",
        "no-memory and memory-enabled paths can run under identical replay conditions",
        "corruption/downstream checks can be defined",
        "all artifacts can be hashed",
        "decision-time/outcome separation can be enforced",
    ]:
        if required not in acceptance:
            errors.append(f"candidate_acceptance_criteria missing {required!r}")

    rejection = "\n".join(str(item) for item in plan.get("candidate_rejection_criteria") or [])
    for required in [
        "only evidence is expired remote CI",
        "local replay cannot reproduce failure",
        "setup requires secrets/private APIs",
        "task is security exploit focused",
        "validator is subjective",
        "license/ethics are unclear",
        "baseline comparison cannot be run",
        "artifact custody cannot be preserved",
    ]:
        if required not in rejection:
            errors.append(f"candidate_rejection_criteria missing {required!r}")

    pilot = plan.get("pilot_design") if isinstance(plan.get("pilot_design"), dict) else {}
    if pilot.get("episode_attempt_target") != "3_to_5":
        errors.append("pilot episode_attempt_target must be 3_to_5")
    if pilot.get("allowed_scoring_mode") != "limited_replay_scoring_only_if_all_external_fork_gates_pass":
        errors.append("pilot allowed scoring mode mismatch")
    if pilot.get("full_scoring_allowed") is not False:
        errors.append("pilot full_scoring_allowed must be false")
    criteria = pilot.get("minimum_aggregate_external_memory_lift_criteria") if isinstance(pilot.get("minimum_aggregate_external_memory_lift_criteria"), dict) else {}
    if criteria.get("minimum_scoreable_external_fork_episodes") != 3:
        errors.append("external aggregate minimum scoreable episodes must be 3")
    if criteria.get("minimum_positive_memory_outperformance_episodes") != 2:
        errors.append("external aggregate minimum positive episodes must be 2")
    if criteria.get("positive_episode_corruption_allowed") is not False:
        errors.append("external aggregate must disallow corruption in positive episodes")
    if criteria.get("decision_time_outcome_overlap_required") != 0:
        errors.append("external aggregate overlap required count must be 0")
    if criteria.get("replay_custody_required_for_positive_episodes") is not True:
        errors.append("external aggregate must require replay/custody for positives")
    aggregate_classes = pilot.get("aggregate_classifications") if isinstance(pilot.get("aggregate_classifications"), dict) else {}
    expected_aggregates = {
        "if_criteria_met": "limited_external_fork_memory_lift_criteria_met",
        "if_only_1_or_2_scoreable": "insufficient_episode_count_for_external_memory_lift",
        "if_no_external_candidates_acquired": "blocked_external_candidate_acquisition_failure",
        "if_memory_never_outperforms_no_memory": "negative_evidence_no_external_memory_lift",
    }
    for field, expected in expected_aggregates.items():
        if aggregate_classes.get(field) != expected:
            errors.append(f"aggregate_classifications.{field} must be {expected}")

    boundaries = plan.get("claim_boundaries") if isinstance(plan.get("claim_boundaries"), dict) else {}
    for field in [
        "external_fork_success_may_support_limited_external_fork_memory_lift_only",
        "full_scoring_remains_NOT_RUN",
        "self_maintaining_software_remains_not_demonstrated",
        "broad_organic_public_repo_performance_not_proven_without_aggregate_external_criteria",
        "seeded_controlled_and_user_owned_results_remain_labeled_separately",
        "user_owned_fallback_must_not_be_counted_as_external_fork_evidence",
    ]:
        if boundaries.get(field) is not True:
            errors.append(f"claim_boundaries.{field} must be true")

    distinctions = plan.get("evidence_type_distinctions") if isinstance(plan.get("evidence_type_distinctions"), dict) else {}
    for key in [
        "seeded_controlled_evidence",
        "user_owned_organic_style_evidence",
        "external_fork_evidence",
        "organic_external_evidence",
    ]:
        if key not in distinctions:
            errors.append(f"evidence_type_distinctions missing {key}")

    stop_conditions = "\n".join(str(item) for item in plan.get("stop_conditions") or [])
    for required in [
        "external candidate acquisition repeatedly fails",
        "replay gate repeatedly fails",
        "artifact custody fails",
        "decision-time/outcome leakage appears",
        "memory-enabled path causes repeated corruption",
        "resource limits prevent safe completion",
    ]:
        if required not in stop_conditions:
            errors.append(f"stop_conditions missing {required!r}")

    if v19_completion.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 completion aggregate must remain preserved")
    if v19_completion.get("organic_style_memory_lift_demonstrated") is not True:
        errors.append("v1.9 limited user-owned organic-style lift must remain true")
    if v19_completion.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v1.9 must not demonstrate organic external memory lift")
    if v19_completion.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v1.9 must not demonstrate self-maintaining software")
    if v19_completion.get("full_scoring_allowed") is not False:
        errors.append("v1.9 full scoring must remain false")
    if v19_pilot.get("scoreable_episode_count") != 2 or v19_pilot.get("positive_episode_count") != 2:
        errors.append("v1.9 initial pilot result must remain preserved")
    if v18_campaign.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 seeded campaign aggregate must remain preserved")
    if v18_campaign.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v1.8 must not demonstrate organic external memory lift")
    if episode_003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 negative result must remain preserved")
    if episode_003.get("memory_lift_demonstrated") is not False:
        errors.append("Episode 003 memory lift must remain false")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper deterministic replay-ready count must remain 0")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(
        require_text(
            PLAN_MD_PATH,
            [
                "v1.9 is a meaningful positive milestone",
                "User-owned organic-style evidence is stronger than seeded-only evidence",
                "v2.0 is designed to test whether the memory advantage survives outside Brad-owned repositories.",
                "Full scoring remains disallowed.",
                "Self-maintaining software remains undemonstrated.",
                "Organic external memory lift remains undemonstrated",
                "Limited external-fork memory lift can be claimed only if",
                "Blocked acquisition is not negative capability evidence.",
            ],
        )
    )
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v2.0 External-Fork Replay Pilot Plan",
                "v1.9 met limited user-owned organic-style memory-lift criteria.",
                "v2.0 is designed to test external/fork replay evidence.",
                "Organic external memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )

    if errors:
        print("v2.0 external-fork replay pilot plan audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.0 external-fork replay pilot plan audit: PASS")
    print("plan status: planning_only_no_execution")
    print("v1.9 limited user-owned organic-style memory lift preserved: true")
    print("organic external memory lift demonstrated: false")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
