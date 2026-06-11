#!/usr/bin/env python3
"""GitHub Actions direct target runner fix for BugsInPy v2.7b.

The v2.7 artifact showed that ``bugsinpy-test -r`` can emit wrapper/runtime
errors even when a target-looking unittest failure appears. This runner uses
BugsInPy for checkout/metadata, then runs direct target commands inside the
buggy workspace. A candidate is promoted only when the direct command produces
a target-compatible failure without dependency/import/wrapper contamination.
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


ARTIFACT_ROOT = Path("v2_7b_bugsinpy_direct_target_runner_fix_artifacts")
RUNTIME_ROOT = Path("_v2_7b_bugsinpy_runtime")
BUGSINPY_REPO = RUNTIME_ROOT / "BugsInPy"
BUGSINPY_URL = "https://github.com/soarsmu/BugsInPy.git"

IMPORT_OR_RUNTIME_BLOCKERS = [
    "ModuleNotFoundError",
    "ImportError",
    "No module named",
    "NameError: name 'AioHTTPTestCase' is not defined",
    "command not found",
    "No such file or directory",
]
WRAPPER_BLOCKERS = [
    "bugsinpy-test:",
    "illegal option",
    "env/bin/activate",
    "deactivate: command not found",
]

PHASE_A_CANDIDATES = [
    {
        "dir_name": "black_8_direct_target_rerun",
        "project": "black",
        "bug_id": "8",
        "direct_command": "python -m unittest -q tests.test_black.BlackTestCase.test_comments7",
        "required_markers": ["FAIL: test_comments7", "BlackTestCase.test_comments7", "Cannot parse: 11:4:"],
        "dependency_hints": ["click"],
        "prior_summary": "v2.7 showed target-looking test_comments7 failure but wrapper/runtime contamination remained.",
    },
    {
        "dir_name": "black_2_direct_target_rerun",
        "project": "black",
        "bug_id": "2",
        "direct_command": "python -m unittest -q tests.test_black.BlackTestCase.test_fmtonoff4",
        "required_markers": ["FAIL: test_fmtonoff4", "BlackTestCase.test_fmtonoff4"],
        "dependency_hints": ["regex", "aiohttp"],
        "prior_summary": "v2.7 remained blocked by NameError: AioHTTPTestCase.",
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
        return {"command": command, "started_at_utc": started, "finished_at_utc": now(), "returncode": None, "stdout": "", "stderr": str(exc), "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "started_at_utc": started, "finished_at_utc": now(), "returncode": None, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}


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


def classify_direct_result(test_text: str, returncode: int | None, required_markers: list[str] | None) -> tuple[str, bool, bool, bool, str]:
    wrapper_contaminated = any(marker in test_text for marker in WRAPPER_BLOCKERS)
    runtime_blocked = any(marker in test_text for marker in IMPORT_OR_RUNTIME_BLOCKERS)
    if required_markers:
        target_matched = any(marker in test_text for marker in required_markers)
    else:
        target_matched = "FAIL:" in test_text or "AssertionError" in test_text or "FAILED" in test_text
    if wrapper_contaminated:
        return "target_failure_signal_present_but_wrapper_contaminated" if target_matched else "blocked_runtime_environment_failure", target_matched, wrapper_contaminated, runtime_blocked, "wrapper contamination marker was present"
    if runtime_blocked:
        return "blocked_runtime_environment_failure", target_matched, wrapper_contaminated, runtime_blocked, "dependency/import/runtime blocker marker was present"
    if returncode not in (None, 0) and target_matched:
        return "promoted_ready_for_v2_8_bugsinpy_real_bug", True, wrapper_contaminated, runtime_blocked, "clean direct target failure matched"
    if returncode == 0:
        return "blocked_target_failure_not_reproduced", False, wrapper_contaminated, runtime_blocked, "direct target command passed instead of reproducing failure"
    return "blocked_target_failure_not_reproduced", False, wrapper_contaminated, runtime_blocked, "direct target command did not produce target-compatible failure"


def write_common_candidate_files(directory: Path, project: str, bug_id: str, direct_command: str, dependency_hints: list[str], prior_summary: str, selection_reason: str | None = None) -> None:
    write_json(directory / "candidate_metadata.json", candidate_metadata(project, bug_id))
    if selection_reason is not None:
        write_json(directory / "selection_reason.json", {"selection_reason": selection_reason})
        write_json(directory / "direct_command_source.json", {"source": "BugsInPy run_test.sh or metadata-derived direct command", "direct_command": direct_command})
    write_json(directory / "prior_v2_7_summary.json", {"summary": prior_summary})
    write_json(
        directory / "direct_rerun_plan.json",
        {
            "direct_command": direct_command,
            "bypass_bugsinpy_test_wrapper": True,
            "dependency_setup_is_runtime_setup_not_repair": True,
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_json(
        directory / "dependency_install_plan.json",
        {
            "prefer_project_declared_dependencies": True,
            "explicit_dependency_hints": dependency_hints,
            "source_file_modification_allowed": False,
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_json(
        directory / "gold_patch_exclusion_plan.json",
        {
            "fixed_revision_used_at_decision_time": False,
            "gold_patch_used_at_decision_time": False,
            "corrected_files_used_as_repair_hints": False,
            "policy": "Gold/fixed patches remain outcome-only.",
        },
    )


def run_candidate(candidate: dict[str, Any], env: dict[str, str], additional: bool = False) -> dict[str, Any]:
    project = candidate["project"]
    bug_id = candidate["bug_id"]
    directory = ARTIFACT_ROOT / candidate["dir_name"]
    directory.mkdir(parents=True, exist_ok=True)
    workspace_parent = (RUNTIME_ROOT / "workspaces" / candidate["dir_name"]).resolve()
    checkout_dir = workspace_parent / project
    workspace_parent.mkdir(parents=True, exist_ok=True)
    direct_command = candidate["direct_command"]
    dependency_hints = candidate.get("dependency_hints", [])
    write_common_candidate_files(directory, project, bug_id, direct_command, dependency_hints, candidate.get("prior_summary", "selected for direct target rerun"), candidate.get("selection_reason") if additional else None)

    checkout_command = f"bugsinpy-checkout -p {project} -v 0 -i {bug_id} -w {workspace_parent}"
    compile_command = f"bugsinpy-compile -w {checkout_dir}"
    install_parts = [f"cd {checkout_dir} && python -m pip install -e ."]
    if dependency_hints:
        install_parts.extend(f"python -m pip install {dependency}" for dependency in dependency_hints)
    dependency_command = " && ".join(install_parts)

    write_text(directory / "checkout_command.txt", checkout_command + "\n")
    checkout_result = run_shell(checkout_command, env, timeout=900)
    log_result(directory / "checkout_log_raw.txt", checkout_result)
    write_text(directory / "compile_command.txt", compile_command + "\n")
    compile_result = run_shell(compile_command, env, timeout=1800) if checkout_result.get("returncode") == 0 else {"command": ["bash", "-lc", compile_command], "started_at_utc": now(), "finished_at_utc": now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout failed", "timed_out": False}
    log_result(directory / "compile_log_raw.txt", compile_result)
    write_text(directory / "dependency_install_commands.txt", dependency_command + "\n")
    dependency_result = run_shell(dependency_command, env, timeout=1800) if compile_result.get("returncode") == 0 else {"command": ["bash", "-lc", dependency_command], "started_at_utc": now(), "finished_at_utc": now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: compile/setup failed", "timed_out": False}
    log_result(directory / "dependency_install_log_raw.txt", dependency_result)
    write_text(directory / "direct_test_command.txt", direct_command + "\n")
    test_result = run_shell(direct_command, env, cwd=checkout_dir, timeout=900) if dependency_result.get("returncode") == 0 else {"command": ["bash", "-lc", direct_command], "started_at_utc": now(), "finished_at_utc": now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: dependency install failed", "timed_out": False}
    log_result(directory / "direct_test_log_raw.txt", test_result)
    test_text = f"{test_result.get('stdout', '')}\n{test_result.get('stderr', '')}"
    status, target_matched, wrapper_contaminated, runtime_blocked, reason = classify_direct_result(test_text, test_result.get("returncode"), candidate.get("required_markers"))
    write_text(directory / "failure_signature.txt", f"BUGSINPY_DIRECT_TARGET_REPLAY: {project}:{bug_id}\n" if status.startswith("promoted") else f"DIRECT_TARGET_NOT_PROMOTED: {project}:{bug_id}\n")
    write_json(
        directory / "target_failure_match_check.json",
        {
            "project": project,
            "bug_id": bug_id,
            "target_failure_matched": status.startswith("promoted"),
            "target_failure_signal_present": target_matched,
            "dependency_or_runtime_blocked": runtime_blocked,
            "wrapper_contaminated": wrapper_contaminated,
            "reason": reason,
            "promotion_status": status,
            "direct_test_returncode": test_result.get("returncode"),
        },
    )
    write_json(directory / "wrapper_contamination_check.json", {"wrapper_contamination_detected": wrapper_contaminated, "wrapper_path_bypassed": True, "promotion_allowed": status.startswith("promoted")})
    write_json(
        directory / "replay_feasibility_result.json",
        {
            "project": project,
            "bug_id": bug_id,
            "promotion_status": status,
            "checkout_returncode": checkout_result.get("returncode"),
            "compile_returncode": compile_result.get("returncode"),
            "dependency_install_returncode": dependency_result.get("returncode"),
            "direct_test_returncode": test_result.get("returncode"),
            "runtime_replay_confirmed": status.startswith("promoted"),
            "failing_test_reproduced": status.startswith("promoted"),
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_manifest(directory)
    return {"candidate": f"{project}:{bug_id}", "directory": str(directory), "promotion_status": status, "target_failure_matched": status.startswith("promoted")}


def discover_additional_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    projects_root = BUGSINPY_REPO / "projects"
    excluded = {("black", "2"), ("black", "8"), ("youtube-dl", "1")}
    if not projects_root.exists():
        return candidates
    for project_dir in sorted(path for path in projects_root.iterdir() if path.is_dir()):
        bugs_dir = project_dir / "bugs"
        if not bugs_dir.exists():
            continue
        for bug_dir in sorted(path for path in bugs_dir.iterdir() if path.is_dir()):
            key = (project_dir.name, bug_dir.name)
            if key in excluded:
                continue
            run_test = (bug_dir / "run_test.sh").read_text(encoding="utf-8", errors="replace").strip() if (bug_dir / "run_test.sh").exists() else ""
            if not run_test or "bugsinpy-test" in run_test:
                continue
            candidates.append(
                {
                    "dir_name": f"additional_direct_{project_dir.name.replace('-', '_')}_{bug_dir.name}",
                    "project": project_dir.name,
                    "bug_id": bug_dir.name,
                    "direct_command": run_test.splitlines()[-1],
                    "required_markers": None,
                    "dependency_hints": [],
                    "prior_summary": "focused additional direct candidate selected from BugsInPy run_test.sh",
                    "selection_reason": "direct run_test.sh command exists and does not invoke bugsinpy-test wrapper",
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
            phase_a_results.append(run_candidate(candidate, env))
        total_clean = 1 + sum(1 for item in phase_a_results if item["target_failure_matched"])
        if total_clean < 3:
            for candidate in discover_additional_candidates():
                phase_b_results.append(run_candidate(candidate, env, additional=True))
                total_clean = 1 + sum(1 for item in phase_a_results + phase_b_results if item["target_failure_matched"])
                if total_clean >= 3:
                    break
    write_json(
        ARTIFACT_ROOT / "direct_runner_summary.json",
        {
            "generated_at_utc": now(),
            "previously_promoted_candidate": "youtube-dl:1",
            "phase_a_results": phase_a_results,
            "phase_b_results": phase_b_results,
            "final_clean_target_matched_count": 1 + sum(1 for item in phase_a_results + phase_b_results if item["target_failure_matched"]),
            "full_scoring_allowed": False,
            "self_maintaining_software_demonstrated": False,
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_manifest(ARTIFACT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
