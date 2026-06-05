#!/usr/bin/env python3
"""Audit v2.4b BugsInPy/SWE-bench runtime unblock artifacts."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_DIR = REPO_ROOT / "outputs" / "v2_4b_real_bug_runtime_unblock"
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

REQUIRED_ROOT_FILES = [
    "runtime_probe_plan.json",
    "runtime_probe_results.json",
    "environment_capability_report.md",
    "benchmark_runtime_blocker_report.md",
    "runtime_unblock_results.json",
    "promoted_real_bug_candidate_pool.json",
    "campaign_results.json",
    "aggregate_real_bug_memory_lift_assessment.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_BUGSINPY_FILES = [
    "candidate_metadata.json",
    "bugsinpy_command_probe.txt",
    "checkout_command.txt",
    "checkout_log_raw.txt",
    "compile_command.txt",
    "compile_log_raw.txt",
    "failing_test_command.txt",
    "failing_test_log_raw.txt",
    "failure_signature.txt",
    "replay_feasibility_result.json",
    "gold_patch_exclusion_plan.json",
    "SHA256SUMS.txt",
]

REQUIRED_SWEBENCH_FILES = [
    "candidate_metadata.json",
    "docker_probe.txt",
    "swebench_harness_probe.txt",
    "instance_selection_record.json",
    "failing_test_command.txt",
    "failing_test_log_raw.txt",
    "failure_signature.txt",
    "replay_feasibility_result.json",
    "gold_patch_exclusion_plan.json",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE_FILES = [
    "episode_metadata.json",
    "source_repo_metadata.json",
    "license_summary.txt",
    "candidate_selection_record.json",
    "known_issue_or_bug_reference.json",
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


def check_required(directory: Path, names: list[str]) -> list[str]:
    errors: list[str] = []
    for name in names:
        path = directory / name
        if not path.exists():
            errors.append(f"{directory.name}: missing required artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"{directory.name}: empty required artifact {name}")
    return errors


def audit_candidate(directory: Path, kind: str) -> list[str]:
    errors: list[str] = []
    errors.extend(check_required(directory, REQUIRED_BUGSINPY_FILES if kind == "bugsinpy" else REQUIRED_SWEBENCH_FILES))
    feasibility, feasibility_errors = load_json(directory / "replay_feasibility_result.json")
    exclusion, exclusion_errors = load_json(directory / "gold_patch_exclusion_plan.json")
    metadata, metadata_errors = load_json(directory / "candidate_metadata.json")
    errors.extend(feasibility_errors + exclusion_errors + metadata_errors)
    status = feasibility.get("promotion_status")
    if status and status.startswith("promoted_ready_for_v2_4b"):
        if feasibility.get("runtime_replay_confirmed") is not True:
            errors.append(f"{directory.name}: promoted candidate lacks actual runtime/replay evidence")
        if feasibility.get("failing_test_reproduced") is not True:
            errors.append(f"{directory.name}: promoted candidate lacks failing test reproduction")
    else:
        if feasibility.get("runtime_replay_confirmed") is not False:
            errors.append(f"{directory.name}: blocked candidate should record runtime_replay_confirmed false")
    if exclusion.get("allowed_at_decision_time") is not False:
        errors.append(f"{directory.name}: gold/corrected patches must be barred from decision-time inputs")
    if kind == "bugsinpy" and metadata.get("source_family") != "bugsinpy":
        errors.append(f"{directory.name}: expected BugsInPy source family")
    if kind == "swebench" and "swe" not in str(metadata.get("source_family", "")):
        errors.append(f"{directory.name}: expected SWE-bench source family")
    errors.extend(verify_manifest(directory))
    return errors


def audit_episode(directory: Path) -> list[str]:
    errors = check_required(directory, REQUIRED_EPISODE_FILES)
    gold_check, gold_errors = load_json(directory / "gold_patch_exclusion_check.json")
    overlap, overlap_errors = load_json(directory / "decision_time_outcome_overlap_check.json")
    scoring, scoring_errors = load_json(directory / "limited_scoring_result.json")
    errors.extend(gold_errors + overlap_errors + scoring_errors)
    if gold_check.get("gold_patch_excluded_from_decision_time_inputs") is not True:
        errors.append(f"{directory.name}: gold/corrected patch exclusion check must pass")
    if overlap.get("overlap_detected") is not False:
        errors.append(f"{directory.name}: decision-time/outcome overlap must be false")
    if scoring.get("full_scoring_allowed") is not False or scoring.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append(f"{directory.name}: full scoring must remain NOT_RUN/disallowed")
    errors.extend(verify_manifest(directory))
    return errors


def main() -> int:
    errors: list[str] = []
    if not CAMPAIGN_DIR.exists():
        errors.append(f"missing v2.4b campaign directory: {CAMPAIGN_DIR}")
    for name in REQUIRED_ROOT_FILES:
        path = CAMPAIGN_DIR / name
        if not path.exists():
            errors.append(f"missing v2.4b root artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.4b artifact {name}")

    plan, plan_errors = load_json(CAMPAIGN_DIR / "runtime_probe_plan.json")
    probes, probe_errors = load_json(CAMPAIGN_DIR / "runtime_probe_results.json")
    unblock, unblock_errors = load_json(CAMPAIGN_DIR / "runtime_unblock_results.json")
    pool, pool_errors = load_json(CAMPAIGN_DIR / "promoted_real_bug_candidate_pool.json")
    results, results_errors = load_json(CAMPAIGN_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(CAMPAIGN_DIR / "aggregate_real_bug_memory_lift_assessment.json")
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
        + probe_errors
        + unblock_errors
        + pool_errors
        + results_errors
        + aggregate_errors
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

    if plan.get("full_scoring_allowed") is not False or plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.4b plan must keep full scoring NOT_RUN/disallowed")
    if plan.get("gold_corrected_patches_decision_time_allowed") is not False:
        errors.append("v2.4b plan must bar gold/corrected patches from decision time")
    for required in ["shell_probe_bash", "docker_info_probe", "bugsinpy_path_commands", "swe_bench_import_probe"]:
        if required not in probes:
            errors.append(f"runtime probe missing {required}")

    bugsinpy_dirs = sorted(CAMPAIGN_DIR.glob("bugsinpy_candidate_*"))
    swebench_dirs = sorted(CAMPAIGN_DIR.glob("swebench_candidate_*"))
    if len(bugsinpy_dirs) != 3:
        errors.append("expected exactly 3 BugsInPy smoke-test candidate directories")
    if len(swebench_dirs) != 1:
        errors.append("expected exactly 1 SWE-bench smoke-test candidate directory")
    for directory in bugsinpy_dirs:
        errors.extend(audit_candidate(directory, "bugsinpy"))
    for directory in swebench_dirs:
        errors.extend(audit_candidate(directory, "swebench"))

    if pool.get("count") != 0:
        errors.append("v2.4b should have zero promoted candidates in this environment")
    if unblock.get("execution_performed") is not False:
        errors.append("v2.4b must not execute repairs when promotion gate is closed")
    expected = "blocked_real_bug_runtime_unavailable"
    if unblock.get("aggregate_result") != expected or results.get("aggregate_result") != expected or aggregate.get("aggregate_result") != expected:
        errors.append("v2.4b aggregate result mismatch")
    if results.get("executed_episode_count") != 0 or results.get("scoreable_episode_count") != 0:
        errors.append("v2.4b must have zero executed/scoreable episodes")
    if aggregate.get("blocked_runtime_is_negative_capability_evidence") is not False:
        errors.append("blocked runtime must not be classified as negative capability evidence")
    if aggregate.get("gold_corrected_patches_excluded_from_decision_time_inputs") is not True:
        errors.append("gold/corrected patches must remain outcome-only")
    if aggregate.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain false")
    if aggregate.get("broad_organic_external_memory_lift_demonstrated") is not False:
        errors.append("broad organic external memory lift must remain false")
    if aggregate.get("full_scoring_allowed") is not False or aggregate.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain NOT_RUN/disallowed")

    episode_dir = CAMPAIGN_DIR / "episodes"
    episode_dirs = sorted(episode_dir.glob("episode_*")) if episode_dir.exists() else []
    if episode_dirs and pool.get("count", 0) == 0:
        errors.append("episodes exist even though no candidate promoted")
    for directory in episode_dirs:
        errors.extend(audit_episode(directory))

    if v24.get("aggregate_result") != "blocked_real_external_bug_candidate_acquisition_failure":
        errors.append("v2.4 local blocked result must remain preserved")
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
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(verify_manifest(CAMPAIGN_DIR, recursive=True))
    errors.extend(
        require_text(
            CAMPAIGN_DIR / "campaign_summary.md",
            [
                "The blocker is benchmark runtime acquisition.",
                "BugsInPy/SWE-bench candidates require local benchmark harness execution.",
                "Blocked runtime is not negative ControllerGate capability evidence.",
                "Gold/corrected patches are outcome-only.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY,
            [
                "v2.4b BugsInPy/SWE-bench Runtime Unblock",
                "The blocker is benchmark runtime acquisition.",
                "Blocked runtime is not negative ControllerGate capability evidence.",
                "Gold/corrected patches are outcome-only",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )

    if errors:
        print("v2.4b real bug runtime unblock audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.4b real bug runtime unblock audit: PASS")
    print("promoted candidates: 0")
    print("executed episodes: 0")
    print("scoreable episodes: 0")
    print(f"aggregate: {expected}")
    print("blocked runtime is negative capability evidence: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
