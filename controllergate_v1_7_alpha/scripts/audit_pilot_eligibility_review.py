#!/usr/bin/env python3
"""Audit the v1.7-alpha limited pilot eligibility review."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"
REVIEW_PATH = ROOT / "traces" / "audits" / "pilot_eligibility_review.json"
CLASSIFICATION_PATH = ROOT / "traces" / "audits" / "episode_review_classification.json"
REQUIRED_DIVERSITY = {
    "malformed artifact failure",
    "successful rerun / positive signal",
    "dependency or version assertion failure",
    "closed unmerged episode",
    "notebook/kernel failure",
    "workflow/validation failure",
    "repair episode",
    "warning-only or guardrail episode",
    "LaTeX/workflow repair",
    "README/guard failure",
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
    review, review_errors = load_json(REVIEW_PATH)
    classification, classification_errors = load_json(CLASSIFICATION_PATH)
    errors = ledger_errors + review_errors + classification_errors

    external = [
        row
        for row in ledger
        if row.get("category") == "external_real_repo_episode" or row.get("source_type") == "real_repo"
    ]
    external_ids = {row.get("episode_id") for row in external}

    review_episodes = review.get("episodes")
    if not isinstance(review_episodes, list):
        errors.append("pilot review must contain an episodes list")
        review_episodes = []

    review_ids = {episode.get("episode_id") for episode in review_episodes if isinstance(episode, dict)}
    if review_ids != external_ids:
        errors.append(
            "pilot review episode set does not match external ledger episodes: "
            f"missing={sorted(external_ids - review_ids)}, extra={sorted(review_ids - external_ids)}"
        )

    eligible_ids = {
        episode.get("episode_id")
        for episode in review_episodes
        if isinstance(episode, dict) and episode.get("pilot_eligible") is True
    }
    if not eligible_ids <= external_ids:
        errors.append(f"pilot eligible episodes must be external only: {sorted(eligible_ids - external_ids)}")

    if review.get("normalized_episode_count") != len(ledger):
        errors.append(
            f"normalized_episode_count expected {len(ledger)}, got {review.get('normalized_episode_count')!r}"
        )
    if review.get("external_real_repo_episode_count") != len(external):
        errors.append(
            "external_real_repo_episode_count expected "
            f"{len(external)}, got {review.get('external_real_repo_episode_count')!r}"
        )
    if review.get("eligible_external_episode_count") != len(eligible_ids):
        errors.append(
            "eligible_external_episode_count expected "
            f"{len(eligible_ids)}, got {review.get('eligible_external_episode_count')!r}"
        )
    if review.get("scoring_allowed") != "limited_pilot_only":
        errors.append("scoring_allowed must be limited_pilot_only for this review")
    if review.get("scoring_mode") != "limited_pilot_only":
        errors.append("scoring_mode must be limited_pilot_only")
    if review.get("full_scoring_allowed") is not False:
        errors.append("full_scoring_allowed must be false")
    if review.get("controllergate_scoring_run") is not False:
        errors.append("controllergate_scoring_run must be false")

    constraints = review.get("constraints")
    if not isinstance(constraints, dict):
        errors.append("constraints must be an object")
    else:
        for field in [
            "only_external_real_repo_episode_entries_may_be_used",
            "controlled_benchmark_evidence_excluded",
            "correction_review_episode_excluded",
            "pilot_must_be_reported_as_limited_and_exploratory",
            "no_self_maintaining_software_claim",
            "no_broad_external_generalization_claim",
            "failed_and_ambiguous_episodes_must_remain_included",
            "full_scoring_requires_separate_explicit_approval",
        ]:
            if constraints.get(field) is not True:
                errors.append(f"constraints.{field} must be true")

    evidence_checks = review.get("evidence_checks")
    if not isinstance(evidence_checks, dict):
        errors.append("evidence_checks must be an object")
    else:
        for field in [
            "decision_time_evidence_separated_from_outcome_only_evidence",
            "github_actions_rerun_unavailability_documented_where_applicable",
            "local_rerun_commands_preserved_where_available",
            "local_rerun_outputs_preserved_where_available",
            "controllergate_scoring_not_run",
        ]:
            if evidence_checks.get(field) is not True:
                errors.append(f"evidence_checks.{field} must be true")

    diversity = review.get("diversity_checks")
    if not isinstance(diversity, list):
        errors.append("diversity_checks must be a list")
        diversity = []
    covered_diversity = {
        item.get("category")
        for item in diversity
        if isinstance(item, dict) and item.get("covered") is True
    }
    missing_diversity = REQUIRED_DIVERSITY - covered_diversity
    if missing_diversity:
        errors.append(f"missing diversity coverage: {sorted(missing_diversity)}")

    summary = classification.get("summary")
    if not isinstance(summary, dict):
        errors.append("classification summary missing")
    else:
        if summary.get("scoring_mode") != "limited_pilot_only":
            errors.append("classification summary scoring_mode must be limited_pilot_only")
        if summary.get("full_scoring_allowed") is not False:
            errors.append("classification summary full_scoring_allowed must be false")
        if summary.get("scoring_eligibility_count_for_v1_7_alpha_real_repo_claim") != len(eligible_ids):
            errors.append(
                "classification summary scoring eligibility count must match limited pilot eligible episodes"
            )

    if errors:
        print("pilot eligibility review: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("pilot eligibility review: PASS")
    print(f"normalized episodes: {len(ledger)}")
    print(f"external real repo episodes: {len(external)}")
    print(f"eligible external episodes: {len(eligible_ids)}")
    print("scoring mode: limited_pilot_only")
    print("full scoring allowed: false")
    print("ControllerGate scoring: NOT RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
