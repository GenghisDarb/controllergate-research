#!/usr/bin/env python3
"""Validate the v1.7-beta normalized ledger."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"
PENDING_DIR = ROOT / "episodes_pending"
LIMITED_SCORING_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
EXPECTED_NORMALIZED_EPISODES = 11
REQUIRED_BUNDLE_FILES = {
    "ci_log.txt",
    "failing_command.txt",
    "patch_diff.diff",
    "agent_trace.md",
    "files_read.txt",
    "files_written.txt",
    "artifact_manifest.txt",
    "outcome.md",
}
REQUIRED_LEDGER_FIELDS = {
    "episode_id",
    "source_episode_folder",
    "source_repo",
    "source_type",
    "category",
    "outcome_type",
    "verified_result",
    "evidence_status",
    "normalized_status",
    "scoring_allowed_for_v1_7_beta_second_repo_claim",
    "controllergate_scoring_run",
    "beta_scoring_run",
    "decision_time_evidence_available",
    "outcome_only_evidence",
    "unavailable_reasons",
}


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.exists():
        return records, [f"missing beta ledger: {path}"]

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


def main() -> int:
    records, errors = load_jsonl(LEDGER_PATH)
    seen_ids: set[str] = set()
    seen_folders: set[str] = set()

    if len(records) != EXPECTED_NORMALIZED_EPISODES:
        errors.append(f"expected {EXPECTED_NORMALIZED_EPISODES} beta normalized episodes, found {len(records)}")

    for index, record in enumerate(records, start=1):
        episode_id = str(record.get("episode_id") or f"line {index}")
        missing_fields = sorted(field for field in REQUIRED_LEDGER_FIELDS if field not in record)
        if missing_fields:
            errors.append(f"{episode_id}: missing fields {missing_fields}")

        if record.get("episode_id") in seen_ids:
            errors.append(f"{episode_id}: duplicate episode_id")
        seen_ids.add(str(record.get("episode_id")))

        folder = record.get("source_episode_folder")
        if not isinstance(folder, str) or not folder:
            errors.append(f"{episode_id}: missing source_episode_folder")
            continue
        if folder in seen_folders:
            errors.append(f"{episode_id}: duplicate source_episode_folder {folder}")
        seen_folders.add(folder)

        bundle_dir = PENDING_DIR / folder
        if not bundle_dir.exists():
            errors.append(f"{episode_id}: source bundle missing: {bundle_dir}")
        else:
            files = {path.name for path in bundle_dir.iterdir() if path.is_file()}
            missing_bundle_files = sorted(REQUIRED_BUNDLE_FILES - files)
            if missing_bundle_files:
                errors.append(f"{episode_id}: source bundle missing files {missing_bundle_files}")

        if record.get("source_repo") != "TatMapper":
            errors.append(f"{episode_id}: source_repo must be TatMapper")
        if record.get("source_type") != "external_real_repo":
            errors.append(f"{episode_id}: source_type must be external_real_repo")
        if record.get("category") != "external_real_repo_episode":
            errors.append(f"{episode_id}: category must be external_real_repo_episode")
        if record.get("verified_result") != "review_required":
            errors.append(f"{episode_id}: verified_result must remain review_required")
        if record.get("normalized_status") != "review_required":
            errors.append(f"{episode_id}: normalized_status must remain review_required")
        if record.get("scoring_allowed_for_v1_7_beta_second_repo_claim") != "review_required":
            errors.append(f"{episode_id}: beta scoring permission must be review_required")
        if record.get("controllergate_scoring_run") is not False:
            errors.append(f"{episode_id}: controllergate_scoring_run must be false")
        if record.get("beta_scoring_run") is not False:
            errors.append(f"{episode_id}: beta_scoring_run must be false")

        for list_field in ["decision_time_evidence_available", "outcome_only_evidence", "unavailable_reasons"]:
            value = record.get(list_field)
            if not isinstance(value, list) or not value:
                errors.append(f"{episode_id}: {list_field} must be a non-empty list")

    if errors:
        print("v1.7-beta ledger validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.7-beta ledger validation: PASS")
    print(f"normalized episodes: {len(records)}")
    print(f"external_real_repo_episode: {len(records)}")
    print("verified_result: review_required")
    if LIMITED_SCORING_PATH.exists():
        print("scoring: LIMITED_PILOT_RUN")
    else:
        print("scoring: NOT RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
