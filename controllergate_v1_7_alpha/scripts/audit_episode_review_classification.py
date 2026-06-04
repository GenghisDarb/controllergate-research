#!/usr/bin/env python3
"""Audit v1.7-alpha episode review classifications for scoring eligibility."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"
CLASSIFICATION_PATH = ROOT / "traces" / "audits" / "episode_review_classification.json"
PILOT_REVIEW_PATH = ROOT / "traces" / "audits" / "pilot_eligibility_review.json"
LIMITED_SCORING_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"

CATEGORIES = {
    "correction_review_episode",
    "controlled_benchmark_evidence",
    "external_real_repo_episode",
    "excluded_from_scoring",
}
REAL_REPO_SCORING_THRESHOLD = 10


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.exists():
        return records, [f"missing ledger: {path}"]

    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            errors.append(f"line {line_no}: blank line")
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"line {line_no}: record must be an object")
            continue
        records.append(record)
    return records, errors


def load_classification(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing classification file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"classification file invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return {}, ["classification file must be an object"]
    return data, []


def load_optional_pilot_review(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"pilot eligibility review invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return None, ["pilot eligibility review must be an object"]
    return data, []


def load_optional_limited_scoring(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"limited pilot scoring output invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return None, ["limited pilot scoring output must be an object"]
    return data, []


def main() -> int:
    ledger, ledger_errors = load_jsonl(LEDGER_PATH)
    classification, classification_errors = load_classification(CLASSIFICATION_PATH)
    pilot_review, pilot_review_errors = load_optional_pilot_review(PILOT_REVIEW_PATH)
    limited_scoring, limited_scoring_errors = load_optional_limited_scoring(LIMITED_SCORING_PATH)
    errors = ledger_errors + classification_errors + pilot_review_errors + limited_scoring_errors

    episodes = classification.get("episodes")
    if not isinstance(episodes, list):
        errors.append("classification file must contain an episodes list")
        episodes = []

    by_folder: dict[str, dict[str, Any]] = {}
    for idx, episode in enumerate(episodes, start=1):
        if not isinstance(episode, dict):
            errors.append(f"classification episode {idx}: must be an object")
            continue
        folder = episode.get("source_episode_folder")
        if not isinstance(folder, str) or not folder:
            errors.append(f"classification episode {idx}: missing source_episode_folder")
            continue
        if folder in by_folder:
            errors.append(f"classification duplicate source_episode_folder: {folder}")
        by_folder[folder] = episode

    counts = {category: 0 for category in CATEGORIES}
    row_scoring_eligible = 0
    ledger_folders: set[str] = set()
    external_episode_ids: set[str] = set()

    for record in ledger:
        folder = record.get("source_episode_folder")
        episode_id = record.get("episode_id", "UNKNOWN")
        if not isinstance(folder, str) or not folder:
            errors.append(f"{episode_id}: missing source_episode_folder")
            continue

        ledger_folders.add(folder)
        review = by_folder.get(folder)
        if review is None:
            errors.append(f"{episode_id}: missing review classification for {folder}")
            continue

        category = review.get("category")
        if category not in CATEGORIES:
            errors.append(f"{episode_id}: invalid review category {category!r}")
            continue

        counts[category] += 1
        if category == "external_real_repo_episode":
            external_episode_ids.add(str(episode_id))

        review_episode_id = review.get("episode_id")
        if review_episode_id != episode_id:
            errors.append(f"{episode_id}: classification episode_id mismatch {review_episode_id!r}")

        allowed = review.get("scoring_allowed_for_v1_7_alpha_real_repo_claim")
        if isinstance(allowed, bool):
            scoring_eligible_episode = allowed
        elif allowed in {"review_required", "pilot_review_required"}:
            scoring_eligible_episode = False
        else:
            errors.append(
                f"{episode_id}: scoring_allowed_for_v1_7_alpha_real_repo_claim must be boolean or review_required"
            )
            scoring_eligible_episode = False

        if scoring_eligible_episode and category != "external_real_repo_episode":
            errors.append(f"{episode_id}: only external_real_repo_episode may be scoring eligible")
        elif scoring_eligible_episode and category == "external_real_repo_episode":
            row_scoring_eligible += 1

    extra_folders = sorted(set(by_folder) - ledger_folders)
    for folder in extra_folders:
        errors.append(f"classification has no matching normalized episode: {folder}")

    limited_pilot_eligible = 0
    scoring_mode = "blocked"
    full_scoring_allowed = row_scoring_eligible >= REAL_REPO_SCORING_THRESHOLD

    if full_scoring_allowed:
        scoring_mode = "full"

    if pilot_review is not None:
        pilot_episodes = pilot_review.get("episodes")
        if not isinstance(pilot_episodes, list):
            errors.append("pilot eligibility review must contain an episodes list")
            pilot_episodes = []

        pilot_eligible_ids = {
            episode.get("episode_id")
            for episode in pilot_episodes
            if isinstance(episode, dict) and episode.get("pilot_eligible") is True
        }
        if not pilot_eligible_ids <= external_episode_ids:
            errors.append(
                "pilot eligibility review marks non-external episodes eligible: "
                f"{sorted(pilot_eligible_ids - external_episode_ids)}"
            )

        if pilot_review.get("scoring_allowed") == "limited_pilot_only":
            scoring_mode = "limited_pilot_only"
            full_scoring_allowed = False
            limited_pilot_eligible = len(pilot_eligible_ids)
        elif pilot_review.get("scoring_allowed") in {False, "false"}:
            scoring_mode = "blocked"
            full_scoring_allowed = False
            limited_pilot_eligible = 0
        else:
            errors.append("pilot eligibility review scoring_allowed must be false or limited_pilot_only")

        if pilot_review.get("full_scoring_allowed") is not False:
            errors.append("pilot eligibility review full_scoring_allowed must be false")
        if pilot_review.get("controllergate_scoring_run") is not False:
            errors.append("pilot eligibility review controllergate_scoring_run must be false")

    reported_scoring_eligible = limited_pilot_eligible if scoring_mode == "limited_pilot_only" else row_scoring_eligible
    limited_pilot_scoring_run = limited_scoring is not None

    if limited_scoring is not None:
        scoring_ids = set(limited_scoring.get("included_episode_ids") or [])
        if scoring_ids != {
            episode.get("episode_id")
            for episode in (pilot_review or {}).get("episodes", [])
            if isinstance(episode, dict) and episode.get("pilot_eligible") is True
        }:
            errors.append("limited pilot scoring included episodes must match pilot-eligible episodes")
        if limited_scoring.get("scoring_mode") != "limited_pilot_only":
            errors.append("limited pilot scoring mode must be limited_pilot_only")
        if limited_scoring.get("full_scoring_allowed") is not False:
            errors.append("limited pilot scoring full_scoring_allowed must be false")

    summary = classification.get("summary")
    if not isinstance(summary, dict):
        errors.append("classification file must contain a summary object")
    else:
        expected_summary = {
            "normalized_episode_count": len(ledger),
            "correction_review_episode": counts["correction_review_episode"],
            "controlled_benchmark_evidence": counts["controlled_benchmark_evidence"],
            "external_real_repo_episode": counts["external_real_repo_episode"],
            "excluded_from_scoring": counts["excluded_from_scoring"],
            "scoring_eligibility_count_for_v1_7_alpha_real_repo_claim": reported_scoring_eligible,
            "scoring_allowed_for_v1_7_alpha_real_repo_claim": full_scoring_allowed,
            "scoring_mode": scoring_mode,
            "full_scoring_allowed": full_scoring_allowed,
        }
        if scoring_mode == "limited_pilot_only":
            expected_summary["limited_pilot_eligible_external_episode_count"] = limited_pilot_eligible
            expected_summary["limited_pilot_scoring_run"] = limited_pilot_scoring_run
            expected_summary["full_scoring_run"] = False
        for field, expected in expected_summary.items():
            if summary.get(field) != expected:
                errors.append(f"summary.{field} expected {expected!r}, got {summary.get(field)!r}")

    if errors:
        print("episode review classification: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("episode review classification: PASS")
    print(f"normalized episodes: {len(ledger)}")
    print(f"correction_review_episode: {counts['correction_review_episode']}")
    print(f"controlled_benchmark_evidence: {counts['controlled_benchmark_evidence']}")
    print(f"external_real_repo_episode: {counts['external_real_repo_episode']}")
    print(f"excluded_from_scoring: {counts['excluded_from_scoring']}")
    print(f"scoring eligibility count for real repo pilot: {reported_scoring_eligible}")
    print(f"scoring mode: {scoring_mode}")
    print(f"full scoring allowed: {str(full_scoring_allowed).lower()}")
    print(f"scoring allowed: {str(full_scoring_allowed).lower()}")
    print(f"limited pilot scoring run: {str(limited_pilot_scoring_run).lower()}")
    print("full scoring run: false")
    if scoring_mode == "limited_pilot_only":
        print("reason: limited exploratory pilot eligibility approved; full scoring remains blocked")
    elif not full_scoring_allowed:
        print("reason: fewer than 10 scoring-eligible external real repo episodes")
    if limited_pilot_scoring_run:
        print("scoring: LIMITED_PILOT_RUN")
    else:
        print("scoring: NOT RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
