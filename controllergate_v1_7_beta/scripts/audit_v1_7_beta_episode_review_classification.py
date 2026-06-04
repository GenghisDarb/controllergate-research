#!/usr/bin/env python3
"""Audit v1.7-beta episode review classifications."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"
CLASSIFICATION_PATH = ROOT / "traces" / "audits" / "beta_episode_review_classification.json"
ELIGIBILITY_REVIEW_PATH = ROOT / "traces" / "audits" / "v1_7_beta_second_repo_eligibility_review.json"


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


def load_optional_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, []
    data, errors = load_json(path)
    if errors:
        return None, errors
    return data, []


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
            errors.append(f"line {line_no}: expected object")
            continue
        records.append(record)
    return records, errors


def main() -> int:
    ledger, ledger_errors = load_jsonl(LEDGER_PATH)
    classification, classification_errors = load_json(CLASSIFICATION_PATH)
    eligibility_review, eligibility_errors = load_optional_json(ELIGIBILITY_REVIEW_PATH)
    errors = ledger_errors + classification_errors + eligibility_errors

    episodes = classification.get("episodes")
    if not isinstance(episodes, list):
        errors.append("classification must contain an episodes list")
        episodes = []

    by_folder: dict[str, dict[str, Any]] = {}
    for idx, episode in enumerate(episodes, start=1):
        if not isinstance(episode, dict):
            errors.append(f"classification episode {idx}: expected object")
            continue
        folder = episode.get("source_episode_folder")
        if not isinstance(folder, str) or not folder:
            errors.append(f"classification episode {idx}: missing source_episode_folder")
            continue
        if folder in by_folder:
            errors.append(f"duplicate classification folder: {folder}")
        by_folder[folder] = episode

    external_count = 0
    for record in ledger:
        episode_id = record.get("episode_id")
        folder = record.get("source_episode_folder")
        if not isinstance(folder, str):
            errors.append(f"{episode_id}: missing source_episode_folder")
            continue
        review = by_folder.get(folder)
        if review is None:
            errors.append(f"{episode_id}: missing classification for {folder}")
            continue
        if review.get("episode_id") != episode_id:
            errors.append(f"{episode_id}: classification episode_id mismatch {review.get('episode_id')!r}")
        if review.get("category") != "external_real_repo_episode":
            errors.append(f"{episode_id}: classification category must be external_real_repo_episode")
        if review.get("source_repo") != "TatMapper":
            errors.append(f"{episode_id}: classification source_repo must be TatMapper")
        if review.get("verified_result") != "review_required":
            errors.append(f"{episode_id}: classification verified_result must be review_required")
        if review.get("scoring_allowed_for_v1_7_beta_second_repo_claim") != "review_required":
            errors.append(f"{episode_id}: classification scoring permission must be review_required")
        external_count += 1

    extra = sorted(set(by_folder) - {str(record.get("source_episode_folder")) for record in ledger})
    for folder in extra:
        errors.append(f"classification has no matching normalized episode: {folder}")

    summary = classification.get("summary")
    if not isinstance(summary, dict):
        errors.append("classification must contain summary object")
    else:
        expected_scoring_mode = "blocked_pending_beta_eligibility_review"
        expected_second_repo_review_run = False
        if eligibility_review is not None:
            expected_scoring_mode = str(eligibility_review.get("scoring_mode"))
            expected_second_repo_review_run = True
            if eligibility_review.get("scoring_allowed") is not False:
                errors.append("eligibility review scoring_allowed must remain false for beta classification audit")
            if eligibility_review.get("beta_scoring_run") is not False:
                errors.append("eligibility review beta_scoring_run must remain false")

        expected = {
            "pending_bundle_count": 6,
            "normalized_episode_count": len(ledger),
            "external_real_repo_episode": external_count,
            "pending_incomplete": 0,
            "excluded_from_scoring": 0,
            "scoring_eligibility_count_for_v1_7_beta_second_repo_claim": 0,
            "scoring_allowed_for_v1_7_beta_second_repo_claim": False,
            "scoring_mode": expected_scoring_mode,
            "controllergate_scoring_run": False,
            "beta_scoring_run": False,
            "full_scoring_allowed": False,
            "second_repo_eligibility_review_run": expected_second_repo_review_run,
            "normalization_status": "REVIEW_NORMALIZED",
        }
        for key, expected_value in expected.items():
            if summary.get(key) != expected_value:
                errors.append(f"summary.{key} expected {expected_value!r}, got {summary.get(key)!r}")

    if errors:
        print("v1.7-beta episode review classification: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.7-beta episode review classification: PASS")
    print(f"normalized episodes: {len(ledger)}")
    print(f"external_real_repo_episode: {external_count}")
    print("scoring eligibility count for second repo claim: 0")
    scoring_mode = "blocked_pending_beta_eligibility_review"
    if eligibility_review is not None:
        scoring_mode = str(eligibility_review.get("scoring_mode"))
    print(f"scoring mode: {scoring_mode}")
    print("scoring allowed: false")
    print("scoring: NOT RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
