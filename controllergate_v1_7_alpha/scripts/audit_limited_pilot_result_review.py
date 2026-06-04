#!/usr/bin/env python3
"""Audit the v1.7-alpha limited pilot result review."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCORING_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
REVIEW_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_result_review.json"
TECHNICAL_REPORT_PATH = ROOT / "reports" / "limited_pilot_scoring" / "v1_7_alpha_limited_pilot_result_review.md"
SUMMARY_PATH = ROOT / "reports" / "limited_pilot_scoring" / "README.md"

REQUIRED_STATUS = (
    "ControllerGate v1.7-alpha limited pilot scoring was run on 10 normalized "
    "TORUS-Theory external real repo episodes. This is exploratory pilot evidence "
    "only, not proof of self-maintaining software."
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

    expected_counts = {
        "eligible_external_episodes": scoring.get("eligible_episode_count"),
        "passed": (scoring.get("pass_fail_warning_breakdown") or {}).get("passed"),
        "failed": (scoring.get("pass_fail_warning_breakdown") or {}).get("failed"),
        "warning_only": (scoring.get("pass_fail_warning_breakdown") or {}).get("warning_only"),
        "review_required": (scoring.get("pass_fail_warning_breakdown") or {}).get("review_required"),
        "closed_unmerged": scoring.get("closed_unmerged_episode_count"),
        "controlled_benchmark_excluded": (scoring.get("excluded_episode_count_by_category") or {}).get(
            "controlled_benchmark_evidence"
        ),
        "correction_review_excluded": (scoring.get("excluded_episode_count_by_category") or {}).get(
            "correction_review_episode"
        ),
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
    if scoring.get("final_status_wording") != REQUIRED_STATUS:
        errors.append("scoring final_status_wording changed or is missing")

    non_claims = set(review.get("result_not_accepted_as") or [])
    for required in [
        "proof of self-maintaining software",
        "full v1.7-alpha scoring pass",
        "broad external generalization",
        "real-repo memory lift demonstration",
    ]:
        if required not in non_claims:
            errors.append(f"result_not_accepted_as missing {required!r}")

    memory = review.get("memory_baseline_review")
    if not isinstance(memory, dict):
        errors.append("memory_baseline_review must be an object")
        memory = {}
    for field in ["discovered_memory", "no_memory", "predefined_memory", "poisoned_memory"]:
        if memory.get(field) != "UNAVAILABLE":
            errors.append(f"memory_baseline_review.{field} must be UNAVAILABLE")

    checks = review.get("review_checks")
    if not isinstance(checks, dict):
        errors.append("review_checks must be an object")
        checks = {}
    for field in ["scope_gate", "exclusion_gate", "caveat_preservation", "decision_outcome_separation", "non_claim_boundary"]:
        if checks.get(field) != "PASS":
            errors.append(f"review_checks.{field} must be PASS")
    if checks.get("future_leakage_guard") != "PASS_WITH_REVIEW_REQUIRED_CAVEATS":
        errors.append("review_checks.future_leakage_guard must be PASS_WITH_REVIEW_REQUIRED_CAVEATS")

    if review.get("recommended_next_step") != "v1.7-beta second-repo external evidence collection":
        errors.append("recommended_next_step must point to v1.7-beta second-repo evidence collection")

    errors.extend(
        require_text(
            TECHNICAL_REPORT_PATH,
            [
                REQUIRED_STATUS,
                "Result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`",
                "The pilot cannot measure ControllerGate memory lift.",
                "Do not claim proof of self-maintaining software.",
                "Move next to v1.7-beta second-repo external evidence collection.",
            ],
        )
    )
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                REQUIRED_STATUS,
                "Status: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`",
                "Full scoring allowed: `false`",
                "Start v1.7-beta second-repo evidence collection",
            ],
        )
    )

    if errors:
        print("limited pilot result review audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("limited pilot result review audit: PASS")
    print("accepted result: COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS")
    print("recommendation: v1.7-beta second-repo external evidence collection")
    print("self-maintaining claim: NOT ALLOWED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
