#!/usr/bin/env python3
"""Audit v2.6 BugsInPy real-bug limited replay campaign artifacts."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_6_bugsinpy_real_bug_limited_replay"
V25_STATUS = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "runner_status.json"
V25_PARSED = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "parsed_runtime_artifact_summary.json"
V24B_AGG = REPO_ROOT / "outputs" / "v2_4b_real_bug_runtime_unblock" / "aggregate_real_bug_memory_lift_assessment.json"
V24_AGG = REPO_ROOT / "outputs" / "v2_4_real_external_bug_replay_campaign" / "aggregate_real_external_bug_memory_lift_assessment.json"
V23_AGG = (
    REPO_ROOT
    / "outputs"
    / "v2_3_known_external_bug_replay_campaign"
    / "aggregate_known_external_bug_memory_lift_assessment.json"
)
V22_AGG = (
    REPO_ROOT
    / "outputs"
    / "v2_2_external_fork_controlled_fixture_replay_pilot"
    / "aggregate_external_fork_controlled_fixture_memory_lift_assessment.json"
)
V19_AGG = (
    REPO_ROOT
    / "outputs"
    / "v1_9_organic_style_replay_pilot_completion_pass"
    / "aggregate_v1_9_updated_memory_lift_assessment.json"
)
V18_AGG = REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
E003_RESULT = REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json"
BETA_REPLAY = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING = REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
ALPHA_CLASSIFICATION = REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_CAMPAIGN_FILES = [
    "campaign_plan.json",
    "campaign_results.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "campaign_summary.md",
    "candidate_source_integrity_check.json",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE_FILES = [
    "episode_metadata.json",
    "source_repo_metadata.json",
    "license_summary.txt",
    "candidate_selection_record.json",
    "bugsinpy_bug_reference.json",
    "target_repo_snapshot.json",
    "environment_snapshot.txt",
    "decision_time_input_manifest.json",
    "gold_patch_exclusion_check.json",
    "failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "pre_repair_replay_transcript.txt",
    "no_memory_decision_time_inputs.json",
    "no_memory_action_trace.json",
    "no_memory_repair_patch.diff",
    "no_memory_post_repair_log_raw.txt",
    "no_memory_outcome.json",
    "memory_enabled_decision_time_inputs.json",
    "memory_enabled_action_trace.json",
    "memory_evidence_used.json",
    "memory_enabled_repair_patch.diff",
    "memory_enabled_post_repair_log_raw.txt",
    "memory_enabled_outcome.json",
    "post_repair_comparison.json",
    "corruption_check_result.json",
    "decision_time_outcome_overlap_check.json",
    "limited_scoring_result.json",
    "proof_obligations_ledger.json",
    "SHA256SUMS.txt",
]


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


def verify_manifest(directory: Path, recursive: bool = True) -> list[str]:
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.exists():
        return [f"missing SHA256SUMS.txt in {directory}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"{manifest}:{line_no}: expected '<sha256>  <path>'")
            continue
        expected, rel = parts
        seen.add(rel)
        path = directory / rel
        if not path.exists():
            errors.append(f"{manifest}:{line_no}: missing artifact {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{manifest}:{line_no}: hash mismatch for {rel}")
    if recursive:
        for path in directory.rglob("*"):
            if path.is_file() and path.name != "SHA256SUMS.txt":
                rel = str(path.relative_to(directory)).replace("\\", "/")
                if rel not in seen:
                    errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def audit_episode(directory: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_EPISODE_FILES:
        path = directory / name
        if not path.exists():
            errors.append(f"{directory.name}: missing required artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"{directory.name}: empty required artifact {name}")
    scoring, scoring_errors = load_json(directory / "limited_scoring_result.json")
    exclusion, exclusion_errors = load_json(directory / "gold_patch_exclusion_check.json")
    overlap, overlap_errors = load_json(directory / "decision_time_outcome_overlap_check.json")
    errors.extend(scoring_errors + exclusion_errors + overlap_errors)
    if scoring.get("full_scoring_allowed") is not False or scoring.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append(f"{directory.name}: full scoring must remain NOT_RUN/disallowed")
    if exclusion.get("gold_fixed_patches_excluded_from_decision_time_inputs") is not True:
        errors.append(f"{directory.name}: gold/fixed patch exclusion must be true")
    if overlap.get("overlap_detected") is not False:
        errors.append(f"{directory.name}: decision-time/outcome overlap must be false")
    errors.extend(verify_manifest(directory))
    return errors


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.6 output directory: {OUTPUT_DIR}")
    for name in REQUIRED_CAMPAIGN_FILES:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.6 campaign artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.6 campaign artifact {name}")

    plan, plan_errors = load_json(OUTPUT_DIR / "campaign_plan.json")
    results, results_errors = load_json(OUTPUT_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    integrity, integrity_errors = load_json(OUTPUT_DIR / "candidate_source_integrity_check.json")
    v25_status, v25_status_errors = load_json(V25_STATUS)
    v25_parsed, v25_parsed_errors = load_json(V25_PARSED)
    v24b, v24b_errors = load_json(V24B_AGG)
    v24, v24_errors = load_json(V24_AGG)
    v23, v23_errors = load_json(V23_AGG)
    v22, v22_errors = load_json(V22_AGG)
    v19, v19_errors = load_json(V19_AGG)
    v18, v18_errors = load_json(V18_AGG)
    e003, e003_errors = load_json(E003_RESULT)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION)
    errors.extend(
        plan_errors
        + results_errors
        + aggregate_errors
        + integrity_errors
        + v25_status_errors
        + v25_parsed_errors
        + v24b_errors
        + v24_errors
        + v23_errors
        + v22_errors
        + v19_errors
        + v18_errors
        + e003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    if plan.get("target_failure_matching_guard_required") is not True:
        errors.append("v2.6 plan must require target-failure matching guard")
    if integrity.get("target_failure_matching_guard_exists") is not True:
        errors.append("target-failure matching guard must exist")
    if integrity.get("target_failure_matching_guard_enforced") is not True:
        errors.append("target-failure matching guard must be enforced")
    if integrity.get("dependency_import_or_runtime_failure_counts_as_target_replay") is not False:
        errors.append("dependency/import/runtime failure must not count as target replay")

    records = integrity.get("records") if isinstance(integrity.get("records"), list) else []
    if len(records) != 3:
        errors.append("v2.6 source integrity must include exactly three BugsInPy candidates")
    for record in records:
        candidate = record.get("candidate")
        final_status = record.get("final_promotion_status")
        if record.get("dependency_or_import_failure_detected") is True and final_status == "promoted_ready_for_v2_5_bugsinpy_real_bug":
            errors.append(f"{candidate}: dependency/import/runtime failure cannot be promoted")
        if final_status == "promoted_ready_for_v2_5_bugsinpy_real_bug" and record.get("target_failure_matched") is not True:
            errors.append(f"{candidate}: promoted candidate must match target failure")
    if integrity.get("target_matched_promoted_count") != 1:
        errors.append("v2.6 should preserve exactly one target-matched promoted candidate from current v2.5 artifact")
    if integrity.get("blocked_target_mismatch_count") != 2:
        errors.append("v2.6 should block two target-mismatch candidates from current v2.5 artifact")

    expected = "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    if results.get("aggregate_result") != expected or aggregate.get("aggregate_result") != expected:
        errors.append("v2.6 aggregate result mismatch")
    if results.get("executed_episode_count") != 0 or results.get("scoreable_episode_count") != 0:
        errors.append("v2.6 must not execute scoreable episodes when source integrity leaves one candidate")
    if results.get("repair_scoring_run") is not False:
        errors.append("v2.6 must not run repair scoring in blocked/insufficient state")
    if results.get("full_scoring_allowed") is not False or results.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.6 must keep full scoring NOT_RUN/disallowed")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is not False:
        errors.append("v2.6 must not claim BugsInPy memory lift")
    if aggregate.get("gold_fixed_patches_excluded_from_decision_time_inputs") is not True:
        errors.append("gold/fixed patch exclusion must be true")
    if aggregate.get("decision_time_outcome_overlap_count") != 0:
        errors.append("decision-time/outcome overlap count must remain 0")
    if aggregate.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain false")
    if aggregate.get("broad_organic_external_memory_lift_demonstrated") is not False:
        errors.append("broad organic external memory lift must remain false")

    if v25_status.get("promoted_candidate_count") != 1:
        errors.append("v2.5 target-guarded promoted candidate count must remain 1")
    if v25_parsed.get("promoted_candidate_count") != 1:
        errors.append("v2.5 parsed summary promoted count must remain 1")
    if v24b.get("aggregate_result") != "blocked_real_bug_runtime_unavailable":
        errors.append("v2.4b blocked runtime result must remain preserved")
    if v24.get("aggregate_result") != "blocked_real_external_bug_candidate_acquisition_failure":
        errors.append("v2.4 blocked acquisition result must remain preserved")
    if v23.get("aggregate_result") != "limited_known_external_or_benchmark_memory_lift_criteria_met":
        errors.append("v2.3 QuixBugs benchmark result must remain preserved")
    if v22.get("aggregate_result") != "limited_external_fork_controlled_fixture_memory_lift_criteria_met":
        errors.append("v2.2 external-fork controlled fixture result must remain preserved")
    if v19.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 user-owned result must remain preserved")
    if v18.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 seeded result must remain preserved")
    if e003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 negative simple-task result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper quarantine must remain unchanged")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    episode_dir = OUTPUT_DIR / "episodes"
    episode_dirs = sorted(episode_dir.glob("episode_*")) if episode_dir.exists() else []
    for directory in episode_dirs:
        errors.extend(audit_episode(directory))
    errors.extend(verify_manifest(OUTPUT_DIR, recursive=True))
    errors.extend(
        require_text(
            OUTPUT_DIR / "campaign_summary.md",
            [
                "Result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.",
                "blocked after target-failure guard",
                "No limited replay scoring episodes were executed.",
                "Gold/fixed patches are outcome-only",
                "Full scoring remains disallowed.",
                "Self-maintaining software remains undemonstrated.",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY,
            [
                "v2.6 BugsInPy Real-Bug Limited Replay Execution",
                "target-failure matching is now a hard gate",
                "Executed episodes: 0.",
                "Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.",
                "Full scoring remains disallowed.",
            ],
        )
    )

    if errors:
        print("v2.6 BugsInPy real-bug limited replay audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.6 BugsInPy real-bug limited replay audit: PASS")
    print("target-matched promoted candidates: 1")
    print("executed episodes: 0")
    print(f"aggregate: {expected}")
    print("memory lift demonstrated: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
