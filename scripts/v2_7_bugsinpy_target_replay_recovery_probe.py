#!/usr/bin/env python3
"""GitHub Actions BugsInPy target replay recovery probe for v2.7.

This script is intended for the Ubuntu GitHub Actions runner. It retries the
two Black candidates that were blocked by dependency/import failures, records
candidate-specific dependency setup as runtime setup rather than repair, and
then attempts a bounded BugsInPy metadata expansion if fewer than three
target-matched candidates exist.

Fixed/gold patches are never decision-time inputs.
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


ARTIFACT_ROOT = Path("v2_7_bugsinpy_target_replay_recovery_artifacts")
RUNTIME_ROOT = Path("_v2_7_bugsinpy_runtime")
BUGSINPY_REPO = RUNTIME_ROOT / "BugsInPy"
BUGSINPY_URL = "https://github.com/soarsmu/BugsInPy.git"

IMPORT_BLOCKERS = [
    "ModuleNotFoundError",
    "ImportError: Failed to import test module",
    "No module named",
    "command not found",
    "No such file or directory",
]

PHASE_A_CANDIDATES = [
    {
        "dir_name": "black_2_dependency_rerun",
        "project": "black",
        "bug_id": "2",
        "dependency_hint": "regex",
        "expected_markers": ["FAIL: test_fmtonoff4", "BlackTestCase.test_fmtonoff4"],
        "prior_blocker": "ModuleNotFoundError: No module named 'regex'",
    },
    {
        "dir_name": "black_8_dependency_rerun",
        "project": "black",
        "bug_id": "8",
        "dependency_hint": "click",
        "expected_markers": ["FAIL: test_comments7", "BlackTestCase.test_comments7"],
        "prior_blocker": "ModuleNotFoundError: No module named 'click'",
    },
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
            "timed_out": False,
        }
    except FileNotFoundError as exc:
        return {
            "command": command,
            "started_at_utc": started,
            "finished_at_utc": now(),
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "started_at_utc": started,
            "finished_at_utc": now(),
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }


def run_shell(command: str, env: dict[str, str], cwd: Path | None = None, timeout: int = 1800) -> dict[str, Any]:
    return run_raw(["bash", "-lc", command], cwd=cwd, env=env, timeout=timeout)


def log_result(path: Path, result: dict[str, Any]) -> None:
    command = " ".join(str(part) for part in result["command"])
    write_text(
        path,
        "\n".join(
            [
                f"$ {command}",
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


def candidate_metadata(project: str, bug_id: str) -> dict[str, Any]:
    project_dir = BUGSINPY_REPO / "projects" / project
    bug_dir = project_dir / "bugs" / bug_id
    project_info = read_kv_file(project_dir / "project.info")
    bug_info = read_kv_file(bug_dir / "bug.info")
    run_test = (bug_dir / "run_test.sh").read_text(encoding="utf-8", errors="replace").strip() if (bug_dir / "run_test.sh").exists() else None
    return {
        "source_family": "bugsinpy",
        "project": project,
        "bug_id": bug_id,
        "repo_url": project_info.get("github_url"),
        "buggy_commit_id": bug_info.get("buggy_commit_id"),
        "fixed_commit_id_outcome_only": bug_info.get("fixed_commit_id"),
        "python_version_required": bug_info.get("python_version"),
        "test_file": bug_info.get("test_file"),
        "run_test_sh": run_test,
        "candidate_class": "real_bug_benchmark_entry",
        "fixed_or_gold_patch_used_at_decision_time": False,
    }


def target_match(test_text: str, expected_markers: list[str] | None) -> tuple[bool, bool, str]:
    import_blocked = any(marker in test_text for marker in IMPORT_BLOCKERS)
    if import_blocked:
        return False, True, "dependency/import/runtime failure marker was present"
    if expected_markers:
        matched = any(marker in test_text for marker in expected_markers)
        return matched, False, "expected BugsInPy target marker matched" if matched else "expected BugsInPy target marker was not found"
    matched = "FAIL:" in test_text or "AssertionError" in test_text or "FAILED" in test_text
    return matched, False, "generic BugsInPy test failure marker matched" if matched else "no target-compatible failure marker was found"


def write_candidate_common(
    directory: Path,
    project: str,
    bug_id: str,
    dependency_hint: str | None,
    prior_blocker: str | None,
) -> dict[str, Any]:
    metadata = candidate_metadata(project, bug_id)
    write_json(directory / "candidate_metadata.json", metadata)
    if prior_blocker is not None:
        write_json(
            directory / "prior_blocker_summary.json",
            {"prior_blocker": prior_blocker, "dependency_repair_is_runtime_setup_not_code_repair": True},
        )
    plan = {
        "project": project,
        "bug_id": bug_id,
        "dependency_policy": "Install dependencies only to make buggy project tests runnable; never modify source to bypass imports.",
        "prefer_project_declared_dependencies": True,
        "explicit_dependency_hint": dependency_hint,
        "fixed_or_gold_patch_used_at_decision_time": False,
    }
    write_json(directory / "dependency_install_plan.json", plan)
    write_json(
        directory / "gold_patch_exclusion_plan.json",
        {
            "project": project,
            "bug_id": bug_id,
            "fixed_revision_used_at_decision_time": False,
            "gold_patch_used_at_decision_time": False,
            "policy": "Only buggy checkout metadata and failing logs are decision-time inputs.",
        },
    )
    return metadata


def probe_candidate(candidate: dict[str, Any], env: dict[str, str], phase: str) -> dict[str, Any]:
    project = candidate["project"]
    bug_id = candidate["bug_id"]
    directory = ARTIFACT_ROOT / candidate["dir_name"]
    directory.mkdir(parents=True, exist_ok=True)
    workspace_parent = (RUNTIME_ROOT / "workspaces" / candidate["dir_name"]).resolve()
    checkout_dir = workspace_parent / project
    workspace_parent.mkdir(parents=True, exist_ok=True)
    dependency_hint = candidate.get("dependency_hint")
    write_candidate_common(directory, project, bug_id, dependency_hint, candidate.get("prior_blocker"))

    checkout_command = f"bugsinpy-checkout -p {project} -v 0 -i {bug_id} -w {workspace_parent}"
    compile_command = f"bugsinpy-compile -w {checkout_dir}"
    install_commands = [
        f"cd {checkout_dir} && python -m pip install -e .",
    ]
    if dependency_hint:
        install_commands.append(f"python -m pip install {dependency_hint}")
    install_command = " && ".join(install_commands)
    test_command = f"bugsinpy-test -w {checkout_dir} -r"

    write_text(directory / "checkout_command.txt", checkout_command + "\n")
    checkout_result = run_shell(checkout_command, env, timeout=900)
    log_result(directory / "checkout_log_raw.txt", checkout_result)

    write_text(directory / "compile_command.txt", compile_command + "\n")
    compile_result = run_shell(compile_command, env, timeout=1800) if checkout_result.get("returncode") == 0 else {
        "command": ["bash", "-lc", compile_command],
        "started_at_utc": now(),
        "finished_at_utc": now(),
        "returncode": None,
        "stdout": "",
        "stderr": "NOT_RUN: checkout failed",
        "timed_out": False,
    }
    log_result(directory / "compile_log_raw.txt", compile_result)

    write_text(directory / "dependency_install_commands.txt", install_command + "\n")
    install_result = run_shell(install_command, env, timeout=1800) if compile_result.get("returncode") == 0 else {
        "command": ["bash", "-lc", install_command],
        "started_at_utc": now(),
        "finished_at_utc": now(),
        "returncode": None,
        "stdout": "",
        "stderr": "NOT_RUN: compile/setup failed",
        "timed_out": False,
    }
    log_result(directory / "dependency_install_log_raw.txt", install_result)

    write_text(directory / "test_command.txt", test_command + "\n")
    test_result = run_shell(test_command, env, timeout=900) if install_result.get("returncode") == 0 else {
        "command": ["bash", "-lc", test_command],
        "started_at_utc": now(),
        "finished_at_utc": now(),
        "returncode": None,
        "stdout": "",
        "stderr": "NOT_RUN: dependency install failed",
        "timed_out": False,
    }
    log_result(directory / "test_log_raw.txt", test_result)
    test_text = f"{test_result.get('stdout', '')}\n{test_result.get('stderr', '')}"
    matched, import_blocked, reason = target_match(test_text, candidate.get("expected_markers"))
    if checkout_result.get("returncode") != 0:
        status = "blocked_runtime_environment_failure"
    elif compile_result.get("returncode") != 0 or install_result.get("returncode") != 0:
        status = "blocked_dependency_repair_failed"
    elif test_result.get("returncode") is None:
        status = "blocked_runtime_environment_failure"
    elif import_blocked:
        status = "blocked_runtime_environment_failure"
    elif matched and test_result.get("returncode") != 0:
        status = "promoted_ready_for_v2_7_bugsinpy_real_bug"
    else:
        status = "blocked_target_failure_not_reproduced"
    signature = f"BUGSINPY_TARGET_REPLAY: {project}:{bug_id}" if status.startswith("promoted") else f"TARGET_FAILURE_NOT_REPRODUCED: {project}:{bug_id}"
    write_text(directory / "failure_signature.txt", signature + "\n")
    write_json(
        directory / "target_failure_match_check.json",
        {
            "project": project,
            "bug_id": bug_id,
            "target_failure_matched": status.startswith("promoted"),
            "dependency_or_import_failure_detected": import_blocked,
            "target_failure_match_reason": reason,
            "test_returncode": test_result.get("returncode"),
            "promotion_status": status,
        },
    )
    write_json(
        directory / "replay_feasibility_result.json",
        {
            "project": project,
            "bug_id": bug_id,
            "phase": phase,
            "promotion_status": status,
            "checkout_returncode": checkout_result.get("returncode"),
            "compile_returncode": compile_result.get("returncode"),
            "dependency_install_returncode": install_result.get("returncode"),
            "test_returncode": test_result.get("returncode"),
            "runtime_replay_confirmed": status.startswith("promoted"),
            "failing_test_reproduced": status.startswith("promoted"),
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_manifest(directory)
    return {"candidate": f"{project}:{bug_id}", "directory": str(directory), "promotion_status": status, "failure_signature": signature}


def discover_expansion_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    projects_root = BUGSINPY_REPO / "projects"
    if not projects_root.exists():
        return candidates
    excluded = {("black", "2"), ("black", "8"), ("youtube-dl", "1")}
    for project_dir in sorted(path for path in projects_root.iterdir() if path.is_dir()):
        bugs_dir = project_dir / "bugs"
        if not bugs_dir.exists():
            continue
        for bug_dir in sorted(path for path in bugs_dir.iterdir() if path.is_dir()):
            key = (project_dir.name, bug_dir.name)
            if key in excluded:
                continue
            candidates.append(
                {
                    "dir_name": f"additional_{project_dir.name.replace('-', '_')}_{bug_dir.name}",
                    "project": project_dir.name,
                    "bug_id": bug_dir.name,
                    "dependency_hint": None,
                    "expected_markers": None,
                    "prior_blocker": None,
                }
            )
            if len(candidates) >= 8:
                return candidates
    return candidates


def main() -> int:
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True)
    RUNTIME_ROOT.mkdir(parents=True)
    env = os.environ.copy()
    write_text(
        ARTIFACT_ROOT / "runtime_environment.txt",
        "\n".join(
            [
                f"generated_at_utc={now()}",
                f"platform={platform.platform()}",
                f"python={platform.python_version()}",
                f"cwd={Path.cwd()}",
                f"runner_os={env.get('RUNNER_OS')}",
                f"github_repository={env.get('GITHUB_REPOSITORY')}",
            ]
        )
        + "\n",
    )
    clone_result = run_raw(["git", "clone", "--depth", "1", BUGSINPY_URL, str(BUGSINPY_REPO)], timeout=900)
    log_result(ARTIFACT_ROOT / "bugsinpy_clone_log_raw.txt", clone_result)
    if clone_result.get("returncode") == 0:
        env["PATH"] = str((BUGSINPY_REPO / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")

    phase_a_results: list[dict[str, Any]] = []
    phase_b_results: list[dict[str, Any]] = []
    if clone_result.get("returncode") == 0:
        for candidate in PHASE_A_CANDIDATES:
            phase_a_results.append(probe_candidate(candidate, env, "phase_a_dependency_recovery"))
        promoted_count = sum(1 for item in phase_a_results if item["promotion_status"].startswith("promoted")) + 1
        if promoted_count < 3:
            for candidate in discover_expansion_candidates():
                phase_b_results.append(probe_candidate(candidate, env, "phase_b_candidate_expansion"))
                promoted_count = 1 + sum(1 for item in phase_a_results + phase_b_results if item["promotion_status"].startswith("promoted"))
                if promoted_count >= 3:
                    break
    write_json(
        ARTIFACT_ROOT / "runtime_probe_summary.json",
        {
            "generated_at_utc": now(),
            "phase_a_results": phase_a_results,
            "phase_b_results": phase_b_results,
            "previously_promoted_candidate": "youtube-dl:1",
            "target_matched_candidate_count": 1 + sum(1 for item in phase_a_results + phase_b_results if item["promotion_status"].startswith("promoted")),
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_manifest(ARTIFACT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
