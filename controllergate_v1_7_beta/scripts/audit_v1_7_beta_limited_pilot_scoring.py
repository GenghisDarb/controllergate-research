#!/usr/bin/env python3
"""Audit the v1.7-beta limited TatMapper scoring output."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"
ELIGIBILITY_REVIEW_PATH = ROOT / "traces" / "audits" / "v1_7_beta_second_repo_eligibility_review.json"
SCORING_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
REPORT_PATH = ROOT / "reports" / "limited_pilot_scoring" / "limited_pilot_scoring_report.md"
README_PATH = ROOT / "reports" / "limited_pilot_scoring" / "README.md"

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


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], [f"missing ledger: {path}"]
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            errors.append(f"ledger line {line_no}: blank line")
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"ledger line {line_no}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"ledger line {line_no}: expected object")
            continue
        rows.append(record)
    return rows, errors


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


def main() -> int:
    ledger, ledger_errors = load_jsonl(LEDGER_PATH)
    eligibility, eligibility_errors = load_json(ELIGIBILITY_REVIEW_PATH)
    scoring, scoring_errors = load_json(SCORING_PATH)
    errors = ledger_errors + eligibility_errors + scoring_errors

    external_ids = {
        row.get("episode_id")
        for row in ledger
        if row.get("category") == "external_real_repo_episode"
    }
    eligibility_rows = eligibility.get("episodes")
    if not isinstance(eligibility_rows, list):
        errors.append("eligibility review episodes must be a list")
        eligibility_rows = []
    eligible_ids = {
        row.get("episode_id")
        for row in eligibility_rows
        if isinstance(row, dict) and row.get("pilot_eligible") is True
    }
    included_ids = set(scoring.get("included_episode_ids") or [])

    if len(ledger) != 11:
        errors.append(f"expected 11 beta ledger episodes, found {len(ledger)}")
    if included_ids != external_ids:
        errors.append(
            "included scoring episodes must match beta external ledger episodes: "
            f"missing={sorted(external_ids - included_ids)}, extra={sorted(included_ids - external_ids)}"
        )
    if included_ids != eligible_ids:
        errors.append("included scoring episodes must match renewed eligibility review episodes")
    if scoring.get("eligible_episode_count") != 11:
        errors.append("eligible_episode_count must be 11")
    if scoring.get("scoring_mode") != "limited_pilot_only":
        errors.append("scoring_mode must be limited_pilot_only")
    if scoring.get("full_scoring_allowed") is not False:
        errors.append("full_scoring_allowed must be false")
    if scoring.get("beta_limited_pilot_scoring_run") is not True:
        errors.append("beta_limited_pilot_scoring_run must be true")
    if scoring.get("overall_limited_pilot_result") != "COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS":
        errors.append("overall_limited_pilot_result must preserve review-required caveats")
    if scoring.get("final_status_wording") != REQUIRED_FINAL_STATUS:
        errors.append("final_status_wording does not match required wording")

    breakdown = scoring.get("pass_fail_warning_breakdown")
    if not isinstance(breakdown, dict):
        errors.append("pass_fail_warning_breakdown must be an object")
        breakdown = {}
    expected_breakdown = {
        "passed": 0,
        "failed": 0,
        "warning_only": 0,
        "review_required": 11,
    }
    for field, expected in expected_breakdown.items():
        if breakdown.get(field) != expected:
            errors.append(f"pass_fail_warning_breakdown.{field} expected {expected}, got {breakdown.get(field)!r}")

    scope = scoring.get("required_scope_enforced")
    if not isinstance(scope, dict):
        errors.append("required_scope_enforced must be an object")
        scope = {}
    for field in [
        "only_v1_7_beta_tatmapper_external_real_repo_episode_entries_used",
        "v1_7_alpha_torus_episodes_excluded",
        "v1_6_controlled_benchmark_evidence_excluded",
        "weak_ambiguous_warning_unavailable_ci_and_review_required_episodes_preserved",
        "decision_time_evidence_separation_preserved",
        "future_leakage_checks_preserved",
        "full_scoring_disallowed",
    ]:
        if scope.get(field) is not True:
            errors.append(f"required_scope_enforced.{field} must be true")

    episode_decisions = scoring.get("episode_level_decisions")
    if not isinstance(episode_decisions, list) or len(episode_decisions) != 11:
        errors.append("episode_level_decisions must contain 11 rows")
    else:
        for row in episode_decisions:
            if not isinstance(row, dict):
                errors.append("episode_level_decisions rows must be objects")
                continue
            if row.get("verified_result") != "review_required":
                errors.append(f"{row.get('episode_id')}: verified_result must remain review_required")
            if row.get("included_in_limited_pilot") is not True:
                errors.append(f"{row.get('episode_id')}: included_in_limited_pilot must be true")

    for field in [
        "discovered_memory_result",
        "no_memory_baseline_result",
        "predefined_memory_baseline_result",
        "poisoned_memory_baseline_result",
    ]:
        value = scoring.get(field)
        if not isinstance(value, dict) or value.get("status") != "UNAVAILABLE":
            errors.append(f"{field}.status must be UNAVAILABLE")

    errors.extend(
        require_text(
            REPORT_PATH,
            [
                REQUIRED_FINAL_STATUS,
                "Overall limited pilot result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`",
                "This does not demonstrate real-repo memory lift.",
            ],
        )
    )
    errors.extend(
        require_text(
            README_PATH,
            [
                REQUIRED_FINAL_STATUS,
                "Status: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`",
                "ControllerGate full scoring: NOT RUN",
            ],
        )
    )

    if errors:
        print("v1.7-beta limited TatMapper scoring audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.7-beta limited TatMapper scoring audit: PASS")
    print("eligible beta external episodes: 11")
    print("scoring mode: limited_pilot_only")
    print("full scoring allowed: false")
    print("result: COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
