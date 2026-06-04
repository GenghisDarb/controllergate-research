#!/usr/bin/env python3
"""Audit the v1.7-alpha limited pilot scoring output."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"
CLASSIFICATION_PATH = ROOT / "traces" / "audits" / "episode_review_classification.json"
PILOT_REVIEW_PATH = ROOT / "traces" / "audits" / "pilot_eligibility_review.json"
SCORING_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"

REQUIRED_FINAL_STATUS = (
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


def main() -> int:
    ledger, ledger_errors = load_jsonl(LEDGER_PATH)
    classification, classification_errors = load_json(CLASSIFICATION_PATH)
    pilot_review, pilot_errors = load_json(PILOT_REVIEW_PATH)
    scoring, scoring_errors = load_json(SCORING_PATH)
    errors = ledger_errors + classification_errors + pilot_errors + scoring_errors

    ledger_by_id = {row.get("episode_id"): row for row in ledger}
    classification_rows = classification.get("episodes")
    if not isinstance(classification_rows, list):
        errors.append("classification episodes must be a list")
        classification_rows = []
    category_by_id = {
        row.get("episode_id"): row.get("category")
        for row in classification_rows
        if isinstance(row, dict)
    }

    pilot_rows = pilot_review.get("episodes")
    if not isinstance(pilot_rows, list):
        errors.append("pilot review episodes must be a list")
        pilot_rows = []
    pilot_eligible_ids = {
        row.get("episode_id")
        for row in pilot_rows
        if isinstance(row, dict) and row.get("pilot_eligible") is True
    }

    included_ids = set(scoring.get("included_episode_ids") or [])
    if included_ids != pilot_eligible_ids:
        errors.append(
            "included scoring episodes must match pilot-eligible episodes: "
            f"missing={sorted(pilot_eligible_ids - included_ids)}, extra={sorted(included_ids - pilot_eligible_ids)}"
        )
    if scoring.get("eligible_episode_count") != len(included_ids):
        errors.append(
            f"eligible_episode_count expected {len(included_ids)}, got {scoring.get('eligible_episode_count')!r}"
        )
    if scoring.get("scoring_mode") != "limited_pilot_only":
        errors.append("scoring_mode must be limited_pilot_only")
    if scoring.get("full_scoring_allowed") is not False:
        errors.append("full_scoring_allowed must be false")
    if scoring.get("final_status_wording") != REQUIRED_FINAL_STATUS:
        errors.append("final_status_wording does not match required wording")

    for episode_id in included_ids:
        if category_by_id.get(episode_id) != "external_real_repo_episode":
            errors.append(f"{episode_id}: included episode is not external_real_repo_episode")
        if episode_id not in ledger_by_id:
            errors.append(f"{episode_id}: included episode missing from ledger")

    excluded_counts = scoring.get("excluded_episode_count_by_category")
    if not isinstance(excluded_counts, dict):
        errors.append("excluded_episode_count_by_category must be an object")
        excluded_counts = {}
    expected_excluded = {
        "controlled_benchmark_evidence": 8,
        "correction_review_episode": 2,
    }
    for category, expected in expected_excluded.items():
        if excluded_counts.get(category) != expected:
            errors.append(f"excluded {category} expected {expected}, got {excluded_counts.get(category)!r}")

    breakdown = scoring.get("pass_fail_warning_breakdown")
    if not isinstance(breakdown, dict):
        errors.append("pass_fail_warning_breakdown must be an object")
        breakdown = {}
    expected_breakdown = {
        "passed": 2,
        "failed": 5,
        "warning_only": 1,
        "review_required": 2,
    }
    for field, expected in expected_breakdown.items():
        if breakdown.get(field) != expected:
            errors.append(f"pass_fail_warning_breakdown.{field} expected {expected}, got {breakdown.get(field)!r}")

    episode_decisions = scoring.get("episode_level_decisions")
    if not isinstance(episode_decisions, list):
        errors.append("episode_level_decisions must be a list")
        episode_decisions = []
    if len(episode_decisions) != len(included_ids):
        errors.append(
            f"episode_level_decisions expected {len(included_ids)} rows, got {len(episode_decisions)}"
        )

    scope = scoring.get("required_scope_enforced")
    if not isinstance(scope, dict):
        errors.append("required_scope_enforced must be an object")
    else:
        for field in [
            "only_external_real_repo_episode_entries_used",
            "correction_review_episode_entries_excluded",
            "controlled_benchmark_evidence_entries_excluded",
            "failed_warning_ambiguous_closed_unmerged_episodes_preserved",
            "decision_time_evidence_separation_preserved",
            "future_leakage_checks_preserved",
        ]:
            if scope.get(field) is not True:
                errors.append(f"required_scope_enforced.{field} must be true")

    for field in [
        "discovered_memory_result",
        "no_memory_baseline_result",
        "predefined_memory_baseline_result",
        "poisoned_memory_baseline_result",
    ]:
        value = scoring.get(field)
        if not isinstance(value, dict) or value.get("status") != "UNAVAILABLE":
            errors.append(f"{field}.status must be UNAVAILABLE")

    if errors:
        print("limited pilot scoring audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("limited pilot scoring audit: PASS")
    print(f"eligible episodes: {len(included_ids)}")
    print("scoring mode: limited_pilot_only")
    print("full scoring allowed: false")
    print("overall result: COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
