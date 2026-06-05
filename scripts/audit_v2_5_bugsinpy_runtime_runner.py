#!/usr/bin/env python3
"""Audit v2.5 BugsInPy Linux runtime runner setup."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "v2_5_bugsinpy_runtime_probe.yml"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner"
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

REQUIRED_OUTPUT_FILES = [
    "runner_plan.json",
    "runtime_probe_expected_artifacts.json",
    "candidate_attempt_matrix.json",
    "github_actions_usage_instructions.md",
    "runtime_artifact_ingestion_instructions.md",
    "runner_status.json",
    "SHA256SUMS.txt",
]

ARTIFACT_ROOT_FILES = [
    "runtime_environment.txt",
    "bugsinpy_install_log.txt",
    "bugsinpy_command_probe.txt",
    "runtime_probe_summary.json",
    "SHA256SUMS.txt",
]

ARTIFACT_CANDIDATE_FILES = [
    "candidate_metadata.json",
    "info_command.txt",
    "info_log_raw.txt",
    "checkout_command.txt",
    "checkout_log_raw.txt",
    "compile_command.txt",
    "compile_log_raw.txt",
    "test_command.txt",
    "test_log_raw.txt",
    "failure_signature.txt",
    "replay_feasibility_result.json",
    "gold_patch_exclusion_plan.json",
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


def verify_manifest(directory: Path) -> list[str]:
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
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rel = str(path.relative_to(directory)).replace("\\", "/")
            if rel not in seen:
                errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def main() -> int:
    errors: list[str] = []
    if not WORKFLOW_PATH.exists():
        errors.append(f"missing workflow file: {WORKFLOW_PATH}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.5 output directory: {OUTPUT_DIR}")
    for name in REQUIRED_OUTPUT_FILES:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.5 output artifact: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.5 artifact: {name}")

    plan, plan_errors = load_json(OUTPUT_DIR / "runner_plan.json")
    expected, expected_errors = load_json(OUTPUT_DIR / "runtime_probe_expected_artifacts.json")
    matrix, matrix_errors = load_json(OUTPUT_DIR / "candidate_attempt_matrix.json")
    status, status_errors = load_json(OUTPUT_DIR / "runner_status.json")
    parsed, parsed_errors = load_json(OUTPUT_DIR / "parsed_runtime_artifact_summary.json")
    promoted_pool, promoted_errors = load_json(OUTPUT_DIR / "promoted_real_bug_candidate_pool_from_artifacts.json")
    ingestion, ingestion_errors = load_json(OUTPUT_DIR / "runtime_artifact_ingestion_result.json")
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
        + expected_errors
        + matrix_errors
        + status_errors
        + ([] if not (OUTPUT_DIR / "parsed_runtime_artifact_summary.json").exists() else parsed_errors)
        + ([] if not (OUTPUT_DIR / "promoted_real_bug_candidate_pool_from_artifacts.json").exists() else promoted_errors)
        + ([] if not (OUTPUT_DIR / "runtime_artifact_ingestion_result.json").exists() else ingestion_errors)
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

    if WORKFLOW_PATH.exists():
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        for required in [
            "workflow_dispatch",
            "ubuntu-latest",
            "actions/checkout@v4",
            "actions/setup-python@v5",
            "scripts/v2_5_bugsinpy_runtime_probe.py",
            "v2_5_bugsinpy_runtime_probe_artifacts",
        ]:
            if required not in workflow_text:
                errors.append(f"workflow missing required text {required!r}")

    if plan.get("full_scoring_allowed") is not False or plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.5 plan must keep full scoring NOT_RUN/disallowed")
    if plan.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.5 plan must keep self-maintaining software false")
    if plan.get("broad_organic_external_memory_lift_demonstrated") is not False:
        errors.append("v2.5 plan must keep broad organic external memory lift false")
    if plan.get("gold_fixed_patches_decision_time_allowed") is not False:
        errors.append("v2.5 plan must bar gold/fixed patches from decision time")

    records = matrix.get("records") if isinstance(matrix.get("records"), list) else []
    handles = {f"{record.get('project')}:{record.get('bug_id')}" for record in records}
    for handle in {"black:2", "youtube-dl:1", "black:8"}:
        if handle not in handles:
            errors.append(f"candidate attempt matrix missing {handle}")
    if matrix.get("candidate_count") != 3:
        errors.append("candidate attempt matrix must contain exactly 3 candidates")
    if expected.get("artifact_name") != "v2_5_bugsinpy_runtime_probe_artifacts":
        errors.append("expected artifact name mismatch")
    for directory in ["black_2", "youtube_dl_1", "black_8"]:
        if directory not in expected.get("candidate_directories", []):
            errors.append(f"expected artifact schema missing candidate directory {directory}")

    valid_runner_statuses = {
        "workflow_ready_pending_manual_github_actions_run",
        "artifact_ingested_promoted_candidates",
        "artifact_ingested_no_promoted_candidates",
    }
    if status.get("runner_status") not in valid_runner_statuses:
        errors.append("runner_status must be a valid v2.5 runner state")
    if status.get("repair_scoring_run") is not False:
        errors.append("v2.5 must not run repair scoring")
    if status.get("full_scoring_allowed") is not False or status.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.5 status must keep full scoring NOT_RUN/disallowed")
    if status.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain false")
    if status.get("broad_organic_external_memory_lift_demonstrated") is not False:
        errors.append("broad organic external memory lift must remain false")

    if status.get("artifact_ingested") is True:
        artifact_dir = Path(status.get("artifact_dir", ""))
        if not artifact_dir.exists():
            errors.append(f"ingested artifact directory is missing: {artifact_dir}")
        for name in ARTIFACT_ROOT_FILES:
            path = artifact_dir / name
            if not path.exists():
                errors.append(f"ingested artifact missing root file {name}")
            elif path.stat().st_size == 0:
                errors.append(f"ingested artifact has empty root file {name}")
        expected_candidates = {
            "black_2": ("black", "2"),
            "youtube_dl_1": ("youtube-dl", "1"),
            "black_8": ("black", "8"),
        }
        for dirname, (project, bug_id) in expected_candidates.items():
            candidate_dir = artifact_dir / dirname
            if not candidate_dir.exists():
                errors.append(f"ingested artifact missing candidate directory {dirname}")
                continue
            for name in ARTIFACT_CANDIDATE_FILES:
                path = candidate_dir / name
                if not path.exists():
                    errors.append(f"{dirname}: missing artifact file {name}")
                elif path.stat().st_size == 0:
                    errors.append(f"{dirname}: empty artifact file {name}")
            feasibility, feasibility_errors = load_json(candidate_dir / "replay_feasibility_result.json")
            exclusion, exclusion_errors = load_json(candidate_dir / "gold_patch_exclusion_plan.json")
            errors.extend(feasibility_errors + exclusion_errors)
            if feasibility.get("project") != project or feasibility.get("bug_id") != bug_id:
                errors.append(f"{dirname}: feasibility project/bug mismatch")
            if feasibility.get("promotion_status") == "promoted_ready_for_v2_5_bugsinpy_real_bug":
                if feasibility.get("runtime_replay_confirmed") is not True:
                    errors.append(f"{dirname}: promoted candidate lacks runtime_replay_confirmed true")
                if feasibility.get("failing_test_reproduced") is not True:
                    errors.append(f"{dirname}: promoted candidate lacks failing_test_reproduced true")
            if feasibility.get("fixed_or_gold_patch_used_at_decision_time") is not False:
                errors.append(f"{dirname}: fixed/gold patch must not be used at decision time")
            if exclusion.get("allowed_at_decision_time") is not False:
                errors.append(f"{dirname}: gold/fixed patch exclusion plan must bar decision-time use")
            errors.extend(verify_manifest(candidate_dir))
        runtime_summary, runtime_summary_errors = load_json(artifact_dir / "runtime_probe_summary.json")
        errors.extend(runtime_summary_errors)
        if runtime_summary.get("fixed_or_gold_patch_used_at_decision_time") is not False:
            errors.append("runtime artifact summary must keep fixed/gold patch out of decision time")
        errors.extend(verify_manifest(artifact_dir))

        if not parsed:
            errors.append("artifact_ingested true requires parsed_runtime_artifact_summary.json")
        if not promoted_pool:
            errors.append("artifact_ingested true requires promoted_real_bug_candidate_pool_from_artifacts.json")
        if not ingestion:
            errors.append("artifact_ingested true requires runtime_artifact_ingestion_result.json")
        if parsed and parsed.get("promoted_candidate_count") != status.get("promoted_candidate_count"):
            errors.append("parsed promoted count must match runner_status")
        if promoted_pool and promoted_pool.get("count") != status.get("promoted_candidate_count"):
            errors.append("promoted pool count must match runner_status")
        if ingestion:
            if ingestion.get("repair_scoring_run") is not False:
                errors.append("artifact ingestion must not run repair scoring")
            if ingestion.get("gold_fixed_patch_used_at_decision_time") is not False:
                errors.append("artifact ingestion must not use fixed/gold patch at decision time")
            if ingestion.get("full_scoring_allowed") is not False or ingestion.get("controllergate_full_scoring") != "NOT_RUN":
                errors.append("artifact ingestion must keep full scoring NOT_RUN/disallowed")

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

    errors.extend(verify_manifest(OUTPUT_DIR))
    errors.extend(
        require_text(
            OUTPUT_DIR / "github_actions_usage_instructions.md",
            [
                "Run workflow",
                "v2_5_bugsinpy_runtime_probe",
                "v2_5_bugsinpy_runtime_probe_artifacts",
                "Candidate metadata alone does not prove replay readiness.",
            ],
        )
    )
    errors.extend(
        require_text(
            OUTPUT_DIR / "runtime_artifact_ingestion_instructions.md",
            [
                "v2_5_parse_bugsinpy_runtime_artifacts.py",
                "3 promoted candidates",
                "0 promoted candidates",
                "Do not use fixed/gold patches as decision-time inputs.",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY,
            [
                "v2.5 BugsInPy Linux Runtime Runner",
                "The current blocker is benchmark runtime acquisition.",
                "The workflow creates a Linux runtime path for BugsInPy replay.",
                "Candidate replay readiness requires fresh checkout/compile/test logs.",
                "Blocked runtime is not negative ControllerGate capability evidence.",
                "Gold/fixed patches are outcome-only.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )

    if errors:
        print("v2.5 BugsInPy Linux runtime runner audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.5 BugsInPy Linux runtime runner audit: PASS")
    print("workflow: present")
    print(f"runner status: {status.get('runner_status')}")
    print(f"promoted candidates: {status.get('promoted_candidate_count')}")
    print(f"handoff recommendation: {status.get('recommended_handoff')}")
    print("candidate attempts: black:2, youtube-dl:1, black:8")
    print("repair scoring run: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
