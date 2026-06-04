#!/usr/bin/env python3
"""Audit the v1.7-beta limited TatMapper pilot critic review package."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCORING_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
REVIEW_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_result_review.json"
PACKAGE_README_PATH = ROOT / "reports" / "critic_review_package" / "README.md"
CRITIC_REPORT_PATH = ROOT / "reports" / "critic_review_package" / "v1_7_beta_limited_pilot_critic_review.md"
SHAREABLE_SUMMARY_PATH = ROOT / "reports" / "critic_review_package" / "shareable_summary.md"
SCORING_REPORT_PATH = ROOT / "reports" / "limited_pilot_scoring" / "limited_pilot_scoring_report.md"

REQUIRED_FINAL_STATUS = (
    "ControllerGate v1.7-beta limited TatMapper scoring was run on 11 normalized "
    "TatMapper external real repo episodes. This is tiny second-repo exploratory "
    "evidence only, not proof of self-maintaining software."
)


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


def main() -> int:
    scoring, scoring_errors = load_json(SCORING_PATH)
    review, review_errors = load_json(REVIEW_PATH)
    errors = scoring_errors + review_errors

    breakdown = scoring.get("pass_fail_warning_breakdown") or {}
    leakage = scoring.get("future_leakage_checks") or {}
    drift = scoring.get("dependency_or_config_drift_detection_results") or {}
    artifact = scoring.get("generated_artifact_mismatch_detection_results") or {}
    stale = scoring.get("stale_read_or_false_completion_detection_results") or {}

    expected_counts = {
        "eligible_beta_external_episodes": scoring.get("eligible_episode_count"),
        "passed": breakdown.get("passed"),
        "failed": breakdown.get("failed"),
        "warning_only": breakdown.get("warning_only"),
        "review_required": breakdown.get("review_required"),
        "deterministic_pass_fail": scoring.get("deterministic_pass_fail_count"),
        "warning_or_review_required": scoring.get("warning_or_review_required_count"),
        "decision_time_outcome_overlap_episode_count": leakage.get("decision_time_outcome_overlap_episode_count"),
        "dependency_or_config_drift_true": drift.get("true"),
        "generated_artifact_mismatch_true": artifact.get("true"),
        "stale_read_or_false_completion_review_required": stale.get("review_required"),
    }

    counts = review.get("counts")
    if not isinstance(counts, dict):
        errors.append("review counts must be an object")
        counts = {}
    for field, expected in expected_counts.items():
        if counts.get(field) != expected:
            errors.append(f"counts.{field} expected {expected!r}, got {counts.get(field)!r}")

    if review.get("accepted_result") != scoring.get("overall_limited_pilot_result"):
        errors.append("accepted_result must match scoring overall_limited_pilot_result")
    if review.get("accepted_result") != "COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS":
        errors.append("accepted_result must preserve review-required caveats")
    if review.get("final_status_wording") != REQUIRED_FINAL_STATUS:
        errors.append("final_status_wording changed or is missing")
    if scoring.get("final_status_wording") != REQUIRED_FINAL_STATUS:
        errors.append("scoring final_status_wording changed or is missing")

    checks = review.get("review_checks")
    if not isinstance(checks, dict):
        errors.append("review_checks must be an object")
        checks = {}
    for field in [
        "scope_gate",
        "exclusion_gate",
        "limited_mode_gate",
        "decision_outcome_separation",
        "caveat_preservation",
        "non_claim_boundary",
    ]:
        if checks.get(field) != "PASS":
            errors.append(f"review_checks.{field} must be PASS")
    if checks.get("future_leakage_guard") != "PASS_WITH_REVIEW_REQUIRED_CAVEATS":
        errors.append("review_checks.future_leakage_guard must be PASS_WITH_REVIEW_REQUIRED_CAVEATS")
    if checks.get("memory_baseline_availability") != "UNAVAILABLE":
        errors.append("review_checks.memory_baseline_availability must be UNAVAILABLE")
    if checks.get("deterministic_performance_scoring") != "UNAVAILABLE":
        errors.append("review_checks.deterministic_performance_scoring must be UNAVAILABLE")

    fairness = review.get("gate_fairness_review")
    if not isinstance(fairness, dict):
        errors.append("gate_fairness_review must be an object")
        fairness = {}
    if fairness.get("eligibility_rules_were_fair_for_limited_pilot") is not True:
        errors.append("eligibility_rules_were_fair_for_limited_pilot must be true")
    if fairness.get("eligibility_rules_are_too_weak_for_full_scoring") is not True:
        errors.append("eligibility_rules_are_too_weak_for_full_scoring must be true")

    non_claims = set(review.get("result_not_accepted_as") or [])
    for required in [
        "proof of self-maintaining software",
        "full v1.7-beta scoring pass",
        "production readiness",
        "broad cross-repo generalization",
        "real-repo memory lift demonstration",
    ]:
        if required not in non_claims:
            errors.append(f"result_not_accepted_as missing {required!r}")

    episodes = review.get("episode_driver_summary")
    if not isinstance(episodes, list) or len(episodes) != 11:
        errors.append("episode_driver_summary must list all 11 beta episodes")

    if review.get("recommended_next_step") != "hold_full_scoring_and_strengthen_beta_evidence":
        errors.append("recommended_next_step must hold full scoring and strengthen beta evidence")

    errors.extend(
        require_text(
            CRITIC_REPORT_PATH,
            [
                REQUIRED_FINAL_STATUS,
                "Result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`",
                "decision_time_outcome_overlap_episode_count: 0",
                "Do not expand scoring yet.",
                "Real-repo memory-lift demonstration.",
            ],
        )
    )
    errors.extend(
        require_text(
            PACKAGE_README_PATH,
            [
                "Accepted result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`",
                REQUIRED_FINAL_STATUS,
                "Do not expand scoring yet.",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY_PATH,
            [
                REQUIRED_FINAL_STATUS,
                "`COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`",
                "decision_time_outcome_overlap_episode_count: 0",
                "Real-repo memory lift: not demonstrated.",
                "Do not expand scoring yet.",
            ],
        )
    )
    errors.extend(
        require_text(
            SCORING_REPORT_PATH,
            [
                "Overall limited pilot result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`",
                "decision-time/outcome-only overlap episodes=0",
                "This does not demonstrate real-repo memory lift.",
            ],
        )
    )

    if errors:
        print("v1.7-beta limited pilot critic review audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.7-beta limited pilot critic review audit: PASS")
    print("accepted result: COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS")
    print("decision-time/outcome overlap episodes: 0")
    print("recommendation: hold full scoring and strengthen beta evidence")
    print("self-maintaining claim: NOT ALLOWED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
