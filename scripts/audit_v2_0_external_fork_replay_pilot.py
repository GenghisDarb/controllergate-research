#!/usr/bin/env python3
"""Audit the v2.0 external-fork replay pilot artifact bundle."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = REPO_ROOT / "outputs" / "v2_0_external_fork_replay_pilot"
PLAN_PATH = REPO_ROOT / "outputs" / "v2_0_external_fork_replay_pilot_plan.json"
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)
V19_COMPLETION_PATH = (
    REPO_ROOT
    / "outputs"
    / "v1_9_organic_style_replay_pilot_completion_pass"
    / "aggregate_v1_9_updated_memory_lift_assessment.json"
)
V18_CAMPAIGN_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
)
EPISODE_003_PATH = REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json"
BETA_REPLAY_PLAN_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
)
ALPHA_CLASSIFICATION_PATH = (
    REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"
)

REQUIRED_PILOT_FILES = [
    "pilot_plan.json",
    "candidate_search_log.json",
    "candidate_acceptance_rejection_table.json",
    "pilot_results.json",
    "aggregate_external_memory_lift_assessment.json",
    "pilot_summary.md",
    "SHA256SUMS.txt",
]

ALLOWED_CANDIDATE_CLASSIFICATIONS = {
    "rejected_license_or_ethics",
    "rejected_private_service_or_secret_required",
    "rejected_no_deterministic_validator",
    "rejected_too_large_or_slow",
    "blocked_local_replay_failed",
    "blocked_candidate_acquisition_failure",
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


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


def verify_sha256_manifest(base_dir: Path, recursive: bool = False) -> list[str]:
    manifest_path = base_dir / "SHA256SUMS.txt"
    if not manifest_path.exists():
        return [f"missing SHA256SUMS.txt in {base_dir}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"{manifest_path}:{line_no}: expected '<sha256>  <path>'")
            continue
        expected, rel = parts
        seen.add(rel)
        path = base_dir / rel
        if not path.exists():
            errors.append(f"{manifest_path}:{line_no}: missing artifact {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{manifest_path}:{line_no}: hash mismatch for {rel}")
    if recursive:
        for path in base_dir.rglob("*"):
            if path.is_file() and path.name != "SHA256SUMS.txt":
                rel = str(path.relative_to(base_dir)).replace("\\", "/")
                if rel not in seen:
                    errors.append(f"pilot SHA256SUMS missing artifact entry {rel}")
    return errors


def audit_candidate(record: dict[str, Any], candidate_dir: Path) -> list[str]:
    errors: list[str] = []
    candidate_id = record.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        return ["candidate record missing candidate_id"]
    classification = record.get("classification")
    if classification not in ALLOWED_CANDIDATE_CLASSIFICATIONS:
        errors.append(f"{candidate_id}: invalid classification {classification!r}")
    for field in [
        "repo_url",
        "license_summary",
        "rejection_or_block_reason",
        "clean_checkout_succeeded",
        "deterministic_command_existed",
        "local_replay_succeeded",
    ]:
        if field not in record:
            errors.append(f"{candidate_id}: missing field {field}")
    if record.get("clean_checkout_succeeded") is not True:
        errors.append(f"{candidate_id}: expected clean checkout to be recorded as true")
    if record.get("deterministic_command_existed") is not False:
        errors.append(f"{candidate_id}: deterministic command should be false for rejected acquisition")
    if record.get("local_replay_succeeded") is not False:
        errors.append(f"{candidate_id}: local replay should be false for rejected acquisition")
    if not record.get("rejection_or_block_reason"):
        errors.append(f"{candidate_id}: missing explicit rejection/block reason")
    license_summary = record.get("license_summary") if isinstance(record.get("license_summary"), dict) else {}
    if license_summary.get("license_summary_available") is not True:
        errors.append(f"{candidate_id}: license summary must be available")
    if not license_summary.get("license_files_found"):
        errors.append(f"{candidate_id}: license file list must be non-empty")
    source = record.get("source_repo_metadata") if isinstance(record.get("source_repo_metadata"), dict) else {}
    if not source.get("head_sha"):
        errors.append(f"{candidate_id}: missing source head SHA")
    scan = record.get("scan_result") if isinstance(record.get("scan_result"), dict) else {}
    if scan.get("deterministic_local_failure_found") is not False:
        errors.append(f"{candidate_id}: expected no deterministic local failure")
    for path in [
        candidate_dir / f"{candidate_id}.json",
        candidate_dir / f"{candidate_id}_license_summary.txt",
    ]:
        if not path.exists():
            errors.append(f"{candidate_id}: missing candidate artifact {path.name}")
        elif path.stat().st_size == 0:
            errors.append(f"{candidate_id}: candidate artifact is empty {path.name}")
    return errors


def main() -> int:
    errors: list[str] = []
    if not PILOT_DIR.exists():
        errors.append(f"pilot directory missing: {PILOT_DIR}")
    for name in REQUIRED_PILOT_FILES:
        path = PILOT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.0 pilot artifact: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"v2.0 pilot artifact is empty: {name}")

    pilot_plan, pilot_plan_errors = load_json(PILOT_DIR / "pilot_plan.json")
    search_log, search_errors = load_json(PILOT_DIR / "candidate_search_log.json")
    table, table_errors = load_json(PILOT_DIR / "candidate_acceptance_rejection_table.json")
    results, results_errors = load_json(PILOT_DIR / "pilot_results.json")
    aggregate, aggregate_errors = load_json(PILOT_DIR / "aggregate_external_memory_lift_assessment.json")
    preregistered_plan, plan_errors = load_json(PLAN_PATH)
    v19_completion, v19_errors = load_json(V19_COMPLETION_PATH)
    v18_campaign, v18_errors = load_json(V18_CAMPAIGN_PATH)
    episode_003, episode_003_errors = load_json(EPISODE_003_PATH)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY_PLAN_PATH)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING_PATH)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION_PATH)
    errors.extend(
        pilot_plan_errors
        + search_errors
        + table_errors
        + results_errors
        + aggregate_errors
        + plan_errors
        + v19_errors
        + v18_errors
        + episode_003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    if pilot_plan.get("pilot_id") != "v2_0_external_fork_replay_pilot":
        errors.append("pilot_plan pilot_id mismatch")
    if pilot_plan.get("pilot_status") != "executed_candidate_acquisition_only":
        errors.append("pilot_plan status must be executed_candidate_acquisition_only")
    if pilot_plan.get("full_scoring_allowed") is not False:
        errors.append("pilot_plan must keep full scoring false")
    if pilot_plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("pilot_plan must keep ControllerGate full scoring NOT_RUN")
    if pilot_plan.get("candidate_attempt_count") != 5:
        errors.append("pilot_plan candidate_attempt_count must be 5")

    if search_log.get("candidate_count") != 5:
        errors.append("candidate search log must record 5 candidates")
    if search_log.get("remote_ci_logs_used") is not False:
        errors.append("remote CI logs must not be used")
    if search_log.get("upstream_interactions") != "none":
        errors.append("upstream interactions must be none")
    if search_log.get("blocked_candidate_acquisition_is_negative_capability_evidence") is not False:
        errors.append("blocked acquisition must not be treated as negative capability evidence")

    records = table.get("records") if isinstance(table.get("records"), list) else []
    if len(records) != 5:
        errors.append("candidate table must contain 5 records")
    if table.get("rejected_candidate_count") != 5:
        errors.append("candidate table rejected_candidate_count must be 5")
    if table.get("blocked_candidate_count") != 0:
        errors.append("candidate table blocked_candidate_count must be 0")
    if table.get("accepted_scoreable_candidates") != []:
        errors.append("candidate table accepted_scoreable_candidates must be empty")
    counts = table.get("classification_counts") if isinstance(table.get("classification_counts"), dict) else {}
    if counts.get("rejected_no_deterministic_validator") != 5:
        errors.append("classification count for rejected_no_deterministic_validator must be 5")
    for record in records:
        errors.extend(audit_candidate(record, PILOT_DIR / "candidates"))

    expected_result_fields = {
        "candidate_attempt_count": 5,
        "scoreable_episode_count": 0,
        "positive_episode_count": 0,
        "negative_episode_count": 0,
        "inconclusive_episode_count": 0,
        "rejected_candidate_count": 5,
        "blocked_candidate_count": 0,
        "decision_time_outcome_overlap_count": 0,
        "corruption_episode_count": 0,
        "aggregate_classification": "blocked_external_candidate_acquisition_failure",
        "controllergate_full_scoring": "NOT_RUN",
    }
    for field, expected in expected_result_fields.items():
        if results.get(field) != expected:
            errors.append(f"pilot_results.{field} must be {expected!r}")
    for field in [
        "organic_external_memory_lift_demonstrated",
        "external_fork_memory_lift_demonstrated",
        "self_maintaining_software_demonstrated",
        "full_scoring_allowed",
    ]:
        if results.get(field) is not False:
            errors.append(f"pilot_results.{field} must be false")

    if aggregate.get("aggregate_classification") != "blocked_external_candidate_acquisition_failure":
        errors.append("aggregate classification must be blocked_external_candidate_acquisition_failure")
    criteria = aggregate.get("criteria_observed") if isinstance(aggregate.get("criteria_observed"), dict) else {}
    expected_criteria = {
        "scoreable_external_fork_episode_count": 0,
        "positive_memory_outperformance_episodes": 0,
        "decision_time_outcome_overlap_count": 0,
        "corruption_episode_count": 0,
        "replay_custody_passes_for_positive_episodes": False,
    }
    for field, expected in expected_criteria.items():
        if criteria.get(field) != expected:
            errors.append(f"aggregate criteria {field} must be {expected!r}")
    for field in [
        "external_fork_memory_lift_demonstrated",
        "organic_external_memory_lift_demonstrated",
        "self_maintaining_software_demonstrated",
        "full_scoring_allowed",
    ]:
        if aggregate.get(field) is not False:
            errors.append(f"aggregate.{field} must be false")
    if aggregate.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("aggregate ControllerGate full scoring must remain NOT_RUN")

    if preregistered_plan.get("plan_status") != "planning_only_no_execution":
        errors.append("v2.0 preregistered plan must remain planning-only")
    if preregistered_plan.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v2.0 preregistered plan must not demonstrate organic external memory lift")
    if preregistered_plan.get("full_scoring_allowed") is not False:
        errors.append("v2.0 preregistered plan must keep full scoring false")
    if v19_completion.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 limited user-owned organic-style result must remain preserved")
    if v19_completion.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v1.9 must not demonstrate organic external memory lift")
    if v18_campaign.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 seeded campaign result must remain preserved")
    if episode_003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 negative result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper deterministic replay-ready count must remain 0")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(verify_sha256_manifest(PILOT_DIR, recursive=True))
    episode_dirs = sorted(path for path in PILOT_DIR.glob("episode_*") if path.is_dir())
    if episode_dirs:
        errors.append("v2.0 pilot should not have scoreable episode directories when scoreable_episode_count is 0")
    errors.extend(
        require_text(
            PILOT_DIR / "pilot_summary.md",
            [
                "v2.0 tests forked/public replay evidence.",
                "Aggregate assessment: `blocked_external_candidate_acquisition_failure`",
                "External memory lift remains undemonstrated.",
                "Full scoring remains disallowed.",
                "Self-maintaining software remains undemonstrated.",
                "Blocked candidate acquisition is not negative capability evidence.",
            ],
        )
    )
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v2.0 External-Fork Replay Pilot Result",
                "v2.0 tests forked/public replay evidence.",
                "Blocked candidate acquisition is not negative capability evidence.",
                "Aggregate assessment: `blocked_external_candidate_acquisition_failure`",
                "External memory lift remains undemonstrated.",
                "Full scoring remains disallowed.",
                "Self-maintaining software remains undemonstrated.",
            ],
        )
    )

    if errors:
        print("v2.0 external-fork replay pilot audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.0 external-fork replay pilot audit: PASS")
    print("candidate attempts: 5")
    print("scoreable external/fork episodes: 0")
    print("aggregate: blocked_external_candidate_acquisition_failure")
    print("external memory lift demonstrated: false")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
