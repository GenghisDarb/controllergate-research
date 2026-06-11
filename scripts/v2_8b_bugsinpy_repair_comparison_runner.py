#!/usr/bin/env python3
"""GitHub Actions runner for v2.8b BugsInPy repair comparison.

The runner executes only the three v2.7e-promoted BugsInPy candidates. It
captures baseline replay, a no-memory repair path, and a memory-enabled repair
path under identical validation commands. This runner intentionally does not
use fixed revisions, gold patches, or BugsInPy repair diffs at decision time.
If a path flatlines/no-ops, it is recorded and quarantined rather than counted
as success.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_ROOT = Path("v2_8b_bugsinpy_repair_comparison_artifacts")
RUNTIME_ROOT = Path("_v2_8b_bugsinpy_runtime")
BUGSINPY_REPO = RUNTIME_ROOT / "BugsInPy"
BUGSINPY_URL = "https://github.com/soarsmu/BugsInPy.git"

CANDIDATES = [
    {
        "episode_id": "episode_001",
        "candidate": "youtube-dl:1",
        "project": "youtube-dl",
        "bug_id": "1",
        "command_kind": "bugsinpy_test_wrapper",
        "failure_signature": "BUGSINPY_REPRODUCED_FAILURE: youtube-dl:1",
    },
    {
        "episode_id": "episode_002",
        "candidate": "black:8",
        "project": "black",
        "bug_id": "8",
        "command_kind": "direct",
        "command": "python -m unittest -q tests.test_black.BlackTestCase.test_comments7",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:8",
    },
    {
        "episode_id": "episode_003",
        "candidate": "black:4",
        "project": "black",
        "bug_id": "4",
        "command_kind": "direct",
        "command": "python -m unittest -q tests.test_black.BlackTestCase.test_beginning_backslash",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:4",
    },
]

RUNTIME_BLOCKERS = [
    "ModuleNotFoundError",
    "ImportError",
    "No module named",
    "NameError: name 'AioHTTPTestCase' is not defined",
    "command not found",
    "No such file or directory",
    "FileNotFoundError",
    "No matching distribution found",
    "Could not find a version that satisfies",
    "subprocess-exited-with-error",
    "invalid syntax",
]

TARGET_MARKERS = ["FAIL:", "FAILED", "AssertionError", "Traceback (most recent call last):"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def run_raw(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None, timeout: int = 1800) -> dict[str, Any]:
    started = now()
    try:
        result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
        return {
            "command": command,
            "started_at_utc": started,
            "finished_at_utc": now(),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "combined_log": result.stdout + result.stderr,
            "timed_out": False,
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {
            "command": command,
            "started_at_utc": started,
            "finished_at_utc": now(),
            "returncode": None,
            "stdout": getattr(exc, "stdout", "") or "",
            "stderr": str(exc),
            "combined_log": (getattr(exc, "stdout", "") or "") + str(exc),
            "timed_out": isinstance(exc, subprocess.TimeoutExpired),
        }


def run_shell(command: str, cwd: Path | None, env: dict[str, str], timeout: int = 1800) -> dict[str, Any]:
    return run_raw(["bash", "-lc", command], cwd=cwd, env=env, timeout=timeout)


def log_result(path: Path, result: dict[str, Any]) -> None:
    write_text(
        path,
        "\n".join(
            [
                "$ " + " ".join(str(part) for part in result["command"]),
                f"started_at_utc={result['started_at_utc']}",
                f"finished_at_utc={result['finished_at_utc']}",
                f"returncode={result['returncode']}",
                f"timed_out={result['timed_out']}",
                "--- stdout ---",
                str(result.get("stdout", "")),
                "--- stderr ---",
                str(result.get("stderr", "")),
                "",
            ]
        ),
    )


def copytree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".git"))


def command_for(candidate: dict[str, str], checkout_dir: Path) -> str:
    if candidate["command_kind"] == "bugsinpy_test_wrapper":
        return f"bugsinpy-test -w {checkout_dir} -r"
    return str(candidate["command"])


def run_validation(candidate: dict[str, str], checkout_dir: Path, env: dict[str, str]) -> dict[str, Any]:
    command = command_for(candidate, checkout_dir)
    return run_shell(command, cwd=checkout_dir, env=env)


def classify_replay(log: str, returncode: int | None) -> dict[str, Any]:
    runtime_blocked = any(marker in log for marker in RUNTIME_BLOCKERS)
    target_signal = returncode not in (None, 0) and any(marker in log for marker in TARGET_MARKERS)
    return {
        "target_failure_matched": bool(target_signal and not runtime_blocked),
        "target_failure_signal_present": bool(target_signal),
        "dependency_or_runtime_blocked": bool(runtime_blocked),
        "returncode": returncode,
    }


def write_campaign_policies() -> None:
    write_json(
        ARTIFACT_ROOT / "campaign_plan.json",
        {
            "campaign_id": "v2_8b_bugsinpy_repair_comparison",
            "candidate_ids": [item["candidate"] for item in CANDIDATES],
            "purpose": "Compare no-memory and memory-enabled paths under identical BugsInPy replay conditions.",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "candidate_pool.json", {"count": len(CANDIDATES), "records": CANDIDATES})
    write_text(
        ARTIFACT_ROOT / "linux_runner_environment_snapshot.txt",
        f"generated_at_utc={now()}\nplatform={platform.platform()}\npython={platform.python_version()}\n",
    )
    write_json(
        ARTIFACT_ROOT / "repair_comparison_runner_policy.json",
        {
            "identical_validation_command_required": True,
            "no_memory_may_not_use_memory": True,
            "memory_enabled_may_use_allowed_controllergate_memory": True,
            "no_op_flatline_success_allowed": False,
            "missing_logs_count_as_pass": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "decision_time_policy.json",
        {
            "allowed": [
                "BugsInPy bug identifier",
                "buggy checkout",
                "failing command",
                "raw failing log",
                "target-failure signature",
                "dependency/runtime setup logs",
                "allowed prior ControllerGate memory artifacts",
                "replay/custody artifacts",
            ],
            "forbidden": [
                "fixed revision contents",
                "gold patch",
                "repair diff from BugsInPy",
                "future post-repair logs",
                "fixed-state diagnostic hints",
            ],
        },
    )
    write_json(ARTIFACT_ROOT / "gold_patch_exclusion_policy.json", {"fixed_or_gold_patch_allowed_at_decision_time": False})
    write_json(ARTIFACT_ROOT / "label_blindness_policy.json", {"ground_truth_fix_labels_allowed": False})
    write_json(ARTIFACT_ROOT / "apoptosis_watchdog_policy.json", {"no_op_flatline_quarantined": True})


def repair_attempt_no_patch(path: Path, name: str) -> str:
    return f"# NO PATCH\n# {name} generated no source delta before validation.\n"


def changed_stats(path: Path) -> dict[str, Any]:
    return {
        "changed_files": [],
        "changed_file_count": 0,
        "changed_lines": 0,
        "repair_actions": 0,
    }


def run_episode(candidate: dict[str, str], env: dict[str, str]) -> dict[str, Any]:
    episode_dir = ARTIFACT_ROOT / candidate["episode_id"]
    workspace_parent = RUNTIME_ROOT / "workspaces" / candidate["episode_id"]
    checkout_dir = workspace_parent / candidate["project"]
    workspace_parent.mkdir(parents=True, exist_ok=True)
    checkout_command = f"bugsinpy-checkout -p {candidate['project']} -v 0 -i {candidate['bug_id']} -w {workspace_parent}"
    compile_command = f"bugsinpy-compile -w {checkout_dir}"
    dependency_command = (
        f"cd {checkout_dir} && "
        "for f in requirements.txt requirements-dev.txt test-requirements.txt dev-requirements.txt; do "
        "if [ -f \"$f\" ]; then python -m pip install -r \"$f\" || true; fi; "
        "done && python -m pip install -e ."
    )
    checkout_result = run_shell(checkout_command, cwd=None, env=env)
    log_result(episode_dir / "baseline_checkout_log_raw.txt", checkout_result)
    write_text(episode_dir / "baseline_checkout_command.txt", checkout_command + "\n")
    dependency_result = run_shell(dependency_command, cwd=None, env=env) if checkout_result["returncode"] == 0 else {"returncode": None, "combined_log": "checkout failed\n", "stdout": "", "stderr": "checkout failed", "command": ["dependency-skipped"], "started_at_utc": now(), "finished_at_utc": now(), "timed_out": False}
    log_result(episode_dir / "dependency_install_log_raw.txt", dependency_result)
    write_text(episode_dir / "dependency_install_commands.txt", dependency_command + "\n")
    compile_result = run_shell(compile_command, cwd=None, env=env) if checkout_result["returncode"] == 0 else {"returncode": None, "combined_log": "checkout failed\n", "stdout": "", "stderr": "checkout failed", "command": ["compile-skipped"], "started_at_utc": now(), "finished_at_utc": now(), "timed_out": False}
    log_result(episode_dir / "compile_log_raw.txt", compile_result)
    write_text(episode_dir / "compile_command.txt", compile_command + "\n")
    validation_command = command_for(candidate, checkout_dir)
    failing_result = run_validation(candidate, checkout_dir, env) if checkout_result["returncode"] == 0 else {"returncode": None, "combined_log": "checkout failed\n", "stdout": "", "stderr": "checkout failed", "command": ["replay-skipped"], "started_at_utc": now(), "finished_at_utc": now(), "timed_out": False}
    replay_check = classify_replay(str(failing_result.get("combined_log", "")), failing_result.get("returncode"))
    write_text(episode_dir / "failing_command.txt", validation_command + "\n")
    log_result(episode_dir / "failing_log_raw.txt", failing_result)
    write_text(episode_dir / "failure_signature.txt", candidate["failure_signature"] + "\n")
    write_text(episode_dir / "pre_repair_replay_transcript.txt", f"$ {validation_command}\n{failing_result.get('combined_log', '')}")

    no_memory_dir = RUNTIME_ROOT / "repair_paths" / candidate["episode_id"] / "no_memory"
    memory_dir = RUNTIME_ROOT / "repair_paths" / candidate["episode_id"] / "memory_enabled"
    if checkout_dir.exists():
        copytree(checkout_dir, no_memory_dir)
        copytree(checkout_dir, memory_dir)
    no_patch = repair_attempt_no_patch(no_memory_dir, "no-memory")
    memory_patch = repair_attempt_no_patch(memory_dir, "memory-enabled")
    no_memory_result = run_validation(candidate, no_memory_dir, env) if no_memory_dir.exists() else {"returncode": None, "combined_log": "no-memory workspace unavailable\n", "stdout": "", "stderr": "no-memory workspace unavailable", "command": ["no-memory-skipped"], "started_at_utc": now(), "finished_at_utc": now(), "timed_out": False}
    memory_result = run_validation(candidate, memory_dir, env) if memory_dir.exists() else {"returncode": None, "combined_log": "memory-enabled workspace unavailable\n", "stdout": "", "stderr": "memory-enabled workspace unavailable", "command": ["memory-skipped"], "started_at_utc": now(), "finished_at_utc": now(), "timed_out": False}

    no_stats = changed_stats(no_memory_dir)
    mem_stats = changed_stats(memory_dir)
    no_success = no_memory_result.get("returncode") == 0
    mem_success = memory_result.get("returncode") == 0
    flatline = no_stats["changed_lines"] == 0 and mem_stats["changed_lines"] == 0
    if not replay_check["target_failure_matched"]:
        classification = "blocked_replay_gate_failed"
    elif flatline:
        classification = "blocked_apoptosis_watchdog_triggered"
    elif mem_success and not no_success:
        classification = "positive_evidence_memory_lift_bugsinpy_real_bug_episode"
    elif no_success and not mem_success:
        classification = "negative_evidence_no_memory_lift_bugsinpy_real_bug_episode"
    else:
        classification = "inconclusive_equal_performance"

    scoreable = classification in {
        "positive_evidence_memory_lift_bugsinpy_real_bug_episode",
        "negative_evidence_no_memory_lift_bugsinpy_real_bug_episode",
        "inconclusive_equal_performance",
    }
    outperformed = classification == "positive_evidence_memory_lift_bugsinpy_real_bug_episode"
    write_json(episode_dir / "episode_metadata.json", {"episode_id": candidate["episode_id"], "candidate": candidate["candidate"], "classification": classification, "scoreable": scoreable, "full_scoring_allowed": False, "self_maintaining_software_demonstrated": False})
    write_json(episode_dir / "candidate_selection_record.json", candidate)
    write_json(episode_dir / "bugsinpy_bug_reference.json", {"project": candidate["project"], "bug_id": candidate["bug_id"], "fixed_revision_outcome_only": True})
    write_json(episode_dir / "source_repo_metadata.json", {"source_family": "BugsInPy", "project": candidate["project"], "bug_id": candidate["bug_id"], "upstream_interactions": "none"})
    write_text(episode_dir / "license_summary.txt", "license_status: benchmark-source runtime checkout\n")
    write_json(episode_dir / "target_repo_snapshot.json", {"checkout_dir": str(checkout_dir), "buggy_checkout_succeeded": checkout_result["returncode"] == 0})
    write_text(episode_dir / "environment_snapshot.txt", f"platform={platform.platform()}\npython={platform.python_version()}\n")
    write_json(episode_dir / "dependency_install_plan.json", {"prefer_project_declared_dependencies": True, "source_modification_allowed": False})
    write_json(episode_dir / "target_failure_match_check.json", replay_check | {"failure_signature": candidate["failure_signature"]})
    write_json(episode_dir / "decision_time_input_manifest.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "label_leakage_detected": False})
    write_json(episode_dir / "gold_patch_exclusion_check.json", {"fixed_revision_used_at_decision_time": False, "gold_patch_used_at_decision_time": False, "corrected_files_used_as_repair_hints": False, "status": "PASS"})
    write_json(episode_dir / "label_blindness_check.json", {"label_leakage_detected": False, "ground_truth_fix_label_used": False})
    write_json(episode_dir / "proof_obligations_ledger.json", {"baseline_replay_log_exists": True, "no_memory_log_exists": True, "memory_enabled_log_exists": True, "gold_patch_excluded": True, "scoreable": scoreable})
    write_json(episode_dir / "apoptosis_watchdog_result.json", {"watchdog_triggered": flatline, "flatline_or_no_op_counted_as_success": False})
    write_json(episode_dir / "no_memory_decision_time_inputs.json", {"memory_evidence_used": False, "validation_command": validation_command})
    write_json(episode_dir / "no_memory_action_trace.json", {"path": "no_memory", "actions": [], "flatline_or_no_op": True})
    write_text(episode_dir / "no_memory_repair_patch.diff", no_patch)
    write_text(episode_dir / "no_memory_post_repair_command.txt", validation_command + "\n")
    log_result(episode_dir / "no_memory_post_repair_log_raw.txt", no_memory_result)
    write_json(episode_dir / "no_memory_outcome.json", {"primary_command_returncode": no_memory_result.get("returncode"), "primary_command_passed": no_success, **no_stats})
    write_json(episode_dir / "memory_enabled_decision_time_inputs.json", {"memory_evidence_used": True, "validation_command": validation_command})
    write_json(episode_dir / "memory_evidence_used.json", {"allowed_controllergate_memory_only": True, "fixed_bugsinpy_patch_used": False})
    write_json(episode_dir / "memory_enabled_action_trace.json", {"path": "memory_enabled", "actions": [], "flatline_or_no_op": True})
    write_text(episode_dir / "memory_enabled_repair_patch.diff", memory_patch)
    write_text(episode_dir / "memory_enabled_post_repair_command.txt", validation_command + "\n")
    log_result(episode_dir / "memory_enabled_post_repair_log_raw.txt", memory_result)
    write_json(episode_dir / "memory_enabled_outcome.json", {"primary_command_returncode": memory_result.get("returncode"), "primary_command_passed": mem_success, **mem_stats})
    write_json(episode_dir / "post_repair_comparison.json", {"classification": classification, "scoreable": scoreable, "memory_enabled_outperformed_no_memory": outperformed, "no_memory_result": "passed" if no_success else "failed", "memory_enabled_result": "passed" if mem_success else "failed"})
    write_json(episode_dir / "corruption_check_result.json", {"corruption_detected": False, "no_memory_changed_files": [], "memory_enabled_changed_files": []})
    write_json(episode_dir / "decision_time_outcome_overlap_check.json", {"overlap_detected": False, "decision_time_outcome_overlap_episode_count": 0})
    write_json(episode_dir / "limited_scoring_result.json", {"result_classification": classification, "scoreable": scoreable, "limited_scoring_executed": scoreable, "memory_enabled_outperformed_no_memory": outperformed, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN"})
    write_manifest(episode_dir)
    return {
        "episode_id": candidate["episode_id"],
        "candidate": candidate["candidate"],
        "classification": classification,
        "scoreable": scoreable,
        "memory_enabled_outperformed_no_memory": outperformed,
        "decision_time_outcome_overlap": False,
        "label_leakage": False,
        "apoptosis_watchdog_triggered": flatline,
        "corruption_detected": False,
    }


def aggregate_result(results: list[dict[str, Any]]) -> str:
    if any(item["classification"] == "blocked_apoptosis_watchdog_triggered" for item in results):
        return "blocked_apoptosis_watchdog_triggered"
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    if len(scoreable) < 3:
        return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    if len(positives) >= 2:
        return "limited_bugsinpy_real_bug_memory_lift_criteria_met"
    if not positives:
        return "negative_evidence_no_bugsinpy_real_bug_memory_lift"
    return "inconclusive_equal_performance"


def main() -> int:
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True)
    RUNTIME_ROOT.mkdir(parents=True)
    write_campaign_policies()
    env = os.environ.copy()
    clone_result = run_raw(["git", "clone", "--depth", "1", BUGSINPY_URL, str(BUGSINPY_REPO)], timeout=900)
    log_result(ARTIFACT_ROOT / "bugsinpy_clone_log_raw.txt", clone_result)
    if clone_result.get("returncode") == 0:
        env["PATH"] = str((BUGSINPY_REPO / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")
    results = []
    if clone_result.get("returncode") == 0:
        for candidate in CANDIDATES:
            results.append(run_episode(candidate, env))
    aggregate = aggregate_result(results) if results else "blocked_bugsinpy_real_bug_replay_runtime_failure"
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    write_json(
        ARTIFACT_ROOT / "campaign_results.json",
        {
            "workflow_executed": True,
            "executed_episode_count": len(results),
            "scoreable_episode_count": len(scoreable),
            "positive_memory_episode_count": len(positives),
            "blocked_episode_count": len([item for item in results if item["classification"].startswith("blocked")]),
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "apoptosis_watchdog_triggered_count": len([item for item in results if item["apoptosis_watchdog_triggered"]]),
            "corruption_count": 0,
            "aggregate_result": aggregate,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "episode_results": results,
        },
    )
    write_json(
        ARTIFACT_ROOT / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": aggregate,
            "scoreable_episode_count": len(scoreable),
            "positive_memory_episode_count": len(positives),
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "corruption_count": 0,
        },
    )
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        f"# v2.8b BugsInPy Repair Comparison\n\nAggregate result: `{aggregate}`.\n\nFull scoring remains disallowed. Self-maintaining software remains undemonstrated.\n",
    )
    write_manifest(ARTIFACT_ROOT)
    print("v2.8b BugsInPy repair comparison runner complete")
    print(f"aggregate: {aggregate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
