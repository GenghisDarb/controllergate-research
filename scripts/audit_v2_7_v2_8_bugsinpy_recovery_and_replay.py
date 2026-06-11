#!/usr/bin/env python3
"""Audit v2.7/v2.8 BugsInPy recovery and replay gate artifacts."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_7_bugsinpy_target_replay_promotion_recovery"
V28_DIR = REPO_ROOT / "outputs" / "v2_8_bugsinpy_real_bug_limited_replay_execution"
V27E_GATE = REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion" / "v2_8_execution_gate_decision.json"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_7_bugsinpy_target_replay_recovery.yml"
PROBE = REPO_ROOT / "scripts" / "v2_7_bugsinpy_target_replay_recovery_probe.py"
V25_STATUS = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "runner_status.json"
V26_RESULTS = REPO_ROOT / "outputs" / "v2_6_bugsinpy_real_bug_limited_replay" / "campaign_results.json"
V24B_AGG = REPO_ROOT / "outputs" / "v2_4b_real_bug_runtime_unblock" / "aggregate_real_bug_memory_lift_assessment.json"
V24_AGG = REPO_ROOT / "outputs" / "v2_4_real_external_bug_replay_campaign" / "aggregate_real_external_bug_memory_lift_assessment.json"
V23_AGG = REPO_ROOT / "outputs" / "v2_3_known_external_bug_replay_campaign" / "aggregate_known_external_bug_memory_lift_assessment.json"
V22_AGG = REPO_ROOT / "outputs" / "v2_2_external_fork_controlled_fixture_replay_pilot" / "aggregate_external_fork_controlled_fixture_memory_lift_assessment.json"
V19_AGG = REPO_ROOT / "outputs" / "v1_9_organic_style_replay_pilot_completion_pass" / "aggregate_v1_9_updated_memory_lift_assessment.json"
V18_AGG = REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
E003_RESULT = REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json"
BETA_REPLAY = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING = REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
ALPHA_CLASSIFICATION = REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_OUTPUT_FILES = [
    "phase_a_dependency_repair_plan.json",
    "phase_a_dependency_repair_results.json",
    "phase_b_candidate_expansion_plan.json",
    "phase_b_candidate_expansion_results.json",
    "additional_candidate_attempt_matrix.json",
    "additional_candidate_rejection_table.json",
    "promoted_bugsinpy_real_bug_candidate_pool.json",
    "blocked_candidate_summary.json",
    "target_failure_matching_summary.json",
    "v2_8_execution_gate_decision.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_RERUN_FILES = [
    "candidate_metadata.json",
    "prior_blocker_summary.json",
    "dependency_install_plan.json",
    "dependency_install_commands.txt",
    "dependency_install_log_raw.txt",
    "checkout_command.txt",
    "checkout_log_raw.txt",
    "compile_command.txt",
    "compile_log_raw.txt",
    "test_command.txt",
    "test_log_raw.txt",
    "failure_signature.txt",
    "target_failure_match_check.json",
    "gold_patch_exclusion_plan.json",
    "replay_feasibility_result.json",
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


def later_v28_gate_passed() -> bool:
    if not V27E_GATE.exists():
        return False
    data, _ = load_json(V27E_GATE)
    return data.get("execute_v2_8") is True and data.get("target_matched_candidate_count") == 3


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


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


def audit_rerun_dir(directory: Path) -> list[str]:
    errors: list[str] = []
    if not directory.exists():
        return [f"missing rerun directory: {directory}"]
    for name in REQUIRED_RERUN_FILES:
        path = directory / name
        if not path.exists():
            errors.append(f"{directory.name}: missing required artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"{directory.name}: empty required artifact {name}")
    match, match_errors = load_json(directory / "target_failure_match_check.json")
    exclusion, exclusion_errors = load_json(directory / "gold_patch_exclusion_plan.json")
    feasibility, feasibility_errors = load_json(directory / "replay_feasibility_result.json")
    errors.extend(match_errors + exclusion_errors + feasibility_errors)
    if match.get("promotion_status", "").startswith("promoted") and match.get("target_failure_matched") is not True:
        errors.append(f"{directory.name}: promoted candidate must have target_failure_matched true")
    if match.get("dependency_or_import_failure_counts_as_target_replay") is True:
        errors.append(f"{directory.name}: dependency/import failure must not count as target replay")
    if exclusion.get("fixed_revision_used_at_decision_time") is not False:
        errors.append(f"{directory.name}: fixed revision must not be decision-time input")
    if exclusion.get("gold_patch_used_at_decision_time") is not False:
        errors.append(f"{directory.name}: gold patch must not be decision-time input")
    if feasibility.get("promotion_status", "").startswith("promoted") and feasibility.get("target_failure_matched") is not True:
        errors.append(f"{directory.name}: feasibility cannot promote without target failure")
    errors.extend(verify_manifest(directory))
    return errors


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.7 output directory: {OUTPUT_DIR}")
    if not WORKFLOW.exists():
        errors.append("missing v2.7 GitHub Actions recovery workflow")
    if not PROBE.exists():
        errors.append("missing v2.7 BugsInPy recovery probe script")
    for name in REQUIRED_OUTPUT_FILES:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.7 output artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.7 output artifact {name}")
    phase_a, phase_a_errors = load_json(OUTPUT_DIR / "phase_a_dependency_repair_results.json")
    phase_b, phase_b_errors = load_json(OUTPUT_DIR / "phase_b_candidate_expansion_results.json")
    pool, pool_errors = load_json(OUTPUT_DIR / "promoted_bugsinpy_real_bug_candidate_pool.json")
    blocked, blocked_errors = load_json(OUTPUT_DIR / "blocked_candidate_summary.json")
    target_summary, target_errors = load_json(OUTPUT_DIR / "target_failure_matching_summary.json")
    gate, gate_errors = load_json(OUTPUT_DIR / "v2_8_execution_gate_decision.json")
    v25, v25_errors = load_json(V25_STATUS)
    v26, v26_errors = load_json(V26_RESULTS)
    v24b, v24b_errors = load_json(V24B_AGG)
    v24, v24_errors = load_json(V24_AGG)
    v23, v23_errors = load_json(V23_AGG)
    v22, v22_errors = load_json(V22_AGG)
    v19, v19_errors = load_json(V19_AGG)
    v18, v18_errors = load_json(V18_AGG)
    e003, e003_errors = load_json(E003_RESULT)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING)
    alpha, alpha_errors = load_json(ALPHA_CLASSIFICATION)
    errors.extend(
        phase_a_errors
        + phase_b_errors
        + pool_errors
        + blocked_errors
        + target_errors
        + gate_errors
        + v25_errors
        + v26_errors
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
    errors.extend(audit_rerun_dir(OUTPUT_DIR / "black_2_dependency_rerun"))
    errors.extend(audit_rerun_dir(OUTPUT_DIR / "black_8_dependency_rerun"))
    if phase_a.get("newly_promoted_count") != 0:
        errors.append("phase A must not promote candidates without a fresh recovery artifact")
    if phase_b.get("additional_candidates_attempted_locally") != 0:
        errors.append("phase B local expansion count must remain 0 without Linux artifact")
    if pool.get("count") != 1:
        errors.append("promoted candidate pool must preserve exactly one current target-matched candidate")
    if target_summary.get("final_target_matched_count") != 1:
        errors.append("final target-matched count must be 1 in current local campaign")
    if target_summary.get("dependency_import_failures_count_as_target_replay") is not False:
        errors.append("dependency/import failures must not count as target replay")
    if gate.get("target_matched_candidate_count") != 1 or gate.get("execute_v2_8") is not False:
        errors.append("v2.8 gate decision must block execution with one target-matched candidate")
    if gate.get("repair_scoring_run") is not False:
        errors.append("repair scoring must remain NOT RUN unless v2.8 gate passes")
    blocked_records = blocked.get("records") if isinstance(blocked.get("records"), list) else []
    blocked_candidates = {record.get("candidate") for record in blocked_records if isinstance(record, dict)}
    if blocked.get("blocked_count", 0) < 2 or not {"black:2", "black:8"}.issubset(blocked_candidates):
        errors.append("blocked candidate summary must include black:2 and black:8")
    if V28_DIR.exists() and not later_v28_gate_passed():
        errors.append("v2.8 output directory must not exist when no later gate passes")
    if v25.get("promoted_candidate_count") != 1:
        errors.append("corrected v2.5 promoted count must remain 1")
    if v26.get("aggregate_result") != "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift":
        errors.append("v2.6 insufficient-count result must remain preserved")
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
        errors.append("Episode 003 negative result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper quarantine must remain unchanged")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha.get("summary") if isinstance(alpha.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")
    errors.extend(verify_manifest(OUTPUT_DIR))
    errors.extend(
        require_text(
            OUTPUT_DIR / "campaign_summary.md",
            [
                "Dependency repair is runtime setup, not code repair.",
                "Target-failure matching remains mandatory.",
                "v2.8 limited replay execution did not run.",
                "Full scoring remains disallowed.",
                "Memory lift is not demonstrated.",
                "Self-maintaining software is not demonstrated.",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY,
            [
                "v2.7/v2.8 BugsInPy Target-Replay Recovery and Limited Replay Campaign",
                "Dependency repair is runtime setup, not code repair.",
                "Dependency/import failures do not count as target bug replay.",
                "v2.8 executed: false.",
                "Full scoring remains disallowed.",
            ],
        )
    )
    if errors:
        print("v2.7/v2.8 BugsInPy recovery and replay audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.7/v2.8 BugsInPy recovery and replay audit: PASS")
    print("final target-matched candidates: 1")
    print("v2.8 executed: false")
    print("repair scoring run: false")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
