#!/usr/bin/env python3
"""Audit v2.8c BugsInPy repair checkout-fix campaign artifacts."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_A_DIR = REPO_ROOT / "outputs" / "v2_8c_bugsinpy_repair_checkout_fix"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8c_bugsinpy_real_bug_repair_comparison_rerun"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8c_bugsinpy_repair_checkout_fix.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8c_bugsinpy_repair_checkout_fix_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8c_prepare_bugsinpy_repair_checkout_fix.py"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

V27E_GATE = REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion" / "v2_8_execution_gate_decision.json"
V27D_GATE = REPO_ROOT / "outputs" / "v2_7d_bugsinpy_third_candidate_direct_runner_expansion" / "v2_8_execution_gate_decision.json"
V27B_GATE = REPO_ROOT / "outputs" / "v2_7b_bugsinpy_direct_target_runner_fix" / "v2_8_execution_gate_decision.json"
V27_INGEST = REPO_ROOT / "outputs" / "v2_7_bugsinpy_target_replay_promotion_recovery" / "runtime_artifact_ingestion_result.json"
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

REQUIRED_PHASE_A = [
    "v2_8b_artifact_ingestion_summary.json",
    "v2_8b_artifact_sha256_verification.json",
    "v2_8b_failure_diagnosis.json",
    "checkout_failure_root_cause_report.md",
    "episode_blocker_table.json",
    "apoptosis_watchdog_context_correction.json",
    "SHA256SUMS.txt",
]

REQUIRED_RERUN = [
    "campaign_plan.json",
    "campaign_results.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "campaign_summary.md",
    "candidate_source_integrity_check.json",
    "pre_repair_replay_gate_summary.json",
    "checkout_runtime_fix_summary.json",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE = [
    "episode_metadata.json",
    "source_repo_metadata.json",
    "license_summary.txt",
    "candidate_selection_record.json",
    "bugsinpy_bug_reference.json",
    "target_repo_snapshot.json",
    "environment_snapshot.txt",
    "absolute_workspace_path.txt",
    "project_root_path.txt",
    "checkout_path_resolution.json",
    "checkout_integrity_check.json",
    "decision_time_input_manifest.json",
    "gold_patch_exclusion_check.json",
    "label_blindness_check.json",
    "failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "target_failure_match_check.json",
    "wrapper_contamination_check.json",
    "pre_repair_replay_transcript.txt",
    "pre_repair_replay_gate_result.json",
    "dependency_install_plan.json",
    "dependency_install_commands.txt",
    "dependency_install_log_raw.txt",
    "compile_command.txt",
    "compile_log_raw.txt",
    "no_memory_decision_time_inputs.json",
    "no_memory_action_trace.json",
    "no_memory_repair_patch.diff",
    "no_memory_post_repair_command.txt",
    "no_memory_post_repair_log_raw.txt",
    "no_memory_outcome.json",
    "memory_enabled_decision_time_inputs.json",
    "memory_enabled_action_trace.json",
    "memory_evidence_used.json",
    "memory_enabled_repair_patch.diff",
    "memory_enabled_post_repair_command.txt",
    "memory_enabled_post_repair_log_raw.txt",
    "memory_enabled_outcome.json",
    "post_repair_comparison.json",
    "corruption_check_result.json",
    "decision_time_outcome_overlap_check.json",
    "limited_scoring_result.json",
    "proof_obligations_ledger.json",
    "apoptosis_watchdog_result.json",
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
            if path.is_file() and path.name != "SHA256SUMS.txt" and path.suffix.lower() != ".zip":
                rel = str(path.relative_to(directory)).replace("\\", "/")
                if rel not in seen:
                    errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def require_text(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing required text {snippet!r}" for snippet in snippets if snippet not in text]


def audit_episode(path: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_EPISODE:
        file = path / name
        if not file.exists():
            errors.append(f"{path.name}: missing {name}")
        elif file.stat().st_size == 0:
            errors.append(f"{path.name}: empty {name}")
    checkout_resolution, resolution_errors = load_json(path / "checkout_path_resolution.json")
    checkout_integrity, integrity_errors = load_json(path / "checkout_integrity_check.json")
    gate, gate_errors = load_json(path / "pre_repair_replay_gate_result.json")
    gold, gold_errors = load_json(path / "gold_patch_exclusion_check.json")
    label, label_errors = load_json(path / "label_blindness_check.json")
    overlap, overlap_errors = load_json(path / "decision_time_outcome_overlap_check.json")
    watchdog, watchdog_errors = load_json(path / "apoptosis_watchdog_result.json")
    scoring, scoring_errors = load_json(path / "limited_scoring_result.json")
    errors.extend(resolution_errors + integrity_errors + gate_errors + gold_errors + label_errors + overlap_errors + watchdog_errors + scoring_errors)
    if checkout_resolution.get("all_paths_absolute") is not True:
        errors.append(f"{path.name}: checkout path resolution must use absolute paths")
    if gate.get("pre_repair_replay_gate_passed") is not True and scoring.get("scoreable") is True:
        errors.append(f"{path.name}: cannot be scoreable when pre-repair replay gate fails")
    if gate.get("pre_repair_replay_gate_passed") is not True:
        for name in ["no_memory_outcome.json", "memory_enabled_outcome.json"]:
            outcome, outcome_errors = load_json(path / name)
            errors.extend(outcome_errors)
            if outcome.get("repair_path_ran") is True:
                errors.append(f"{path.name}: repair path ran despite failed pre-repair replay gate")
    for key in ["fixed_revision_used_at_decision_time", "gold_patch_used_at_decision_time", "corrected_files_used_as_repair_hints"]:
        if gold.get(key) is not False:
            errors.append(f"{path.name}: gold/fixed patch exclusion failed for {key}")
    if label.get("label_leakage_detected") is True:
        errors.append(f"{path.name}: label leakage detected")
    if overlap.get("overlap_detected") is True:
        errors.append(f"{path.name}: decision-time/outcome overlap detected")
    if checkout_integrity.get("checkout_integrity_passed") is not True and watchdog.get("infrastructure_checkout_failure_counted_as_flatline") is not False:
        errors.append(f"{path.name}: infrastructure checkout failure cannot be counted as repair flatline")
    errors.extend(verify_manifest(path))
    return errors


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.8c implementation file: {path}")
    if RUNNER.exists():
        runner_text = RUNNER.read_text(encoding="utf-8")
        for snippet in [
            "Path.cwd().resolve()",
            "workspace_parent = (RUNTIME_ROOT / \"workspaces\"",
            "symlinks=True",
            "repair_workspace_copy_result.json",
            "infrastructure_copy_failure_counts_as_repair_failure",
            "checkout_integrity_check.json",
            "pre_repair_replay_gate_result.json",
            "infrastructure_checkout_failure_counted_as_flatline",
        ]:
            if snippet not in runner_text:
                errors.append(f"v2.8c runner missing required checkout/pre-repair gate snippet: {snippet}")
    if not PHASE_A_DIR.exists():
        errors.append(f"missing v2.8c phase A output directory: {PHASE_A_DIR}")
    if not RERUN_DIR.exists():
        errors.append(f"missing v2.8c rerun output directory: {RERUN_DIR}")
    for name in REQUIRED_PHASE_A:
        path = PHASE_A_DIR / name
        if not path.exists():
            errors.append(f"missing phase A artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty phase A artifact {name}")
    for name in REQUIRED_RERUN:
        path = RERUN_DIR / name
        if not path.exists():
            errors.append(f"missing v2.8c rerun artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.8c rerun artifact {name}")

    ingestion, ingestion_errors = load_json(PHASE_A_DIR / "v2_8b_artifact_ingestion_summary.json")
    verification, verification_errors = load_json(PHASE_A_DIR / "v2_8b_artifact_sha256_verification.json")
    diagnosis, diagnosis_errors = load_json(PHASE_A_DIR / "v2_8b_failure_diagnosis.json")
    blockers, blockers_errors = load_json(PHASE_A_DIR / "episode_blocker_table.json")
    apoptosis, apoptosis_errors = load_json(PHASE_A_DIR / "apoptosis_watchdog_context_correction.json")
    results, results_errors = load_json(RERUN_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    fix_summary, fix_summary_errors = load_json(RERUN_DIR / "checkout_runtime_fix_summary.json")
    pre_gate, pre_gate_errors = load_json(RERUN_DIR / "pre_repair_replay_gate_summary.json")
    v27e, v27e_errors = load_json(V27E_GATE)
    v27d, v27d_errors = load_json(V27D_GATE)
    v27b, v27b_errors = load_json(V27B_GATE)
    v27_ingest, v27_ingest_errors = load_json(V27_INGEST)
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
        ingestion_errors
        + verification_errors
        + diagnosis_errors
        + blockers_errors
        + apoptosis_errors
        + results_errors
        + aggregate_errors
        + fix_summary_errors
        + pre_gate_errors
        + v27e_errors
        + v27d_errors
        + v27b_errors
        + v27_ingest_errors
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
    if verification.get("verification_clean") is not True:
        errors.append("v2.8b artifact SHA256 verification must be clean")
    if ingestion.get("workflow_executed") is not True or ingestion.get("executed_episode_count") != 3:
        errors.append("v2.8b artifact ingestion must preserve executed workflow with three episodes")
    if ingestion.get("scoreable_episode_count") != 0:
        errors.append("v2.8b artifact must remain zero-scoreable due checkout/runtime failure")
    if diagnosis.get("classification") != "blocked_checkout_runtime_failure" or diagnosis.get("negative_controllergate_repair_evidence") is not False:
        errors.append("v2.8b checkout failure must be classified blocked, not negative repair evidence")
    records = blockers.get("records", [])
    if len(records) != 3 or {record.get("candidate") for record in records} != {"youtube-dl:1", "black:8", "black:4"}:
        errors.append("episode blocker table must cover exactly the three BugsInPy candidates")
    if any(record.get("classification") != "blocked_checkout_runtime_failure" for record in records):
        errors.append("all v2.8b artifact episodes must be checkout/runtime blocked")
    if apoptosis.get("infrastructure_checkout_failure_counts_as_negative_repair_evidence") is not False:
        errors.append("apoptosis context correction must not count checkout failure as negative repair evidence")
    for key in ["absolute_workspace_paths_required", "bugsinpy_checkout_absolute_w_path_required", "checkout_integrity_check_required", "pre_repair_replay_gate_required"]:
        if fix_summary.get(key) is not True:
            errors.append(f"checkout runtime fix summary missing {key}=true")
    if results.get("full_scoring_allowed") is not False or results.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain NOT_RUN / disallowed")
    if results.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain not demonstrated")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True:
        if int(aggregate.get("scoreable_episode_count") or 0) < 3 or int(aggregate.get("positive_memory_episode_count") or 0) < 2:
            errors.append("memory lift can be claimed only if v2.8c aggregate criteria are met")
    workflow_executed = results.get("workflow_executed") is True
    episode_dirs = sorted(path for path in RERUN_DIR.glob("episode_*") if path.is_dir())
    if workflow_executed:
        if len(episode_dirs) != 3:
            errors.append("executed v2.8c workflow must produce three episode directories")
        for path in episode_dirs:
            errors.extend(audit_episode(path))
    else:
        if pre_gate.get("workflow_executed") is not False or pre_gate.get("repair_paths_run_count") != 0:
            errors.append("pending v2.8c rerun bundle cannot run repair paths")
        if results.get("scoreable_episode_count") != 0:
            errors.append("pending v2.8c rerun bundle cannot have scoreable episodes")
    if v27e.get("execute_v2_8") is not True or v27e.get("target_matched_candidate_count") != 3:
        errors.append("v2.7e/v2.8 candidate-pool result must remain preserved")
    if v27d.get("target_matched_candidate_count") != 2:
        errors.append("v2.7d result must remain preserved")
    if v27b.get("target_matched_candidate_count") != 1:
        errors.append("v2.7b direct-runner result must remain preserved")
    if v27_ingest.get("final_target_matched_candidate_count") != 1:
        errors.append("v2.7 artifact ingestion result must remain preserved")
    if v25.get("promoted_candidate_count") != 1:
        errors.append("corrected v2.5 result must remain preserved")
    if v26.get("aggregate_result") != "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift":
        errors.append("v2.6 insufficient-count result must remain preserved")
    if v24b.get("aggregate_result") != "blocked_real_bug_runtime_unavailable":
        errors.append("v2.4b blocked runtime result must remain preserved")
    if v24.get("aggregate_result") != "blocked_real_external_bug_candidate_acquisition_failure":
        errors.append("v2.4 blocked acquisition result must remain preserved")
    if v23.get("aggregate_result") != "limited_known_external_or_benchmark_memory_lift_criteria_met":
        errors.append("v2.3 QuixBugs benchmark result must remain preserved")
    if v22.get("aggregate_result") != "limited_external_fork_controlled_fixture_memory_lift_criteria_met":
        errors.append("v2.2 controlled fixture result must remain preserved")
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
    alpha_summary = alpha.get("summary") if isinstance(alpha.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")
    errors.extend(verify_manifest(PHASE_A_DIR))
    errors.extend(verify_manifest(RERUN_DIR))
    errors.extend(
        require_text(
            PHASE_A_DIR / "checkout_failure_root_cause_report.md",
            [
                "blocked checkout/runtime evidence",
                "not negative ControllerGate repair capability evidence",
                "absolute workspace paths",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY,
            [
                "v2.8c BugsInPy Repair-Comparison Checkout Fix",
                "Checkout/runtime failure is blocked evidence, not negative ControllerGate repair evidence.",
                "v2.8c checkout fix status",
                "Full scoring remains disallowed.",
                "Self-maintaining software remains undemonstrated.",
            ],
        )
    )
    if errors:
        print("v2.8c BugsInPy repair checkout-fix audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8c BugsInPy repair checkout-fix audit: PASS")
    print(f"v2.8b artifact scoreable episodes: {ingestion.get('scoreable_episode_count')}")
    print(f"v2.8c workflow executed: {str(workflow_executed).lower()}")
    print(f"aggregate: {aggregate.get('aggregate_result')}")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
