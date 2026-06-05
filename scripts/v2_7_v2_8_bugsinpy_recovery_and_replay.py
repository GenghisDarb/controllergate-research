#!/usr/bin/env python3
"""Generate v2.7/v2.8 BugsInPy recovery and replay gate artifacts.

The local Windows workspace cannot rerun BugsInPy Linux recovery commands.
This campaign therefore records the recovery workflow/gate, preserves the one
valid v2.5 target-matched candidate, and blocks v2.8 repair scoring until a
fresh v2.7 GitHub Actions artifact promotes at least two more candidates.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_7_bugsinpy_target_replay_promotion_recovery"
V25_PARSED = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "parsed_runtime_artifact_summary.json"
V26_RESULTS = REPO_ROOT / "outputs" / "v2_6_bugsinpy_real_bug_limited_replay" / "campaign_results.json"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"


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


def write_candidate_blocker_dir(
    directory: Path,
    project: str,
    bug_id: str,
    prior_blocker: str,
    dependency_hint: str,
    expected_marker: str,
) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    candidate_id = f"{project}:{bug_id}"
    write_json(
        directory / "candidate_metadata.json",
        {
            "source_family": "bugsinpy",
            "project": project,
            "bug_id": bug_id,
            "candidate_class": "real_bug_benchmark_entry",
            "recovery_status": "blocked_pending_linux_github_actions_rerun",
        },
    )
    write_json(
        directory / "prior_blocker_summary.json",
        {
            "candidate": candidate_id,
            "prior_blocker": prior_blocker,
            "dependency_repair_is_runtime_setup_not_code_repair": True,
        },
    )
    write_json(
        directory / "dependency_install_plan.json",
        {
            "candidate": candidate_id,
            "prefer_project_declared_dependencies": True,
            "explicit_dependency_if_needed": dependency_hint,
            "source_file_modification_allowed": False,
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_text(
        directory / "dependency_install_commands.txt",
        "\n".join(
            [
                "cd <buggy-checkout> && python -m pip install -e .",
                f"python -m pip install {dependency_hint}",
                "",
            ]
        ),
    )
    write_text(
        directory / "dependency_install_log_raw.txt",
        "NOT_RUN_LOCALLY: dependency recovery requires the v2.7 Ubuntu GitHub Actions runner artifact.\n",
    )
    checkout_command = f"bugsinpy-checkout -p {project} -v 0 -i {bug_id} -w <workspace>"
    compile_command = f"bugsinpy-compile -w <workspace>/{project}"
    test_command = f"bugsinpy-test -w <workspace>/{project} -r"
    write_text(directory / "checkout_command.txt", checkout_command + "\n")
    write_text(directory / "checkout_log_raw.txt", "NOT_RUN_LOCALLY: use v2_7_bugsinpy_target_replay_recovery workflow.\n")
    write_text(directory / "compile_command.txt", compile_command + "\n")
    write_text(directory / "compile_log_raw.txt", "NOT_RUN_LOCALLY: use v2_7_bugsinpy_target_replay_recovery workflow.\n")
    write_text(directory / "test_command.txt", test_command + "\n")
    write_text(directory / "test_log_raw.txt", "NOT_RUN_LOCALLY: use v2_7_bugsinpy_target_replay_recovery workflow.\n")
    write_text(directory / "failure_signature.txt", f"TARGET_REPLAY_RECOVERY_PENDING: {candidate_id}\n")
    write_json(
        directory / "target_failure_match_check.json",
        {
            "candidate": candidate_id,
            "target_failure_matched": False,
            "expected_marker": expected_marker,
            "dependency_or_import_failure_counts_as_target_replay": False,
            "promotion_status": "blocked_runtime_environment_failure",
            "reason": "Fresh dependency-recovery rerun artifact is required before target promotion.",
        },
    )
    write_json(
        directory / "gold_patch_exclusion_plan.json",
        {
            "candidate": candidate_id,
            "fixed_revision_used_at_decision_time": False,
            "gold_patch_used_at_decision_time": False,
            "policy": "Gold/fixed patches remain outcome-only.",
        },
    )
    write_json(
        directory / "replay_feasibility_result.json",
        {
            "candidate": candidate_id,
            "promotion_status": "blocked_runtime_environment_failure",
            "runtime_replay_confirmed": False,
            "failing_test_reproduced": False,
            "target_failure_matched": False,
            "blocked_reason": "v2.7 GitHub Actions recovery artifact required",
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_manifest(directory)
    return {
        "candidate": candidate_id,
        "prior_blocker": prior_blocker,
        "dependency_hint": dependency_hint,
        "promotion_status": "blocked_runtime_environment_failure",
        "target_failure_matched": False,
        "next_action": "Run v2_7_bugsinpy_target_replay_recovery workflow and ingest artifact.",
    }


def update_shareable_summary(final_count: int, gate_result: str) -> None:
    section = f"""## v2.7/v2.8 BugsInPy Target-Replay Recovery and Limited Replay Campaign

Dependency repair is runtime setup, not code repair. Target-failure matching remains mandatory. Dependency/import failures do not count as target bug replay.

- Previous target-matched count: 1 (`youtube-dl:1`).
- `black:2` recovery status: blocked pending v2.7 Linux GitHub Actions dependency rerun for `regex`.
- `black:8` recovery status: blocked pending v2.7 Linux GitHub Actions dependency rerun for `click`.
- Additional candidates attempted locally: 0; local Windows runtime cannot perform BugsInPy expansion.
- Final target-matched count: {final_count}.
- v2.8 executed: false.
- Aggregate/gate result: `{gate_result}`.

Candidate promotion is not repair success. Limited BugsInPy memory lift is not demonstrated. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.

Next required runtime action: run the `v2_7_bugsinpy_target_replay_recovery` GitHub Actions workflow, download `v2_7_bugsinpy_target_replay_recovery_artifacts`, and ingest it before any v2.8 repair scoring.
"""
    marker = "## v2.7/v2.8 BugsInPy Target-Replay Recovery and Limited Replay Campaign"
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
    parsed = load_json(V25_PARSED)
    records = parsed.get("records", []) if isinstance(parsed.get("records"), list) else []
    promoted = [
        record
        for record in records
        if record.get("promotion_status") == "promoted_ready_for_v2_5_bugsinpy_real_bug"
        and record.get("target_failure_matched") is True
    ]
    black_results = [
        write_candidate_blocker_dir(
            OUTPUT_DIR / "black_2_dependency_rerun",
            "black",
            "2",
            "ModuleNotFoundError: No module named 'regex'",
            "regex",
            "BlackTestCase.test_fmtonoff4",
        ),
        write_candidate_blocker_dir(
            OUTPUT_DIR / "black_8_dependency_rerun",
            "black",
            "8",
            "ModuleNotFoundError: No module named 'click'",
            "click",
            "BlackTestCase.test_comments7",
        ),
    ]
    final_count = len(promoted)
    gate_result = "insufficient_target_matched_bugsinpy_candidates_for_v2_8"
    write_json(
        OUTPUT_DIR / "phase_a_dependency_repair_plan.json",
        {
            "phase": "v2.7 Phase A",
            "candidates": ["black:2", "black:8"],
            "dependency_repair_is_runtime_setup_not_code_repair": True,
            "workflow_added": ".github/workflows/v2_7_bugsinpy_target_replay_recovery.yml",
            "probe_script_added": "scripts/v2_7_bugsinpy_target_replay_recovery_probe.py",
            "fixed_or_gold_patch_used_at_decision_time": False,
            "source_file_bypass_allowed": False,
        },
    )
    write_json(
        OUTPUT_DIR / "phase_a_dependency_repair_results.json",
        {
            "phase": "v2.7 Phase A",
            "local_execution_status": "blocked_runtime_environment_failure",
            "reason": "Fresh Linux GitHub Actions recovery artifact is required; local Windows workspace cannot perform BugsInPy rerun.",
            "results": black_results,
            "newly_promoted_count": 0,
        },
    )
    write_json(
        OUTPUT_DIR / "phase_b_candidate_expansion_plan.json",
        {
            "phase": "v2.7 Phase B",
            "budget": 8,
            "policy": "Discover additional BugsInPy metadata on Linux runner if Phase A leaves fewer than three target-matched candidates.",
            "local_execution_status": "blocked_runtime_environment_failure",
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_json(
        OUTPUT_DIR / "phase_b_candidate_expansion_results.json",
        {
            "phase": "v2.7 Phase B",
            "additional_candidates_attempted_locally": 0,
            "reason": "No fresh v2.7 Linux recovery artifact is available; additional BugsInPy expansion must run in the GitHub Actions recovery workflow.",
            "newly_promoted_count": 0,
        },
    )
    write_json(
        OUTPUT_DIR / "additional_candidate_attempt_matrix.json",
        {
            "attempted_count": 0,
            "bounded_budget": 8,
            "attempts": [],
            "next_action": "Run v2.7 GitHub Actions workflow to discover and attempt additional BugsInPy candidates.",
        },
    )
    write_json(
        OUTPUT_DIR / "additional_candidate_rejection_table.json",
        {
            "rejected_or_blocked_count": 0,
            "records": [],
            "blocker": "local BugsInPy runtime unavailable for expansion",
        },
    )
    write_json(
        OUTPUT_DIR / "promoted_bugsinpy_real_bug_candidate_pool.json",
        {
            "count": final_count,
            "records": promoted,
            "source": "corrected v2.5 target-failure-matched pool plus v2.7 recovery results",
        },
    )
    write_json(
        OUTPUT_DIR / "blocked_candidate_summary.json",
        {
            "blocked_count": 2,
            "records": black_results,
            "candidate_expansion_blocker": "v2.7 GitHub Actions artifact required for additional BugsInPy expansion",
        },
    )
    write_json(
        OUTPUT_DIR / "target_failure_matching_summary.json",
        {
            "previous_target_matched_count": len(promoted),
            "phase_a_new_target_matched_count": 0,
            "phase_b_new_target_matched_count": 0,
            "final_target_matched_count": final_count,
            "dependency_import_failures_count_as_target_replay": False,
            "target_failure_matching_mandatory": True,
        },
    )
    write_json(
        OUTPUT_DIR / "v2_8_execution_gate_decision.json",
        {
            "gate": "v2.8 limited BugsInPy real-bug replay execution",
            "target_matched_candidate_count": final_count,
            "minimum_required": 3,
            "execute_v2_8": False,
            "repair_scoring_run": False,
            "gate_result": gate_result,
            "next_required_action": "Run v2.7 GitHub Actions recovery workflow and ingest artifact; v2.8 remains blocked until at least three target-matched candidates exist.",
        },
    )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        f"""# v2.7/v2.8 BugsInPy Target-Replay Recovery and Limited Replay Campaign

Result: `{gate_result}`.

## Phase A

`black:2` and `black:8` now have dependency-recovery rerun plans and a Linux GitHub Actions workflow path. They are not promoted locally because no fresh recovery artifact exists yet.

## Phase B

Additional BugsInPy expansion did not run locally because the workspace lacks the required BugsInPy Linux runtime. The v2.7 workflow can perform bounded expansion on Ubuntu after Phase A.

## Phase C

Final target-matched BugsInPy candidate count remains {final_count}. The only promoted candidate is the corrected v2.5 `youtube-dl:1` target assertion replay.

## Phase D

v2.8 limited replay execution did not run. Repair scoring remains NOT RUN. Full scoring remains disallowed. Memory lift is not demonstrated. Self-maintaining software is not demonstrated.

Dependency repair is runtime setup, not code repair. Target-failure matching remains mandatory. Dependency/import failures do not count as target bug replay.
""",
    )
    update_shareable_summary(final_count, gate_result)
    write_manifest(OUTPUT_DIR)
    print("v2.7/v2.8 BugsInPy recovery and replay gate artifacts generated")
    print(f"final target-matched candidates: {final_count}")
    print(f"v2.8 executed: false")
    print(f"gate result: {gate_result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
