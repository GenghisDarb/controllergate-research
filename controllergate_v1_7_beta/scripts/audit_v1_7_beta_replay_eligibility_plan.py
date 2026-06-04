#!/usr/bin/env python3
"""Audit the v1.7-beta replay eligibility pathway artifact."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_JSON_PATH = ROOT / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
PLAN_REPORT_PATH = ROOT / "outputs" / "v1_7_beta_replay_eligibility_plan.md"
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"
SCORING_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
READINESS_AUDIT_PATH = ROOT / "reports" / "evidence_strengthening" / "tatmapper_deterministic_replay_audit.json"
SHAREABLE_SUMMARY_PATH = ROOT / "reports" / "critic_review_package" / "shareable_summary.md"

CONTROLLED_BLOCKERS = {
    "missing_pr_head_sha",
    "missing_base_sha",
    "missing_changed_files_snapshot",
    "missing_failing_job_log",
    "missing_failure_signature",
    "missing_pre_repair_test_command",
    "missing_repair_patch",
    "missing_post_repair_test_command",
    "missing_outcome_evidence",
    "connector_410_log_unavailable",
    "no_pr_triggered_workflow_run_found",
    "outcome_only_current_head_evidence",
    "insufficient_decision_time_evidence",
    "multiple_blockers",
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


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], [f"missing JSONL file: {path}"]
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            errors.append(f"line {line_no}: blank line")
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(row, dict):
            errors.append(f"line {line_no}: expected object")
            continue
        rows.append(row)
    return rows, errors


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


def main() -> int:
    plan, plan_errors = load_json(PLAN_JSON_PATH)
    ledger, ledger_errors = load_jsonl(LEDGER_PATH)
    scoring, scoring_errors = load_json(SCORING_PATH)
    readiness, readiness_errors = load_json(READINESS_AUDIT_PATH)
    errors = plan_errors + ledger_errors + scoring_errors + readiness_errors

    ledger_external = [row for row in ledger if row.get("category") == "external_real_repo_episode"]
    ledger_ids = {row.get("episode_id") for row in ledger_external}

    if len(ledger_external) != 11:
        errors.append(f"expected 11 beta external ledger episodes, found {len(ledger_external)}")

    if plan.get("limited_pilot_status") != "COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS":
        errors.append("limited_pilot_status must remain COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS")
    if plan.get("deterministic_replay_ready_count") != 0:
        errors.append("deterministic_replay_ready_count must be 0")
    if plan.get("full_scoring_allowed") is not False:
        errors.append("full_scoring_allowed must be false")
    if plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("controllergate_full_scoring must be NOT_RUN")
    if plan.get("decision_time_outcome_overlap_episode_count") != 0:
        errors.append("decision_time_outcome_overlap_episode_count must remain 0")

    scoring_leakage = scoring.get("future_leakage_checks") or {}
    if plan.get("decision_time_outcome_overlap_episode_count") != scoring_leakage.get(
        "decision_time_outcome_overlap_episode_count"
    ):
        errors.append("plan leakage count must match limited scoring leakage count")
    if scoring.get("overall_limited_pilot_result") != plan.get("limited_pilot_status"):
        errors.append("plan limited_pilot_status must match scoring result")
    if scoring.get("full_scoring_allowed") is not False:
        errors.append("scoring full_scoring_allowed must remain false")

    current_policy = plan.get("current_head_evidence_policy")
    if not isinstance(current_policy, dict):
        errors.append("current_head_evidence_policy must be an object")
        current_policy = {}
    if current_policy.get("current_head_sha") != "8f49190a6e9ae29c8c49301a7736e0f838dfd369":
        errors.append("current_head_sha must match Pass 1 readiness audit")
    if current_policy.get("current_head_evidence_role") != "outcome_only":
        errors.append("current_head evidence role must remain outcome_only")
    if current_policy.get("current_head_evidence_promoted_to_pr_head_proof") is not False:
        errors.append("current-head evidence must not be promoted to PR-head proof")

    blockers = set(plan.get("controlled_replay_blocker_classes") or [])
    if blockers != CONTROLLED_BLOCKERS:
        errors.append("controlled replay blocker vocabulary changed or is incomplete")

    episodes = plan.get("episodes")
    if not isinstance(episodes, list):
        errors.append("episodes must be a list")
        episodes = []
    plan_ids = {episode.get("episode_id") for episode in episodes if isinstance(episode, dict)}
    if plan_ids != ledger_ids:
        errors.append(f"plan episode set mismatch: missing={sorted(ledger_ids - plan_ids)}, extra={sorted(plan_ids - ledger_ids)}")

    eligible_now_count = 0
    for episode in episodes:
        if not isinstance(episode, dict):
            errors.append("episode entry must be an object")
            continue
        episode_id = episode.get("episode_id")
        if episode.get("source_repo") != "TatMapper":
            errors.append(f"{episode_id}: source_repo must be TatMapper")
        if episode.get("allowed_scoring_mode") == "full_scoring":
            errors.append(f"{episode_id}: full_scoring must not be allowed")
        if episode.get("allowed_scoring_mode") != "limited_pilot_review_only":
            errors.append(f"{episode_id}: allowed_scoring_mode must be limited_pilot_review_only")
        if episode.get("eligible_now") is True:
            eligible_now_count += 1
        elif episode.get("eligible_now") is not False:
            errors.append(f"{episode_id}: eligible_now must be boolean false")
        missing = episode.get("missing_fields")
        if not isinstance(missing, list) or not missing:
            errors.append(f"{episode_id}: missing_fields must be non-empty")
        blocker = episode.get("replay_blocker_class")
        if blocker not in CONTROLLED_BLOCKERS:
            errors.append(f"{episode_id}: invalid replay_blocker_class {blocker!r}")
        for required_field in [
            "required_pr_head_sha",
            "required_base_sha",
            "required_changed_files_snapshot",
            "required_failing_job_log",
            "required_failure_signature",
            "required_pre_repair_test_command",
            "required_repair_patch",
            "required_post_repair_test_command",
            "required_outcome_evidence",
        ]:
            if required_field not in episode:
                errors.append(f"{episode_id}: missing required field {required_field}")

    if eligible_now_count != 0:
        errors.append("no episode should be eligible_now in Pass 2")

    by_id = {episode.get("episode_id"): episode for episode in episodes if isinstance(episode, dict)}
    for episode_id, run_id, job_ids in [
        ("beta_episode_001", "17986583215", ["51166385920", "51166385937"]),
        ("beta_episode_002", "17984606083", ["51159403854", "51159403859"]),
    ]:
        episode = by_id.get(episode_id) or {}
        combined = json.dumps(episode)
        if run_id not in combined:
            errors.append(f"{episode_id}: must preserve failed run id {run_id}")
        for job_id in job_ids:
            if job_id not in combined:
                errors.append(f"{episode_id}: must preserve failed job id {job_id}")
        if "410" not in combined:
            errors.append(f"{episode_id}: must preserve GitHub API 410 log-unavailable status")
        if episode.get("eligible_now") is not False:
            errors.append(f"{episode_id}: run/job metadata alone must not make episode eligible")

    no_run_or_equivalent = {
        "no_pr_triggered_workflow_run_found",
        "outcome_only_current_head_evidence",
        "insufficient_decision_time_evidence",
    }
    for episode_id in [f"beta_episode_{idx:03d}" for idx in range(3, 12)]:
        episode = by_id.get(episode_id) or {}
        if episode.get("replay_blocker_class") not in no_run_or_equivalent:
            errors.append(f"{episode_id}: must remain no-run/equivalent blocked")

    readiness_count = readiness.get("deterministic_replay_ready_count")
    if readiness_count != plan.get("deterministic_replay_ready_count"):
        errors.append("plan deterministic_replay_ready_count must match readiness audit")

    summary = plan.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object")
        summary = {}
    expected_summary = {
        "episodes_reviewed": 11,
        "eligible_now_count": 0,
        "review_required_count": 11,
        "full_scoring_allowed": False,
        "next_gate": "evidence_acquisition_before_any_deterministic_replay_scoring",
    }
    for field, expected in expected_summary.items():
        if summary.get(field) != expected:
            errors.append(f"summary.{field} expected {expected!r}, got {summary.get(field)!r}")

    errors.extend(
        require_text(
            PLAN_REPORT_PATH,
            [
                "0 of 11 TatMapper external real-repo episodes are deterministic-replay-ready.",
                "Full scoring allowed: false",
                "Decision-time/outcome overlap episode count: 0",
                "Decoded job logs for those jobs returned GitHub API `410`",
                "The other nine TatMapper source SHAs exposed no PR-triggered workflow runs",
                "None of that current-head evidence is promoted to PR-head replay proof.",
                "Real-repo memory lift: not demonstrated",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY_PATH,
            [
                REQUIRED_FINAL_STATUS,
                "Replay-eligibility pathway is now complete.",
                "0 of 11 TatMapper episodes are deterministic-replay-ready.",
                "11 of 11 remain review-required.",
                "Current-head evidence is still outcome-only and is not PR-head proof.",
            ],
        )
    )

    if errors:
        print("v1.7-beta replay eligibility plan audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.7-beta replay eligibility plan audit: PASS")
    print("episodes reviewed: 11")
    print("deterministic replay-ready episodes: 0")
    print("full scoring allowed: false")
    print("ControllerGate full scoring: NOT RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
