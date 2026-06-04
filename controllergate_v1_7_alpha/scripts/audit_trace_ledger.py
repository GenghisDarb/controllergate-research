#!/usr/bin/env python3
"""Audit the v1.7-alpha trace ledger for basic leakage and custody issues."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"
LIMITED_SCORING_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"

FORBIDDEN_MEMORY_KEY_TERMS = {
    "final_success",
    "hidden_pass",
    "hidden_result",
    "downstream_result",
    "correct_action",
    "future_correction",
    "oracle",
    "benchmark_family",
    "attack_class",
}


def load_episodes() -> tuple[list[dict[str, Any]], list[str]]:
    episodes: list[dict[str, Any]] = []
    errors: list[str] = []
    if not LEDGER_PATH.exists():
        return episodes, [f"missing ledger: {LEDGER_PATH}"]
    for line_no, raw in enumerate(LEDGER_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            errors.append(f"line {line_no}: blank line")
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc.msg}")
            continue
        if isinstance(item, dict):
            episodes.append(item)
        else:
            errors.append(f"line {line_no}: episode must be an object")
    return episodes, errors


def limited_scoring_run() -> bool:
    if not LIMITED_SCORING_PATH.exists():
        return False
    try:
        data = json.loads(LIMITED_SCORING_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return (
        isinstance(data, dict)
        and data.get("scoring_mode") == "limited_pilot_only"
        and data.get("full_scoring_allowed") is False
    )


def audit_episode(episode: dict[str, Any]) -> tuple[list[str], list[str]]:
    findings: list[str] = []
    review: list[str] = []
    episode_id = episode.get("episode_id", "UNKNOWN")
    source_type = episode.get("source_type")

    if source_type == "controlled_benchmark":
        review.append(f"{episode_id}: controlled benchmark evidence; review before treating as real-trace scoring input")
    if source_type == "real_repo":
        review.append(f"{episode_id}: external real repo rerun evidence; review before scoring eligibility")

    available = set(episode.get("available_at_decision_time") or [])
    prohibited = set(episode.get("prohibited_future_fields") or [])
    overlap = available & prohibited
    if overlap:
        findings.append(f"{episode_id}: future leakage overlap: {sorted(overlap)}")

    decision_time = set(episode.get("decision_time_evidence_available") or [])
    outcome_only = set(episode.get("outcome_only_evidence") or [])
    decision_outcome_overlap = decision_time & outcome_only
    if decision_outcome_overlap:
        findings.append(f"{episode_id}: decision-time/outcome-only overlap: {sorted(decision_outcome_overlap)}")

    memory_keys = episode.get("memory_keys") or []
    for key in memory_keys:
        normalized = str(key).lower()
        for term in FORBIDDEN_MEMORY_KEY_TERMS:
            if term in normalized:
                findings.append(f"{episode_id}: forbidden memory key term '{term}' in '{key}'")

    if episode.get("evidence_status") == "complete":
        required_paths = ["failure_log", "patch_diff", "agent_trace"]
        for field in required_paths:
            if episode.get(field) in (None, "", "UNAVAILABLE"):
                findings.append(f"{episode_id}: evidence marked complete but '{field}' is missing")

    if episode.get("normalized_status") == "review_required":
        review.append(f"{episode_id}: normalized_status is review_required")
    if episode.get("future_leakage_risk") == "review_required":
        review.append(f"{episode_id}: future_leakage_risk is review_required")
    if episode.get("runner_completed") is not True:
        if source_type == "real_repo":
            review.append(f"{episode_id}: runner_completed is not true; external evidence requires rerun-availability review")
        else:
            findings.append(f"{episode_id}: runner_completed is not true")
    if episode.get("analyzer_completed") is not True:
        if source_type == "real_repo":
            review.append(f"{episode_id}: analyzer_completed is not true; local rerun evidence requires review")
        else:
            findings.append(f"{episode_id}: analyzer_completed is not true")
    if episode.get("sha_manifest_verified") is not True:
        if source_type == "real_repo":
            review.append(f"{episode_id}: sha_manifest_verified is not true; external rerun bundle has no package SHA manifest")
        else:
            findings.append(f"{episode_id}: sha_manifest_verified is not true")
    if episode.get("sha_mismatch_count") not in (0, 0.0):
        if source_type == "real_repo" and episode.get("sha_mismatch_count") is None:
            review.append(f"{episode_id}: sha_mismatch_count is null because no SHA manifest was available")
        else:
            findings.append(f"{episode_id}: sha_mismatch_count is not zero")

    return findings, review


def main() -> int:
    episodes, parse_errors = load_episodes()
    limited_run = limited_scoring_run()
    if parse_errors:
        print("trace audit: FAIL")
        for error in parse_errors:
            print(f"- {error}")
        return 1

    if not episodes:
        print("trace audit: BLOCKED")
        print("episodes: 0")
        print("reason: real repository / real agent trace episodes are required before scoring")
        return 2

    if len(episodes) < 10:
        print("trace audit: BLOCKED")
        print(f"episodes: {len(episodes)}")
        print("reason: at least 10 normalized evidence episodes are required before scoring review")
        return 2

    findings: list[str] = []
    review_findings: list[str] = []
    for episode in episodes:
        episode_findings, episode_review = audit_episode(episode)
        findings.extend(episode_findings)
        review_findings.extend(episode_review)

    if findings:
        print("trace audit: FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1

    if review_findings:
        print("trace audit: REVIEW_REQUIRED")
        print(f"episodes: {len(episodes)}")
        for finding in review_findings:
            print(f"- {finding}")
        if limited_run:
            print("scoring: LIMITED_PILOT_RUN")
            print("full scoring: NOT RUN")
        else:
            print("scoring: NOT RUN")
        return 0

    print("trace audit: PASS")
    print(f"episodes: {len(episodes)}")
    if limited_run:
        print("scoring: LIMITED_PILOT_RUN")
        print("full scoring: NOT RUN")
    else:
        print("scoring: NOT RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
