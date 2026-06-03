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


def main() -> int:
    ledger, ledger_errors = load_jsonl(LEDGER_PATH)
    classification, classification_errors = load_classification(CLASSIFICATION_PATH)
    errors = ledger_errors + classification_errors

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
    scoring_eligible = 0
    ledger_folders: set[str] = set()

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

        review_episode_id = review.get("episode_id")
        if review_episode_id != episode_id:
            errors.append(f"{episode_id}: classification episode_id mismatch {review_episode_id!r}")

        allowed = review.get("scoring_allowed_for_v1_7_alpha_real_repo_claim")
        if not isinstance(allowed, bool):
            errors.append(f"{episode_id}: scoring_allowed_for_v1_7_alpha_real_repo_claim must be boolean")
        elif allowed and category != "external_real_repo_episode":
            errors.append(f"{episode_id}: only external_real_repo_episode may be scoring eligible")
        elif allowed and category == "external_real_repo_episode":
            scoring_eligible += 1

    extra_folders = sorted(set(by_folder) - ledger_folders)
    for folder in extra_folders:
        errors.append(f"classification has no matching normalized episode: {folder}")

    scoring_allowed = scoring_eligible >= REAL_REPO_SCORING_THRESHOLD
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
            "scoring_eligibility_count_for_v1_7_alpha_real_repo_claim": scoring_eligible,
            "scoring_allowed_for_v1_7_alpha_real_repo_claim": scoring_allowed,
        }
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
    print(f"scoring eligibility count for real repo pilot: {scoring_eligible}")
    print(f"scoring allowed: {str(scoring_allowed).lower()}")
    if not scoring_allowed:
        print("reason: fewer than 10 scoring-eligible external real repo episodes")
    print("scoring: NOT RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
