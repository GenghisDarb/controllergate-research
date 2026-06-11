#!/usr/bin/env python3
"""Generate v2.7b/v2.8 direct runner fix gate artifacts.

This local pass adds the executable GitHub Actions runner fix and preserves a
blocked v2.8 gate until fresh direct-runner artifacts provide at least three
clean target-matched BugsInPy candidates.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_7b_bugsinpy_direct_target_runner_fix"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V25_PARSED = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "parsed_runtime_artifact_summary.json"
V27_INGESTION = REPO_ROOT / "outputs" / "v2_7_bugsinpy_target_replay_promotion_recovery" / "runtime_artifact_ingestion_result.json"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def existing_promoted_records() -> list[dict[str, Any]]:
    parsed = load_json(V25_PARSED)
    records = parsed.get("records", []) if isinstance(parsed.get("records"), list) else []
    return [
        record
        for record in records
        if record.get("promotion_status") == "promoted_ready_for_v2_5_bugsinpy_real_bug"
        and record.get("target_failure_matched") is True
    ]


def write_blocked_candidate(directory: Path, project: str, bug_id: str, direct_command: str, prior_summary: str) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    candidate = f"{project}:{bug_id}"
    write_json(directory / "candidate_metadata.json", {"source_family": "bugsinpy", "project": project, "bug_id": bug_id, "candidate_class": "real_bug_benchmark_entry"})
    write_json(directory / "prior_v2_7_summary.json", {"summary": prior_summary})
    write_json(directory / "direct_rerun_plan.json", {"direct_command": direct_command, "bypass_bugsinpy_test_wrapper": True, "dependency_setup_is_runtime_setup_not_repair": True})
    write_json(directory / "dependency_install_plan.json", {"prefer_project_declared_dependencies": True, "source_file_modification_allowed": False, "fixed_or_gold_patch_used_at_decision_time": False})
    write_text(directory / "dependency_install_commands.txt", "cd <buggy-checkout> && python -m pip install -e .\n")
    write_text(directory / "dependency_install_log_raw.txt", "NOT_RUN_LOCALLY: run v2_7b_bugsinpy_direct_target_runner_fix workflow.\n")
    write_text(directory / "checkout_command.txt", f"bugsinpy-checkout -p {project} -v 0 -i {bug_id} -w <workspace>\n")
    write_text(directory / "checkout_log_raw.txt", "NOT_RUN_LOCALLY: run v2_7b_bugsinpy_direct_target_runner_fix workflow.\n")
    write_text(directory / "compile_command.txt", f"bugsinpy-compile -w <workspace>/{project}\n")
    write_text(directory / "compile_log_raw.txt", "NOT_RUN_LOCALLY: run v2_7b_bugsinpy_direct_target_runner_fix workflow.\n")
    write_text(directory / "direct_test_command.txt", direct_command + "\n")
    write_text(directory / "direct_test_log_raw.txt", "NOT_RUN_LOCALLY: run v2_7b_bugsinpy_direct_target_runner_fix workflow.\n")
    write_text(directory / "failure_signature.txt", f"DIRECT_TARGET_RERUN_PENDING: {candidate}\n")
    write_json(directory / "target_failure_match_check.json", {"candidate": candidate, "target_failure_matched": False, "promotion_status": "blocked_runtime_environment_failure", "reason": "fresh direct-runner artifact required"})
    write_json(directory / "wrapper_contamination_check.json", {"wrapper_path_bypassed": True, "wrapper_contamination_detected": False, "promotion_allowed": False})
    write_json(directory / "gold_patch_exclusion_plan.json", {"fixed_revision_used_at_decision_time": False, "gold_patch_used_at_decision_time": False})
    write_json(directory / "replay_feasibility_result.json", {"candidate": candidate, "promotion_status": "blocked_runtime_environment_failure", "runtime_replay_confirmed": False, "fixed_or_gold_patch_used_at_decision_time": False})
    write_manifest(directory)
    return {"candidate": candidate, "promotion_status": "blocked_runtime_environment_failure", "target_failure_matched": False, "direct_command": direct_command}


def update_summary(final_count: int, gate_result: str) -> None:
    section = f"""## v2.7b/v2.8 BugsInPy Direct Target Runner Fix and Conditional Replay

v2.7b fixes the runner by bypassing the broken BugsInPy wrapper path. `black:8` had target-failure signal but required clean direct rerun. Dependency/runtime setup is not code repair.

- `black:8` direct rerun result: pending fresh v2.7b GitHub Actions artifact.
- `black:2` direct rerun result: pending fresh v2.7b GitHub Actions artifact.
- Additional candidates attempted locally: 0.
- Final clean target-matched count: {final_count}.
- v2.8 executed: false.
- Gate result: `{gate_result}`.

Target-failure matching remains mandatory. Dependency/import/wrapper failures do not count as target bug replay. Candidate promotion is not repair success. Limited BugsInPy memory lift is not demonstrated. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.

Next required source/runtime action: run the `v2_7b_bugsinpy_direct_target_runner_fix` GitHub Actions workflow and ingest its artifact before any v2.8 repair scoring.
"""
    marker = "## v2.7b/v2.8 BugsInPy Direct Target Runner Fix and Conditional Replay"
    if SHAREABLE_SUMMARY.exists():
        text = SHAREABLE_SUMMARY.read_text(encoding="utf-8")
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n\n" + section
        else:
            text = text.rstrip() + "\n\n" + section
    else:
        text = section
    write_text(SHAREABLE_SUMMARY, text)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    previous_promoted = existing_promoted_records()
    v27 = load_json(V27_INGESTION)
    final_count = len(previous_promoted)
    gate_result = "insufficient_target_matched_candidates_for_v2_8"
    write_json(
        OUTPUT_DIR / "direct_runner_fix_plan.json",
        {
            "campaign": "v2.7b/v2.8 BugsInPy direct target runner fix",
            "workflow": ".github/workflows/v2_7b_bugsinpy_direct_target_runner_fix.yml",
            "runner_script": "scripts/v2_7b_bugsinpy_direct_target_runner_fix.py",
            "bypass_bugsinpy_test_wrapper": True,
            "full_scoring_allowed": False,
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "direct_command_catalog.json",
        {
            "black:8": "python -m unittest -q tests.test_black.BlackTestCase.test_comments7",
            "black:2": "python -m unittest -q tests.test_black.BlackTestCase.test_fmtonoff4",
            "youtube-dl:1": "python -m unittest -q test.test_utils.TestUtil.test_match_str",
        },
    )
    write_json(
        OUTPUT_DIR / "wrapper_bypass_policy.json",
        {
            "bugsinpy_test_r_wrapper_allowed_for_promotion": False,
            "direct_target_command_required": True,
            "wrapper_contamination_blocks_promotion": True,
        },
    )
    write_json(
        OUTPUT_DIR / "target_failure_matching_policy.json",
        {
            "target_failure_matching_mandatory": True,
            "dependency_import_runtime_or_wrapper_failures_count_as_target_replay": False,
            "gold_fixed_patch_allowed_at_decision_time": False,
        },
    )
    black8 = write_blocked_candidate(
        OUTPUT_DIR / "black_8_direct_target_rerun",
        "black",
        "8",
        "python -m unittest -q tests.test_black.BlackTestCase.test_comments7",
        "v2.7 showed target-looking test_comments7 failure with wrapper/runtime contamination.",
    )
    black2 = write_blocked_candidate(
        OUTPUT_DIR / "black_2_direct_target_rerun",
        "black",
        "2",
        "python -m unittest -q tests.test_black.BlackTestCase.test_fmtonoff4",
        "v2.7 remained blocked by AioHTTPTestCase runtime setup.",
    )
    write_json(
        OUTPUT_DIR / "direct_runner_fix_results.json",
        {
            "artifact_ingested": False,
            "local_execution_status": "blocked_pending_github_actions_artifact",
            "phase_a_results": [black8, black2],
            "newly_promoted_count": 0,
            "previous_v2_7_artifact_final_count": v27.get("final_target_matched_candidate_count"),
        },
    )
    write_json(
        OUTPUT_DIR / "phase_b_focused_candidate_recovery_plan.json",
        {"budget": 8, "trigger": "run only if black:8 and black:2 direct reruns leave fewer than three clean target-matched candidates", "local_execution_status": "not_run_pending_artifact"},
    )
    write_json(
        OUTPUT_DIR / "phase_b_focused_candidate_recovery_results.json",
        {"additional_candidates_attempted": 0, "newly_promoted_count": 0, "reason": "direct-runner workflow artifact is required first"},
    )
    write_json(OUTPUT_DIR / "additional_direct_candidate_attempt_matrix.json", {"attempted_count": 0, "attempts": []})
    write_json(OUTPUT_DIR / "additional_direct_candidate_rejection_table.json", {"rejected_or_blocked_count": 0, "records": []})
    write_json(OUTPUT_DIR / "promoted_bugsinpy_real_bug_candidate_pool.json", {"count": final_count, "records": previous_promoted})
    write_json(OUTPUT_DIR / "blocked_candidate_summary.json", {"blocked_count": 2, "records": [black8, black2]})
    write_json(
        OUTPUT_DIR / "target_failure_matching_summary.json",
        {
            "previous_target_matched_count": len(previous_promoted),
            "phase_a_new_target_matched_count": 0,
            "phase_b_new_target_matched_count": 0,
            "final_clean_target_matched_count": final_count,
            "target_failure_matching_mandatory": True,
        },
    )
    write_json(
        OUTPUT_DIR / "v2_8_execution_gate_decision.json",
        {
            "target_matched_candidate_count": final_count,
            "minimum_required": 3,
            "execute_v2_8": False,
            "repair_scoring_run": False,
            "gate_result": gate_result,
            "next_required_action": "Run v2.7b direct target GitHub Actions workflow and ingest artifact.",
        },
    )
    write_text(
        OUTPUT_DIR / "v2_8_not_executed_blocker_report.md",
        f"""# v2.8 Not Executed Blocker Report

v2.8 did not execute because only {final_count} clean target-matched BugsInPy candidate exists.

- valid: `youtube-dl:1`
- pending direct rerun: `black:8`
- pending direct rerun: `black:2`

Next required source/runtime action: run `v2_7b_bugsinpy_direct_target_runner_fix` and ingest the artifact.
""",
    )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        f"""# v2.7b/v2.8 BugsInPy Direct Target Runner Fix and Conditional Replay

Result: `{gate_result}`.

The direct target runner workflow and script are implemented. v2.8 did not execute because no fresh v2.7b direct-runner artifact has been ingested.

Final clean target-matched count: {final_count}.

Repair scoring remains NOT RUN. Full scoring remains disallowed. Memory lift is not demonstrated. Self-maintaining software is not demonstrated.
""",
    )
    update_summary(final_count, gate_result)
    write_manifest(OUTPUT_DIR)
    print("v2.7b/v2.8 direct runner fix gate artifacts generated")
    print(f"final clean target-matched candidates: {final_count}")
    print("v2.8 executed: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
