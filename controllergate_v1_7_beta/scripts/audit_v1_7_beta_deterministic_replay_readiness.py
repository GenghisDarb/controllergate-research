#!/usr/bin/env python3
"""Audit the v1.7-beta TatMapper deterministic replay readiness package."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_JSON_PATH = ROOT / "reports" / "evidence_strengthening" / "tatmapper_deterministic_replay_audit.json"
AUDIT_REPORT_PATH = ROOT / "reports" / "evidence_strengthening" / "tatmapper_deterministic_replay_audit.md"
SHAREABLE_SUMMARY_PATH = ROOT / "reports" / "critic_review_package" / "shareable_summary.md"
SCORING_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"

EXPECTED_CLASSIFICATION_COUNTS = {
    "deterministic_replay_ready": 0,
    "blocked_missing_ci_log": 5,
    "blocked_pr_head_unavailable": 1,
    "blocked_toolchain_gap": 2,
    "blocked_timeout": 1,
    "blocked_missing_agent_trace": 0,
    "review_required_insufficient_evidence": 2,
}

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


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


def main() -> int:
    audit, audit_errors = load_json(AUDIT_JSON_PATH)
    scoring, scoring_errors = load_json(SCORING_PATH)
    errors = audit_errors + scoring_errors

    if audit.get("limited_pilot_status") != "COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS":
        errors.append("limited_pilot_status must remain COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS")
    if audit.get("full_scoring_allowed") is not False:
        errors.append("full_scoring_allowed must be false")
    if audit.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("controllergate_full_scoring must be NOT_RUN")
    if audit.get("decision_time_outcome_overlap_episode_count") != 0:
        errors.append("decision_time_outcome_overlap_episode_count must remain 0")
    if audit.get("deterministic_replay_ready_count") != 0:
        errors.append("deterministic_replay_ready_count must be 0 for this pass")
    if audit.get("memory_baseline_instrumentation_available") is not False:
        errors.append("memory_baseline_instrumentation_available must be false")

    classification_counts = audit.get("classification_counts")
    if not isinstance(classification_counts, dict):
        errors.append("classification_counts must be an object")
        classification_counts = {}
    for field, expected in EXPECTED_CLASSIFICATION_COUNTS.items():
        if classification_counts.get(field) != expected:
            errors.append(f"classification_counts.{field} expected {expected!r}, got {classification_counts.get(field)!r}")

    github = audit.get("github_actions_lookup")
    if not isinstance(github, dict):
        errors.append("github_actions_lookup must be an object")
        github = {}
    if github.get("checked_commit_count") != 11:
        errors.append("github_actions_lookup.checked_commit_count must be 11")
    if github.get("workflow_runs_found_count") != 2:
        errors.append("github_actions_lookup.workflow_runs_found_count must be 2")
    runs = github.get("workflow_runs_found")
    if not isinstance(runs, list) or len(runs) != 2:
        errors.append("workflow_runs_found must list exactly 2 exposed runs")
    else:
        for run in runs:
            jobs = run.get("jobs")
            if not isinstance(jobs, list) or len(jobs) != 2:
                errors.append(f"{run.get('episode_id')}: expected 2 failed jobs")
                continue
            for job in jobs:
                if job.get("conclusion") != "failure":
                    errors.append(f"{run.get('episode_id')} job {job.get('job_id')}: conclusion must be failure")
                if job.get("decoded_log_fetch_status") != "unavailable_410":
                    errors.append(f"{run.get('episode_id')} job {job.get('job_id')}: log status must be unavailable_410")

    current = audit.get("current_head_strengthening_context")
    if not isinstance(current, dict):
        errors.append("current_head_strengthening_context must be an object")
        current = {}
    if current.get("current_head_sha") != "8f49190a6e9ae29c8c49301a7736e0f838dfd369":
        errors.append("current_head_sha must match the recorded scratch clone head")
    if current.get("not_pr_head_proof") is not True:
        errors.append("current-head strengthening must be marked not_pr_head_proof")

    episodes = audit.get("episodes")
    if not isinstance(episodes, list) or len(episodes) != 11:
        errors.append("episodes must list all 11 TatMapper episodes")
        episodes = []
    expected_ids = {f"beta_episode_{idx:03d}" for idx in range(1, 12)}
    actual_ids = {episode.get("episode_id") for episode in episodes if isinstance(episode, dict)}
    if actual_ids != expected_ids:
        errors.append(f"episode IDs mismatch: missing={sorted(expected_ids - actual_ids)}, extra={sorted(actual_ids - expected_ids)}")
    for episode in episodes:
        if not isinstance(episode, dict):
            continue
        if episode.get("deterministic_replay_ready") is not False:
            errors.append(f"{episode.get('episode_id')}: deterministic_replay_ready must be false")
        if episode.get("readiness_classification") not in EXPECTED_CLASSIFICATION_COUNTS:
            errors.append(f"{episode.get('episode_id')}: invalid readiness_classification")
        if not episode.get("decision_time_evidence"):
            errors.append(f"{episode.get('episode_id')}: decision_time_evidence must be populated")
        if not episode.get("outcome_only_evidence"):
            errors.append(f"{episode.get('episode_id')}: outcome_only_evidence must be populated")

    leakage = scoring.get("future_leakage_checks") or {}
    if leakage.get("decision_time_outcome_overlap_episode_count") != audit.get("decision_time_outcome_overlap_episode_count"):
        errors.append("audit leakage count must match limited scoring leakage count")
    if scoring.get("overall_limited_pilot_result") != audit.get("limited_pilot_status"):
        errors.append("audit limited pilot status must match scoring result")
    if scoring.get("full_scoring_allowed") is not False:
        errors.append("scoring full_scoring_allowed must remain false")

    errors.extend(
        require_text(
            AUDIT_REPORT_PATH,
            [
                "Deterministic replay ready | 0",
                "Flutter CI run `17986583215` found",
                "Flutter CI run `17984606083` found",
                "decoded logs return `410`",
                "Current-head SHA: `8f49190a6e9ae29c8c49301a7736e0f838dfd369`",
                "Full scoring: blocked",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY_PATH,
            [
                REQUIRED_FINAL_STATUS,
                "Deterministic replay-ready episodes: 0.",
                "PR #92 and PR #93 now have failed Flutter CI run/job metadata",
                "Do not expand scoring yet.",
            ],
        )
    )

    if errors:
        print("v1.7-beta deterministic replay readiness audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.7-beta deterministic replay readiness audit: PASS")
    print("deterministic replay-ready episodes: 0")
    print("workflow runs found: 2")
    print("full scoring allowed: false")
    print("ControllerGate full scoring: NOT RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
