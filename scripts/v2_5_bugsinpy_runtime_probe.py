#!/usr/bin/env python3
"""GitHub Actions BugsInPy runtime probe for v2.5.

This script is intended to run on a Linux runner. It clones BugsInPy, attempts
buggy checkouts for a small fixed candidate set, captures raw command logs, and
marks candidates as promoted only when a local failing test is actually
reproduced. Fixed/gold patches are never used as decision-time inputs.
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


ARTIFACT_ROOT = Path("v2_5_bugsinpy_runtime_probe_artifacts")
RUNTIME_ROOT = Path("_v2_5_bugsinpy_runtime")
BUGSINPY_REPO = RUNTIME_ROOT / "BugsInPy"
BUGSINPY_URL = "https://github.com/soarsmu/BugsInPy.git"

CANDIDATES = [
    {"dir_name": "black_2", "project": "black", "bug_id": "2"},
    {"dir_name": "youtube_dl_1", "project": "youtube-dl", "bug_id": "1"},
    {"dir_name": "black_8", "project": "black", "bug_id": "8"},
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
    lines = [
        f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}"
        for path in paths
    ]
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


def status_for(checkout: dict[str, Any], compile_result: dict[str, Any], test_result: dict[str, Any]) -> tuple[str, str]:
    if checkout.get("returncode") != 0:
        return "blocked_bugsinpy_checkout_failed", "checkout did not complete"
    if compile_result.get("returncode") != 0:
        return "blocked_bugsinpy_compile_failed", "compile/setup did not complete"
    if test_result.get("returncode") is None:
        return "blocked_bugsinpy_test_not_reproducible", "test command did not produce a return code"
    if test_result.get("returncode") == 0:
        return "blocked_bugsinpy_test_not_reproducible", "test command passed instead of reproducing a failure"
    return "promoted_ready_for_v2_5_bugsinpy_real_bug", "buggy checkout, compile/setup, and failing test command completed with reproduced failure"


def probe_candidate(candidate: dict[str, str], env: dict[str, str]) -> dict[str, Any]:
    project = candidate["project"]
    bug_id = candidate["bug_id"]
    directory = ARTIFACT_ROOT / candidate["dir_name"]
    directory.mkdir(parents=True, exist_ok=True)
    workspace_parent = (RUNTIME_ROOT / "workspaces" / candidate["dir_name"]).resolve()
    checkout_dir = workspace_parent / project
    workspace_parent.mkdir(parents=True, exist_ok=True)

    metadata = candidate_metadata(project, bug_id)
    write_json(directory / "candidate_metadata.json", metadata)

    info_command = f"bugsinpy-info -p {project} -i {bug_id}"
    checkout_command = f"bugsinpy-checkout -p {project} -v 0 -i {bug_id} -w {workspace_parent}"
    compile_command = f"bugsinpy-compile -w {checkout_dir}"
    test_command = f"bugsinpy-test -w {checkout_dir} -r"

    write_text(directory / "info_command.txt", info_command + "\n")
    info_result = run_shell(info_command, env, timeout=300)
    log_result(directory / "info_log_raw.txt", info_result)

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

    write_text(directory / "test_command.txt", test_command + "\n")
    test_result = run_shell(test_command, env, timeout=900) if compile_result.get("returncode") == 0 else {
        "command": ["bash", "-lc", test_command],
        "started_at_utc": now(),
        "finished_at_utc": now(),
        "returncode": None,
        "stdout": "",
        "stderr": "NOT_RUN: compile/setup failed",
        "timed_out": False,
    }
    log_result(directory / "test_log_raw.txt", test_result)

    promotion_status, reason = status_for(checkout_result, compile_result, test_result)
    failure_signature = (
        f"BUGSINPY_REPRODUCED_FAILURE: {project}:{bug_id}"
        if promotion_status == "promoted_ready_for_v2_5_bugsinpy_real_bug"
        else f"UNAVAILABLE_OR_BLOCKED: BugsInPy {project}:{bug_id}"
    )
    write_text(directory / "failure_signature.txt", failure_signature + "\n")
    write_json(
        directory / "replay_feasibility_result.json",
        {
            "project": project,
            "bug_id": bug_id,
            "promotion_status": promotion_status,
            "reason": reason,
            "checkout_returncode": checkout_result.get("returncode"),
            "compile_returncode": compile_result.get("returncode"),
            "test_returncode": test_result.get("returncode"),
            "runtime_replay_confirmed": promotion_status == "promoted_ready_for_v2_5_bugsinpy_real_bug",
            "failing_test_reproduced": promotion_status == "promoted_ready_for_v2_5_bugsinpy_real_bug",
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_json(
        directory / "gold_patch_exclusion_plan.json",
        {
            "project": project,
            "bug_id": bug_id,
            "outcome_only_sources": ["fixed_commit_id", "bug_patch.txt", "fixed source tree"],
            "allowed_at_decision_time": False,
            "policy": "Only buggy checkout metadata and failing logs are decision-time inputs. Fixed/gold patches are outcome-only.",
        },
    )
    write_manifest(directory)
    return {
        "candidate": f"{project}:{bug_id}",
        "directory": str(directory),
        "promotion_status": promotion_status,
        "failure_signature": failure_signature,
    }


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

    install_lines = []
    for label, command in [
        ("git", ["git", "--version"]),
        ("bash", ["bash", "--version"]),
        ("docker", ["docker", "--version"]),
    ]:
        result = run_raw(command, timeout=60)
        install_lines.append(f"## {label}\n")
        install_lines.append(json.dumps(result, indent=2, sort_keys=True))
        install_lines.append("\n")
    clone_result = run_raw(["git", "clone", "--depth", "1", BUGSINPY_URL, str(BUGSINPY_REPO)], timeout=900)
    install_lines.append("## BugsInPy clone\n")
    install_lines.append(json.dumps(clone_result, indent=2, sort_keys=True))
    write_text(ARTIFACT_ROOT / "bugsinpy_install_log.txt", "\n".join(install_lines) + "\n")

    if clone_result.get("returncode") == 0:
        env["PATH"] = str((BUGSINPY_REPO / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")
    command_probe_lines = []
    for command in ["bugsinpy-info", "bugsinpy-checkout", "bugsinpy-compile", "bugsinpy-test"]:
        result = run_shell(f"command -v {command} && {command} --help", env, timeout=120)
        command_probe_lines.append(f"## {command}\n")
        command_probe_lines.append(json.dumps(result, indent=2, sort_keys=True))
        command_probe_lines.append("\n")
    write_text(ARTIFACT_ROOT / "bugsinpy_command_probe.txt", "\n".join(command_probe_lines) + "\n")

    results = []
    if clone_result.get("returncode") == 0:
        for candidate in CANDIDATES:
            results.append(probe_candidate(candidate, env))
    else:
        for candidate in CANDIDATES:
            directory = ARTIFACT_ROOT / candidate["dir_name"]
            directory.mkdir(parents=True, exist_ok=True)
            write_json(directory / "candidate_metadata.json", candidate)
            for name in [
                "info_command.txt",
                "info_log_raw.txt",
                "checkout_command.txt",
                "checkout_log_raw.txt",
                "compile_command.txt",
                "compile_log_raw.txt",
                "test_command.txt",
                "test_log_raw.txt",
            ]:
                write_text(directory / name, "NOT_RUN: BugsInPy clone failed.\n")
            write_text(directory / "failure_signature.txt", f"UNAVAILABLE_OR_BLOCKED: BugsInPy {candidate['project']}:{candidate['bug_id']}\n")
            write_json(
                directory / "replay_feasibility_result.json",
                {
                    "project": candidate["project"],
                    "bug_id": candidate["bug_id"],
                    "promotion_status": "blocked_bugsinpy_tooling_unavailable",
                    "runtime_replay_confirmed": False,
                    "failing_test_reproduced": False,
                    "fixed_or_gold_patch_used_at_decision_time": False,
                },
            )
            write_json(directory / "gold_patch_exclusion_plan.json", {"allowed_at_decision_time": False})
            write_manifest(directory)

    write_json(
        ARTIFACT_ROOT / "runtime_probe_summary.json",
        {
            "generated_at_utc": now(),
            "candidate_results": results,
            "promoted_candidate_count": sum(1 for item in results if item["promotion_status"].startswith("promoted_ready")),
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_manifest(ARTIFACT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
