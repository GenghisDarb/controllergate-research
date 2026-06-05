#!/usr/bin/env python3
"""Audit the v2.1 external candidate acquisition harness plan."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_JSON_PATH = REPO_ROOT / "outputs" / "v2_1_external_candidate_acquisition_harness_plan.json"
PLAN_MD_PATH = REPO_ROOT / "outputs" / "v2_1_external_candidate_acquisition_harness_plan.md"
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)
V20_RESULTS_PATH = REPO_ROOT / "outputs" / "v2_0_external_fork_replay_pilot" / "pilot_results.json"
V19_COMPLETION_PATH = (
    REPO_ROOT
    / "outputs"
    / "v1_9_organic_style_replay_pilot_completion_pass"
    / "aggregate_v1_9_updated_memory_lift_assessment.json"
)
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

SOURCE_TIERS = {
    "tier_1_curated_bug_benchmarks",
    "tier_2_small_public_repos_with_simple_tests",
    "tier_3_archived_public_repos_with_dependency_drift",
    "tier_4_forked_issue_replay_candidates",
    "tier_5_user_owned_fallback_not_external",
}

PREFLIGHT_CHECKS = {
    "clone/fork availability",
    "license/ethics screen",
    "language/ecosystem detection",
    "dependency install command detection",
    "test/build/lint command detection",
    "clean checkout baseline command result",
    "deterministic failure presence or reproducible issue branch",
    "no private secrets/services required",
    "runtime under pilot budget",
    "artifact capture feasibility",
    "baseline comparison feasibility",
    "corruption/downstream check feasibility",
}

REJECTION_REASONS = {
    "rejected_no_local_test_command",
    "rejected_no_deterministic_failure",
    "rejected_private_service_required",
    "rejected_license_or_ethics_unclear",
    "rejected_runtime_too_large",
    "rejected_environment_not_reproducible",
    "rejected_subjective_validator",
    "rejected_security_exploit_target",
    "rejected_remote_ci_only",
    "rejected_no_baseline_path",
    "rejected_no_corruption_check",
}

FUTURE_OUTPUTS = {
    "external_candidate_search_log.json",
    "external_candidate_preflight_results.json",
    "external_candidate_ranked_pool.json",
    "external_candidate_rejection_table.json",
    "external_candidate_replay_readiness_summary.md",
    "SHA256SUMS.txt",
}

V22_HANDOFF = {
    "readiness score meets threshold",
    "clean checkout can be reproduced",
    "deterministic failure exists",
    "no-memory and memory-enabled paths are feasible",
    "corruption check is defined",
    "artifact custody plan is complete",
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
    missing = sorted(required - observed)
    for item in missing:
        errors.append(f"{field} missing {item!r}")


def main() -> int:
    errors: list[str] = []
    plan, plan_errors = load_json(PLAN_JSON_PATH)
    v20, v20_errors = load_json(V20_RESULTS_PATH)
    v19, v19_errors = load_json(V19_COMPLETION_PATH)
    v18, v18_errors = load_json(V18_CAMPAIGN_PATH)
    episode_003, episode_003_errors = load_json(EPISODE_003_PATH)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY_PLAN_PATH)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING_PATH)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION_PATH)
    errors.extend(
        plan_errors
        + v20_errors
        + v19_errors
        + v18_errors
        + episode_003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    if plan.get("plan_id") != "v2_1_external_candidate_acquisition_harness_plan":
        errors.append("plan_id must be v2_1_external_candidate_acquisition_harness_plan")
    if plan.get("plan_status") != "planning_only_no_execution":
        errors.append("plan_status must be planning_only_no_execution")
    if plan.get("execution_status") != "not_executed":
        errors.append("execution_status must be not_executed")
    if plan.get("full_scoring_allowed") is not False:
        errors.append("v2.1 plan must keep full_scoring_allowed false")
    if plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.1 plan must keep ControllerGate full scoring NOT_RUN")
    if plan.get("external_memory_lift_claim_allowed") is not False:
        errors.append("v2.1 plan must not allow an external memory-lift claim")
    if plan.get("external_memory_lift_demonstrated") is not False:
        errors.append("v2.1 plan must not demonstrate external memory lift")
    if plan.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v2.1 plan must not demonstrate organic external memory lift")
    if plan.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("v2.1 plan must not allow self-maintaining software claim")
    if plan.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.1 plan must not demonstrate self-maintaining software")

    prior = plan.get("prior_evidence_summary") if isinstance(plan.get("prior_evidence_summary"), dict) else {}
    v20_prior = prior.get("v2_0_blocked_acquisition_result_preserved") if isinstance(prior.get("v2_0_blocked_acquisition_result_preserved"), dict) else {}
    if v20_prior.get("aggregate_classification") != "blocked_external_candidate_acquisition_failure":
        errors.append("prior evidence must preserve v2.0 blocked acquisition result")
    if v20_prior.get("scoreable_external_fork_episode_count") != 0:
        errors.append("prior evidence must preserve zero v2.0 scoreable external/fork episodes")
    if "not negative capability evidence" not in str(v20_prior.get("interpretation")):
        errors.append("prior evidence must state v2.0 is not negative capability evidence")
    v19_prior = prior.get("v1_9_user_owned_organic_style_result_preserved") if isinstance(prior.get("v1_9_user_owned_organic_style_result_preserved"), dict) else {}
    if v19_prior.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("prior evidence must preserve v1.9 limited user-owned result")
    v18_prior = prior.get("v1_8_seeded_campaign_result_preserved") if isinstance(prior.get("v1_8_seeded_campaign_result_preserved"), dict) else {}
    if v18_prior.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("prior evidence must preserve v1.8 limited seeded result")
    episode_003_prior = prior.get("episode_003_result_preserved") if isinstance(prior.get("episode_003_result_preserved"), dict) else {}
    if episode_003_prior.get("classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("prior evidence must preserve Episode 003 no-memory-lift result")
    if prior.get("external_memory_lift_remains_undemonstrated") is not True:
        errors.append("prior evidence must state external memory lift remains undemonstrated")
    if prior.get("self_maintaining_software_remains_undemonstrated") is not True:
        errors.append("prior evidence must state self-maintaining software remains undemonstrated")
    if prior.get("full_scoring_remains_disallowed") is not True:
        errors.append("prior evidence must state full scoring remains disallowed")

    tiers = plan.get("candidate_source_tiers")
    if not isinstance(tiers, list):
        errors.append("candidate_source_tiers must be a list")
    else:
        observed_tiers = {item.get("tier") for item in tiers if isinstance(item, dict)}
        for tier in sorted(SOURCE_TIERS - observed_tiers):
            errors.append(f"candidate_source_tiers missing {tier!r}")
        ranks = [item.get("rank") for item in tiers if isinstance(item, dict)]
        if ranks != sorted(ranks):
            errors.append("candidate source tiers must be ranked in ascending order")
    require_list_contains(plan, "candidate_preflight_checks", PREFLIGHT_CHECKS, errors)
    require_list_contains(plan, "rejection_reasons", REJECTION_REASONS, errors)
    require_list_contains(plan, "future_harness_output_artifacts", FUTURE_OUTPUTS, errors)
    require_list_contains(plan, "v2_2_handoff_criteria", V22_HANDOFF, errors)

    preferred = "\n".join(str(item) for item in plan.get("preferred_ecosystems") or [])
    for required in [
        "Python with pytest/unittest and requirements/pyproject",
        "JavaScript/TypeScript with npm test and lockfile",
        "Rust with cargo test",
        "Go with go test",
        "small Java/Maven/Gradle only if runtime is bounded",
    ]:
        if required not in preferred:
            errors.append(f"preferred_ecosystems missing {required!r}")
    deprioritized = "\n".join(str(item) for item in plan.get("deprioritized_ecosystems") or [])
    if "Flutter/Android unless environment is already stable" not in deprioritized:
        errors.append("deprioritized ecosystems must avoid Flutter/Android unless stable")

    scoring = plan.get("candidate_readiness_scoring") if isinstance(plan.get("candidate_readiness_scoring"), dict) else {}
    if scoring.get("score_range") != "0_to_100":
        errors.append("candidate readiness score range must be 0_to_100")
    if scoring.get("minimum_threshold_for_v2_2_execution") != 75:
        errors.append("minimum v2.2 readiness threshold must be 75")
    criteria = scoring.get("criteria") if isinstance(scoring.get("criteria"), list) else []
    point_sum = sum(item.get("points", 0) for item in criteria if isinstance(item, dict))
    if point_sum != 100:
        errors.append(f"candidate readiness scoring points must sum to 100, observed {point_sum}")
    observed_criteria = {item.get("criterion") for item in criteria if isinstance(item, dict)}
    for criterion in [
        "deterministic_local_command",
        "failure_reproducibility",
        "simple_environment",
        "license_clarity",
        "runtime_budget",
        "baseline_comparability",
        "memory_relevance",
        "corruption_check_availability",
        "artifact_custody_ease",
    ]:
        if criterion not in observed_criteria:
            errors.append(f"candidate readiness scoring missing criterion {criterion!r}")

    boundaries = plan.get("claim_boundaries") if isinstance(plan.get("claim_boundaries"), dict) else {}
    for field in [
        "candidate_acquisition_success_is_not_repair_success",
        "candidate_pool_creation_is_not_external_memory_lift",
        "blocked_candidates_are_not_negative_capability_evidence",
        "external_memory_lift_requires_scoreable_v2_2_episodes",
        "self_maintaining_software_remains_undemonstrated",
        "full_scoring_remains_disallowed",
        "user_owned_fallback_must_not_count_as_external_evidence",
    ]:
        if boundaries.get(field) is not True:
            errors.append(f"claim_boundaries.{field} must be true")

    next_stage = plan.get("v2_2_expected_next_stage") if isinstance(plan.get("v2_2_expected_next_stage"), dict) else {}
    if next_stage.get("scoring_allowed") is not False:
        errors.append("v2.2 preflight handoff stage must not allow scoring")
    if next_stage.get("repair_execution_allowed") is not False:
        errors.append("v2.2 preflight handoff stage must not allow repairs yet")
    if next_stage.get("external_memory_lift_claim_allowed") is not False:
        errors.append("v2.2 preflight handoff stage must not allow external memory-lift claim")

    if v20.get("aggregate_classification") != "blocked_external_candidate_acquisition_failure":
        errors.append("v2.0 pilot result must remain blocked acquisition")
    if v20.get("scoreable_episode_count") != 0:
        errors.append("v2.0 scoreable external/fork episode count must remain 0")
    if v20.get("external_fork_memory_lift_demonstrated") is not False:
        errors.append("v2.0 must not demonstrate external/fork memory lift")
    if v19.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 limited user-owned result must remain preserved")
    if v19.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v1.9 must not demonstrate organic external memory lift")
    if v18.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 limited seeded result must remain preserved")
    if episode_003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 negative simple-task result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper quarantine must remain 0 deterministic-replay-ready episodes")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(
        require_text(
            PLAN_MD_PATH,
            [
                "v2.0 blocked at candidate acquisition.",
                "That result is not negative capability evidence",
                "Naive public repo scanning is not enough",
                "Candidate readiness is scored from 0 to 100.",
                "Candidates below 75 should not proceed to v2.2 execution.",
                "Candidate acquisition success is not repair success.",
                "Candidate pool creation is not external memory lift.",
                "External memory lift remains undemonstrated",
                "Self-maintaining software remains undemonstrated",
            ],
        )
    )
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v2.1 External Candidate Acquisition Harness Plan",
                "v2.0 blocked at candidate acquisition.",
                "This is not negative capability evidence.",
                "v2.1 designs systematic preflight candidate mining.",
                "External memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
            ],
        )
    )

    if errors:
        print("v2.1 external candidate acquisition harness plan audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.1 external candidate acquisition harness plan audit: PASS")
    print("v2.0 blocked acquisition preserved: true")
    print("external memory lift demonstrated: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
