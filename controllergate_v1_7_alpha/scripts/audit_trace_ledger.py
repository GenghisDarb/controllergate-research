#!/usr/bin/env python3
"""Audit the v1.7-alpha trace ledger for basic leakage and custody issues."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"

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


def audit_episode(episode: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    episode_id = episode.get("episode_id", "UNKNOWN")

    if episode.get("source_type") == "controlled_benchmark":
        findings.append(f"{episode_id}: controlled benchmark episode cannot be scored as real trace")

    available = set(episode.get("available_at_decision_time") or [])
    prohibited = set(episode.get("prohibited_future_fields") or [])
    overlap = available & prohibited
    if overlap:
        findings.append(f"{episode_id}: future leakage overlap: {sorted(overlap)}")

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

    return findings


def main() -> int:
    episodes, parse_errors = load_episodes()
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

    findings: list[str] = []
    for episode in episodes:
        findings.extend(audit_episode(episode))

    if findings:
        print("trace audit: FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("trace audit: PASS")
    print(f"episodes: {len(episodes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
