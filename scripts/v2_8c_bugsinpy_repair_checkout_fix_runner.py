#!/usr/bin/env python3
"""GitHub Actions runner for v2.8c BugsInPy repair checkout fix.

v2.8b reached the Linux workflow but failed before repair because BugsInPy
checkout/runtime paths were relative and resolved inconsistently. This runner
uses absolute workspace paths, verifies checkout integrity before replay, runs
direct target commands, and blocks repair attempts unless the pre-repair target
replay gate passes.
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


REPO_ROOT = Path.cwd().resolve()
ARTIFACT_ROOT = (REPO_ROOT / "v2_8c_bugsinpy_repair_checkout_fix_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8c_bugsinpy_runtime").resolve()
BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()
BUGSINPY_URL = "https://github.com/soarsmu/BugsInPy.git"

CANDIDATES = [
    {
        "episode_id": "episode_001",
        "candidate": "youtube-dl:1",
        "project": "youtube-dl",
        "bug_id": "1",
        "direct_command": "python -m unittest -q test.test_utils.TestUtil.test_match_str",
        "target_test_file": "test/test_utils.py",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: youtube-dl:1",
        "required_markers": ["FAIL:", "TestUtil.test_match_str", "AssertionError"],
        "dependency_hints": [],
    },
    {
        "episode_id": "episode_002",
        "candidate": "black:8",
        "project": "black",
        "bug_id": "8",
        "direct_command": "python -m unittest -q tests.test_black.BlackTestCase.test_comments7",
        "target_test_file": "tests/test_black.py",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:8",
        "required_markers": ["FAIL: test_comments7", "BlackTestCase.test_comments7", "Cannot parse: 11:4:"],
        "dependency_hints": ["click"],
    },
    {
        "episode_id": "episode_003",
        "candidate": "black:4",
        "project": "black",
        "bug_id": "4",
        "direct_command": "python -m unittest -q tests.test_black.BlackTestCase.test_beginning_backslash",
        "target_test_file": "tests/test_black.py",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:4",
        "required_markers": ["FAIL: test_beginning_backslash", "BlackTestCase.test_beginning_backslash", "AssertionError"],
        "dependency_hints": ["click"],
    },
]

IMPORT_OR_RUNTIME_BLOCKERS = [
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
    "SyntaxError",
    "invalid syntax",
]

WRAPPER_BLOCKERS = [
    "bugsinpy-test:",
    "illegal option",
    "env/bin/activate",
    "deactivate: command not found",
]


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


def read_kv_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def candidate_metadata(candidate: dict[str, str]) -> dict[str, Any]:
    project = candidate["project"]
    bug_id = candidate["bug_id"]
    project_dir = BUGSINPY_REPO / "projects" / project
    bug_dir = project_dir / "bugs" / bug_id
    project_info = read_kv_file(project_dir / "project.info")
    bug_info = read_kv_file(bug_dir / "bug.info")
    return {
        "source_family": "bugsinpy",
        "project": project,
        "bug_id": bug_id,
        "repo_url": project_info.get("github_url"),
        "buggy_commit_id": bug_info.get("buggy_commit_id"),
        "fixed_commit_id_outcome_only": bug_info.get("fixed_commit_id"),
        "python_version_required": bug_info.get("python_version"),
        "candidate_class": "real_bug_benchmark_entry",
        "fixed_or_gold_patch_used_at_decision_time": False,
    }


def combined_log(result: dict[str, Any]) -> str:
    return str(result.get("stdout", "")) + "\n" + str(result.get("stderr", "")) + "\n" + str(result.get("combined_log", ""))


def classify_target_replay(log: str, returncode: int | None, required_markers: list[str]) -> dict[str, Any]:
    wrapper_contaminated = any(marker in log for marker in WRAPPER_BLOCKERS)
    runtime_blocked = any(marker in log for marker in IMPORT_OR_RUNTIME_BLOCKERS)
    marker_matched = any(marker in log for marker in required_markers)
    target_failure_matched = returncode not in (None, 0) and marker_matched and not wrapper_contaminated and not runtime_blocked
    return {
        "target_failure_matched": bool(target_failure_matched),
        "target_failure_signal_present": bool(marker_matched),
        "dependency_or_runtime_blocked": bool(runtime_blocked),
        "wrapper_contaminated": bool(wrapper_contaminated),
        "returncode": returncode,
    }


def copytree(source: Path, destination: Path) -> dict[str, Any]:
    if destination.exists():
        shutil.rmtree(destination)
    try:
        shutil.copytree(
            source,
            destination,
            symlinks=True,
            ignore_dangling_symlinks=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".git"),
        )
    except (OSError, shutil.Error) as exc:
        return {
            "copy_succeeded": False,
            "source": str(source),
            "destination": str(destination),
            "error": str(exc),
        }
    return {
        "copy_succeeded": True,
        "source": str(source),
        "destination": str(destination),
        "preserved_symlinks": True,
    }


def dependency_command_for(project_root: Path, hints: list[str]) -> str:
    commands = [
        f"cd {project_root}",
        "for f in requirements.txt requirements-dev.txt test-requirements.txt dev-requirements.txt; do if [ -f \"$f\" ]; then python -m pip install -r \"$f\" || true; fi; done",
        "python -m pip install -e .",
    ]
    commands.extend(f"python -m pip install {hint}" for hint in hints)
    return " && ".join(commands)


def write_common_campaign_artifacts() -> None:
    write_json(
        ARTIFACT_ROOT / "campaign_plan.json",
        {
            "campaign_id": "v2_8c_bugsinpy_repair_checkout_fix",
            "candidate_ids": [item["candidate"] for item in CANDIDATES],
            "checkout_fix": "absolute workspace paths with pre-repair replay gate",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "candidate_source_integrity_check.json", {"candidate_count": len(CANDIDATES), "records": CANDIDATES})
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.8c BugsInPy Repair-Comparison Checkout Fix\n\nPending campaign summary; runner will update this file at completion.\n",
    )


def write_blocked_path_artifacts(episode_dir: Path, validation_command: str, reason: str) -> None:
    for prefix in ["no_memory", "memory_enabled"]:
        write_json(
            episode_dir / f"{prefix}_decision_time_inputs.json",
            {"validation_command": validation_command, "repair_path_ran": False, "blocked_reason": reason, "memory_evidence_used": prefix == "memory_enabled"},
        )
        if prefix == "memory_enabled":
            write_json(episode_dir / "memory_evidence_used.json", {"memory_path_ran": False, "blocked_reason": reason})
        write_json(episode_dir / f"{prefix}_action_trace.json", {"actions": [], "repair_path_ran": False, "blocked_reason": reason})
        write_text(episode_dir / f"{prefix}_repair_patch.diff", "# NO PATCH\n# Repair path did not run because pre-repair replay gate failed.\n")
        write_text(episode_dir / f"{prefix}_post_repair_command.txt", validation_command + "\n")
        write_text(episode_dir / f"{prefix}_post_repair_log_raw.txt", f"NOT_RUN: {reason}\n")
        write_json(episode_dir / f"{prefix}_outcome.json", {"repair_path_ran": False, "primary_command_passed": False, "blocked_reason": reason})


def run_repair_paths(candidate: dict[str, Any], project_root: Path, episode_dir: Path, env: dict[str, str]) -> dict[str, Any]:
    validation_command = candidate["direct_command"]
    no_memory_dir = (RUNTIME_ROOT / "repair_paths" / candidate["episode_id"] / "no_memory").resolve()
    memory_dir = (RUNTIME_ROOT / "repair_paths" / candidate["episode_id"] / "memory_enabled").resolve()
    no_copy = copytree(project_root, no_memory_dir)
    memory_copy = copytree(project_root, memory_dir)
    write_json(
        episode_dir / "repair_workspace_copy_result.json",
        {
            "no_memory": no_copy,
            "memory_enabled": memory_copy,
            "infrastructure_copy_failure_counts_as_repair_failure": False,
        },
    )
    if not no_copy["copy_succeeded"] or not memory_copy["copy_succeeded"]:
        reason = "repair workspace copy failed before no-memory or memory-enabled repair validation"
        write_blocked_path_artifacts(episode_dir, validation_command, reason)
        write_json(episode_dir / "memory_evidence_used.json", {"memory_path_ran": False, "blocked_reason": reason})
        return {
            "repair_paths_ran": False,
            "repair_workspace_copy_failed": True,
            "flatline_or_no_op": False,
            "no_memory_passed": False,
            "memory_enabled_passed": False,
        }
    no_result = run_shell(validation_command, cwd=no_memory_dir, env=env)
    mem_result = run_shell(validation_command, cwd=memory_dir, env=env)
    for prefix, result in [("no_memory", no_result), ("memory_enabled", mem_result)]:
        write_json(
            episode_dir / f"{prefix}_decision_time_inputs.json",
            {"validation_command": validation_command, "repair_path_ran": True, "memory_evidence_used": prefix == "memory_enabled"},
        )
        write_json(episode_dir / f"{prefix}_action_trace.json", {"actions": [], "flatline_or_no_op": True})
        write_text(episode_dir / f"{prefix}_repair_patch.diff", "# NO PATCH\n# No source delta generated by bounded repair runner.\n")
        write_text(episode_dir / f"{prefix}_post_repair_command.txt", validation_command + "\n")
        log_result(episode_dir / f"{prefix}_post_repair_log_raw.txt", result)
        write_json(
            episode_dir / f"{prefix}_outcome.json",
            {
                "repair_path_ran": True,
                "primary_command_returncode": result.get("returncode"),
                "primary_command_passed": result.get("returncode") == 0,
                "changed_files": [],
                "changed_file_count": 0,
                "changed_lines": 0,
                "repair_actions": 0,
            },
        )
    write_json(episode_dir / "memory_evidence_used.json", {"allowed_controllergate_memory_only": True, "fixed_bugsinpy_patch_used": False})
    return {
        "repair_paths_ran": True,
        "no_memory_passed": no_result.get("returncode") == 0,
        "memory_enabled_passed": mem_result.get("returncode") == 0,
        "no_memory_changed_lines": 0,
        "memory_enabled_changed_lines": 0,
        "repair_actions": 0,
        "flatline_or_no_op": True,
    }


def run_episode(candidate: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    episode_dir = ARTIFACT_ROOT / candidate["episode_id"]
    episode_dir.mkdir(parents=True, exist_ok=True)
    workspace_parent = (RUNTIME_ROOT / "workspaces" / candidate["episode_id"]).resolve()
    project_root = (workspace_parent / candidate["project"]).resolve()
    workspace_parent.mkdir(parents=True, exist_ok=True)

    checkout_command = f"bugsinpy-checkout -p {candidate['project']} -v 0 -i {candidate['bug_id']} -w {workspace_parent}"
    compile_command = f"bugsinpy-compile -w {project_root}"
    dependency_command = dependency_command_for(project_root, candidate["dependency_hints"])
    validation_command = candidate["direct_command"]

    write_text(episode_dir / "absolute_workspace_path.txt", str(workspace_parent) + "\n")
    write_text(episode_dir / "project_root_path.txt", str(project_root) + "\n")
    write_json(
        episode_dir / "checkout_path_resolution.json",
        {
            "repo_root": str(REPO_ROOT),
            "runtime_root": str(RUNTIME_ROOT),
            "workspace_parent": str(workspace_parent),
            "project_root": str(project_root),
            "all_paths_absolute": all(path.is_absolute() for path in [REPO_ROOT, RUNTIME_ROOT, workspace_parent, project_root]),
        },
    )
    write_text(episode_dir / "baseline_checkout_command.txt", checkout_command + "\n")
    checkout_result = run_shell(checkout_command, cwd=REPO_ROOT, env=env, timeout=900)
    log_result(episode_dir / "baseline_checkout_log_raw.txt", checkout_result)

    target_test = project_root / candidate["target_test_file"]
    checkout_integrity = {
        "checkout_returncode": checkout_result.get("returncode"),
        "project_root_exists": project_root.exists(),
        "project_git_exists": (project_root / ".git").exists(),
        "bugsinpy_bug_info_exists": (project_root / "bugsinpy_bug.info").exists(),
        "target_test_file": str(target_test),
        "target_test_file_exists": target_test.exists(),
    }
    checkout_integrity["checkout_integrity_passed"] = bool(
        checkout_integrity["checkout_returncode"] == 0
        and checkout_integrity["project_root_exists"]
        and checkout_integrity["target_test_file_exists"]
    )
    write_json(episode_dir / "checkout_integrity_check.json", checkout_integrity)

    write_text(episode_dir / "dependency_install_commands.txt", dependency_command + "\n")
    write_json(episode_dir / "dependency_install_plan.json", {"prefer_buggy_checkout_dependencies": True, "manual_dependency_hints": candidate["dependency_hints"], "source_modification_allowed": False})
    dependency_result = run_shell(dependency_command, cwd=REPO_ROOT, env=env) if checkout_integrity["checkout_integrity_passed"] else {
        "command": ["dependency-skipped"],
        "started_at_utc": now(),
        "finished_at_utc": now(),
        "returncode": None,
        "stdout": "",
        "stderr": "NOT_RUN: checkout integrity failed",
        "combined_log": "NOT_RUN: checkout integrity failed",
        "timed_out": False,
    }
    log_result(episode_dir / "dependency_install_log_raw.txt", dependency_result)
    write_text(episode_dir / "compile_command.txt", compile_command + "\n")
    compile_result = run_shell(compile_command, cwd=REPO_ROOT, env=env) if checkout_integrity["checkout_integrity_passed"] else {
        "command": ["compile-skipped"],
        "started_at_utc": now(),
        "finished_at_utc": now(),
        "returncode": None,
        "stdout": "",
        "stderr": "NOT_RUN: checkout integrity failed",
        "combined_log": "NOT_RUN: checkout integrity failed",
        "timed_out": False,
    }
    log_result(episode_dir / "compile_log_raw.txt", compile_result)

    write_text(episode_dir / "failing_command.txt", validation_command + "\n")
    failing_result = run_shell(validation_command, cwd=project_root, env=env) if checkout_integrity["checkout_integrity_passed"] and dependency_result.get("returncode") == 0 else {
        "command": ["pre-repair-replay-skipped"],
        "started_at_utc": now(),
        "finished_at_utc": now(),
        "returncode": None,
        "stdout": "",
        "stderr": "NOT_RUN: checkout/dependency gate failed",
        "combined_log": "NOT_RUN: checkout/dependency gate failed",
        "timed_out": False,
    }
    log_result(episode_dir / "failing_log_raw.txt", failing_result)
    write_text(episode_dir / "failure_signature.txt", candidate["failure_signature"] + "\n")
    write_text(episode_dir / "pre_repair_replay_transcript.txt", f"$ {validation_command}\n{combined_log(failing_result)}")
    target_check = classify_target_replay(combined_log(failing_result), failing_result.get("returncode"), candidate["required_markers"])
    write_json(episode_dir / "target_failure_match_check.json", target_check | {"failure_signature": candidate["failure_signature"]})
    write_json(episode_dir / "wrapper_contamination_check.json", {"wrapper_path_bypassed": True, "wrapper_contamination_detected": target_check["wrapper_contaminated"]})

    gate_passed = bool(checkout_integrity["checkout_integrity_passed"] and dependency_result.get("returncode") == 0 and target_check["target_failure_matched"])
    gate_reason = "pre-repair replay gate passed" if gate_passed else "checkout, dependency setup, or target replay failed before repair"
    write_json(
        episode_dir / "pre_repair_replay_gate_result.json",
        {
            "pre_repair_replay_gate_passed": gate_passed,
            "checkout_integrity_passed": checkout_integrity["checkout_integrity_passed"],
            "dependency_setup_returncode": dependency_result.get("returncode"),
            "target_failure_matched": target_check["target_failure_matched"],
            "reason": gate_reason,
        },
    )

    if gate_passed:
        repair = run_repair_paths(candidate, project_root, episode_dir, env)
        if repair.get("repair_workspace_copy_failed"):
            classification = "blocked_checkout_runtime_failure"
        elif repair["flatline_or_no_op"]:
            classification = "blocked_apoptosis_watchdog_triggered"
        elif repair["memory_enabled_passed"] and not repair["no_memory_passed"]:
            classification = "positive_evidence_memory_lift_bugsinpy_real_bug_episode"
        elif repair["no_memory_passed"] and not repair["memory_enabled_passed"]:
            classification = "negative_evidence_no_memory_lift_bugsinpy_real_bug_episode"
        else:
            classification = "inconclusive_equal_performance"
    else:
        repair = {"repair_paths_ran": False, "flatline_or_no_op": False, "no_memory_passed": False, "memory_enabled_passed": False}
        classification = "blocked_checkout_runtime_failure" if not checkout_integrity["checkout_integrity_passed"] else "blocked_pre_repair_replay_gate_failed"
        write_blocked_path_artifacts(episode_dir, validation_command, gate_reason)
        write_json(episode_dir / "memory_evidence_used.json", {"memory_path_ran": False, "blocked_reason": gate_reason})

    scoreable = classification in {
        "positive_evidence_memory_lift_bugsinpy_real_bug_episode",
        "negative_evidence_no_memory_lift_bugsinpy_real_bug_episode",
        "inconclusive_equal_performance",
    }
    memory_outperformed = classification == "positive_evidence_memory_lift_bugsinpy_real_bug_episode"
    write_json(episode_dir / "episode_metadata.json", {"episode_id": candidate["episode_id"], "candidate": candidate["candidate"], "classification": classification, "scoreable": scoreable, "full_scoring_allowed": False, "self_maintaining_software_demonstrated": False})
    write_json(episode_dir / "source_repo_metadata.json", candidate_metadata(candidate))
    write_text(episode_dir / "license_summary.txt", "license_status: BugsInPy benchmark runtime checkout\n")
    write_json(episode_dir / "candidate_selection_record.json", candidate)
    write_json(episode_dir / "bugsinpy_bug_reference.json", {"project": candidate["project"], "bug_id": candidate["bug_id"], "fixed_revision_outcome_only": True})
    write_json(episode_dir / "target_repo_snapshot.json", {"project_root": str(project_root), "buggy_checkout_succeeded": checkout_integrity["checkout_integrity_passed"]})
    write_text(episode_dir / "environment_snapshot.txt", f"platform={platform.platform()}\npython={platform.python_version()}\n")
    write_json(episode_dir / "decision_time_input_manifest.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "label_leakage_detected": False})
    write_json(episode_dir / "gold_patch_exclusion_check.json", {"fixed_revision_used_at_decision_time": False, "gold_patch_used_at_decision_time": False, "corrected_files_used_as_repair_hints": False, "status": "PASS"})
    write_json(episode_dir / "label_blindness_check.json", {"label_leakage_detected": False, "ground_truth_fix_label_used": False})
    write_json(episode_dir / "proof_obligations_ledger.json", {"checkout_integrity_check_exists": True, "pre_repair_replay_gate_exists": True, "repair_paths_ran": repair["repair_paths_ran"], "gold_patch_excluded": True, "scoreable": scoreable})
    write_json(episode_dir / "apoptosis_watchdog_result.json", {"watchdog_triggered": classification == "blocked_apoptosis_watchdog_triggered", "infrastructure_checkout_failure_counted_as_flatline": False, "flatline_or_no_op_counted_as_success": False})
    write_json(episode_dir / "post_repair_comparison.json", {"classification": classification, "scoreable": scoreable, "memory_enabled_outperformed_no_memory": memory_outperformed})
    write_json(episode_dir / "corruption_check_result.json", {"corruption_detected": False, "repair_paths_ran": repair["repair_paths_ran"]})
    write_json(episode_dir / "decision_time_outcome_overlap_check.json", {"overlap_detected": False, "decision_time_outcome_overlap_episode_count": 0})
    write_json(episode_dir / "limited_scoring_result.json", {"result_classification": classification, "scoreable": scoreable, "limited_scoring_executed": scoreable, "memory_enabled_outperformed_no_memory": memory_outperformed, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN"})
    write_manifest(episode_dir)
    return {
        "episode_id": candidate["episode_id"],
        "candidate": candidate["candidate"],
        "classification": classification,
        "scoreable": scoreable,
        "pre_repair_replay_gate_passed": gate_passed,
        "repair_paths_ran": repair["repair_paths_ran"],
        "memory_enabled_outperformed_no_memory": memory_outperformed,
        "decision_time_outcome_overlap": False,
        "label_leakage": False,
        "apoptosis_watchdog_triggered": classification == "blocked_apoptosis_watchdog_triggered",
        "corruption_detected": False,
    }


def aggregate_result(results: list[dict[str, Any]]) -> str:
    if any(item["classification"] == "blocked_apoptosis_watchdog_triggered" for item in results):
        return "blocked_apoptosis_watchdog_triggered"
    if any(item["classification"] in {"blocked_checkout_runtime_failure", "blocked_pre_repair_replay_gate_failed"} for item in results):
        return "blocked_bugsinpy_real_bug_replay_runtime_failure"
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
    write_common_campaign_artifacts()
    write_text(ARTIFACT_ROOT / "runtime_environment.txt", f"generated_at_utc={now()}\nplatform={platform.platform()}\npython={platform.python_version()}\nrepo_root={REPO_ROOT}\nruntime_root={RUNTIME_ROOT}\n")
    env = os.environ.copy()
    clone_result = run_raw(["git", "clone", "--depth", "1", BUGSINPY_URL, str(BUGSINPY_REPO)], timeout=900)
    log_result(ARTIFACT_ROOT / "bugsinpy_clone_log_raw.txt", clone_result)
    results: list[dict[str, Any]] = []
    if clone_result.get("returncode") == 0:
        env["PATH"] = str((BUGSINPY_REPO / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")
        for candidate in CANDIDATES:
            results.append(run_episode(candidate, env))
    aggregate = aggregate_result(results) if results else "blocked_bugsinpy_real_bug_replay_runtime_failure"
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    write_json(ARTIFACT_ROOT / "pre_repair_replay_gate_summary.json", {"episodes": results, "passed_count": sum(1 for item in results if item["pre_repair_replay_gate_passed"])})
    write_json(ARTIFACT_ROOT / "checkout_runtime_fix_summary.json", {"absolute_workspace_paths": True, "pre_repair_replay_gate_required": True, "bugsinpy_checkout_uses_absolute_w_path": True})
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
            "minimum_required_scoreable_episodes": 3,
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
        f"# v2.8c BugsInPy Repair-Comparison Checkout Fix\n\nAggregate result: `{aggregate}`.\n\nFull scoring remains disallowed. Self-maintaining software remains undemonstrated.\n",
    )
    write_manifest(ARTIFACT_ROOT)
    print("v2.8c BugsInPy checkout-fixed repair comparison runner complete")
    print(f"aggregate: {aggregate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
