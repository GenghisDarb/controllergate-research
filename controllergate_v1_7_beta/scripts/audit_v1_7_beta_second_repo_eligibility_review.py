#!/usr/bin/env python3
"""Audit the v1.7-beta second-repo eligibility review."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parent
LEDGER_PATH = BETA_ROOT / "traces" / "normalized" / "episodes.jsonl"
CLASSIFICATION_PATH = BETA_ROOT / "traces" / "audits" / "beta_episode_review_classification.json"
REVIEW_PATH = BETA_ROOT / "traces" / "audits" / "v1_7_beta_second_repo_eligibility_review.json"
ALPHA_ROOT = REPO_ROOT / "controllergate_v1_7_alpha"

REQUIRED_DIVERSITY = {
    "Flutter availability or environment gap",
    "NDK/tooling review",
    "Windows checkout breakage",
    "Android scaffold / NDK / CMake setup",
    "SDK/v2 embedding alignment",
    "pubspec conflict-marker risk",
    "dependency/config drift",
    "build scaffold repair",
    "warning or guardrail case",
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
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"ledger line {line_no}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(row, dict):
            errors.append(f"ledger line {line_no}: expected object")
            continue
        rows.append(row)
    return rows, errors


def main() -> int:
    ledger, ledger_errors = load_jsonl(LEDGER_PATH)
    classification, classification_errors = load_json(CLASSIFICATION_PATH)
    review, review_errors = load_json(REVIEW_PATH)
    errors = ledger_errors + classification_errors + review_errors

    external = [row for row in ledger if row.get("category") == "external_real_repo_episode"]
    external_ids = {row.get("episode_id") for row in external}

    if len(ledger) != 6:
        errors.append(f"expected 6 beta normalized episodes, found {len(ledger)}")
    if len(external) != 6:
        errors.append(f"expected 6 beta external real repo episodes, found {len(external)}")

    review_episodes = review.get("episodes")
    if not isinstance(review_episodes, list):
        errors.append("review must contain an episodes list")
        review_episodes = []
    review_ids = {episode.get("episode_id") for episode in review_episodes if isinstance(episode, dict)}
    if review_ids != external_ids:
        errors.append(
            "review episode set must match beta external ledger episodes: "
            f"missing={sorted(external_ids - review_ids)}, extra={sorted(review_ids - external_ids)}"
        )

    eligible_ids = {
        episode.get("episode_id")
        for episode in review_episodes
        if isinstance(episode, dict) and episode.get("pilot_eligible") is True
    }
    if eligible_ids:
        errors.append(f"no beta episodes should be pilot eligible yet: {sorted(eligible_ids)}")

    if review.get("normalized_episode_count") != len(ledger):
        errors.append("review normalized_episode_count does not match ledger")
    if review.get("external_real_repo_episode_count") != len(external):
        errors.append("review external_real_repo_episode_count does not match ledger")
    if review.get("eligible_external_episode_count") != 0:
        errors.append("eligible_external_episode_count must be 0")
    if review.get("scoring_allowed") is not False:
        errors.append("scoring_allowed must be false")
    if review.get("scoring_mode") != "blocked_insufficient_second_repo_evidence":
        errors.append("scoring_mode must be blocked_insufficient_second_repo_evidence")
    if review.get("full_scoring_allowed") is not False:
        errors.append("full_scoring_allowed must be false")
    if review.get("controllergate_scoring_run") is not False:
        errors.append("controllergate_scoring_run must be false")
    if review.get("beta_scoring_run") is not False:
        errors.append("beta_scoring_run must be false")
    if review.get("alpha_reports_and_scoring_outputs_unchanged") is not True:
        errors.append("alpha_reports_and_scoring_outputs_unchanged must be true")

    constraints = review.get("constraints")
    if not isinstance(constraints, dict):
        errors.append("constraints must be an object")
    else:
        for field in [
            "only_v1_7_beta_tatmapper_external_real_repo_episode_entries_may_be_used",
            "v1_7_alpha_torus_episodes_excluded_from_beta_scoring",
            "v1_6_controlled_benchmark_evidence_excluded",
            "no_self_maintaining_software_claim",
            "no_broad_cross_repo_generalization_claim",
            "tiny_second_repo_exploratory_label_required_if_scoring_is_later_allowed",
            "ambiguous_or_weak_episodes_must_remain_visible",
            "full_scoring_disallowed",
        ]:
            if constraints.get(field) is not True:
                errors.append(f"constraints.{field} must be true")

    evidence_checks = review.get("evidence_checks")
    if not isinstance(evidence_checks, dict):
        errors.append("evidence_checks must be an object")
    else:
        for field in [
            "decision_time_evidence_separated_from_outcome_only_evidence",
            "missing_ci_logs_documented_where_applicable",
            "local_rerun_absence_documented_where_applicable",
            "weak_or_ambiguous_evidence_preserved",
            "controllergate_scoring_not_run",
            "beta_scoring_not_run",
            "alpha_reports_and_scoring_outputs_unchanged",
        ]:
            if evidence_checks.get(field) is not True:
                errors.append(f"evidence_checks.{field} must be true")

    diversity = review.get("diversity_checks")
    if not isinstance(diversity, list):
        errors.append("diversity_checks must be a list")
        diversity = []
    covered = {
        item.get("category")
        for item in diversity
        if isinstance(item, dict) and item.get("covered") is True
    }
    missing_diversity = REQUIRED_DIVERSITY - covered
    if missing_diversity:
        errors.append(f"missing diversity coverage: {sorted(missing_diversity)}")

    ambiguous = review.get("episodes_too_ambiguous_for_scoring")
    if set(ambiguous or []) != external_ids:
        errors.append("all six beta episodes must remain too ambiguous for scoring in this review")

    additional_needed = review.get("additional_tatmapper_evidence_needed")
    if not isinstance(additional_needed, list) or len(additional_needed) < 4:
        errors.append("additional_tatmapper_evidence_needed must list concrete next evidence needs")

    summary = classification.get("summary")
    if not isinstance(summary, dict):
        errors.append("classification summary missing")
    else:
        if summary.get("normalized_episode_count") != len(ledger):
            errors.append("classification normalized count does not match beta ledger")
        if summary.get("external_real_repo_episode") != len(external):
            errors.append("classification external episode count does not match beta ledger")
        if summary.get("scoring_eligibility_count_for_v1_7_beta_second_repo_claim") != 0:
            errors.append("classification beta scoring eligibility count must remain 0")
        if summary.get("beta_scoring_run") is not False:
            errors.append("classification beta_scoring_run must remain false")
        if summary.get("full_scoring_allowed") is not False:
            errors.append("classification full_scoring_allowed must remain false")

    required_alpha_files = [
        ALPHA_ROOT / "traces" / "audits" / "pilot_eligibility_review.json",
        ALPHA_ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json",
        ALPHA_ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_result_review.json",
    ]
    for path in required_alpha_files:
        if not path.exists():
            errors.append(f"required alpha audit artifact missing: {path}")

    if errors:
        print("v1.7-beta second-repo eligibility review: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.7-beta second-repo eligibility review: PASS")
    print(f"beta normalized episodes: {len(ledger)}")
    print(f"beta external real repo episodes: {len(external)}")
    print("beta scoring mode: blocked_insufficient_second_repo_evidence")
    print("beta scoring allowed: false")
    print("full scoring allowed: false")
    print("ControllerGate scoring: NOT RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
