#!/usr/bin/env python3
"""GitHub Actions runner for v2.7d BugsInPy third-candidate recovery.

The runner searches beyond the v2.7b direct-runner artifact for one additional
clean target-matched BugsInPy candidate. It uses BugsInPy only for checkout and
metadata, runs direct target commands in the buggy workspace, and refuses to
promote dependency/import/runtime/wrapper failures as target replay.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_ROOT = Path("v2_7d_bugsinpy_third_candidate_direct_runner_expansion_artifacts")
RUNTIME_ROOT = Path("_v2_7d_bugsinpy_runtime")
BUGSINPY_REPO = RUNTIME_ROOT / "BugsInPy"
BUGSINPY_URL = "https://github.com/soarsmu/BugsInPy.git"
BUDGET = 12

EXCLUDED = {
    ("youtube-dl", "1"),
    ("black", "8"),
    ("black", "2"),
    ("PySnooper", "1"),
    ("PySnooper", "2"),
    ("PySnooper", "3"),
    ("ansible", "1"),
    ("ansible", "10"),
    ("ansible", "11"),
    ("ansible", "12"),
    ("ansible", "13"),
}

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
TARGET_FAILURE_MARKERS = [
    "FAIL:",
    "FAILED",
    "AssertionError",
    "E   AssertionError",
    "Traceback (most recent call last):",
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
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {
            "command": command,
            "started_at_utc": started,
            "finished_at_utc": now(),
            "returncode": None,
            "stdout": getattr(exc, "stdout", "") or "",
            "stderr": str(exc),
            "timed_out": isinstance(exc, subprocess.TimeoutExpired),
        }


def run_shell(command: str, env: dict[str, str], cwd: Path | None = None, timeout: int = 1800) -> dict[str, Any]:
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


def read_metadata(project: str, bug_id: str) -> dict[str, Any]:
    project_dir = BUGSINPY_REPO / "projects" / project
    bug_dir = project_dir / "bugs" / bug_id
    project_info = read_kv_file(project_dir / "project.info")
    bug_info = read_kv_file(bug_dir / "bug.info")
    run_test = (bug_dir / "run_test.sh").read_text(encoding="utf-8", errors="replace").strip() if (bug_dir / "run_test.sh").exists() else ""
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


def normalize_test_file_to_module(test_file: str) -> str:
    module = test_file.replace("\\", "/").removesuffix(".py").replace("/", ".")
    return module.strip(".")


def direct_commands_from_metadata(metadata: dict[str, Any]) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []
    run_test = str(metadata.get("run_test_sh") or "")
    for raw in run_test.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "bugsinpy-test" in line:
            continue
        if any(token in line for token in ["pytest", "unittest", "nosetests"]):
            commands.append({"command": line, "source": "run_test.sh direct command"})
    test_file = str(metadata.get("test_file") or "").strip()
    if test_file and test_file.endswith(".py"):
        commands.append({"command": f"python -m pytest -q {test_file}", "source": "bug.info test_file pytest command"})
        commands.append({"command": f"python -m unittest -q {normalize_test_file_to_module(test_file)}", "source": "bug.info test_file unittest command"})
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in commands:
        command = re.sub(r"\s+", " ", item["command"]).strip()
        if command and command not in seen:
            unique.append({"command": command, "source": item["source"]})
            seen.add(command)
    return unique[:4]


def score_candidate(metadata: dict[str, Any], commands: list[dict[str, str]]) -> int:
    score = 0
    project = str(metadata.get("project") or "").lower()
    python_required = str(metadata.get("python_version_required") or "")
    run_test = str(metadata.get("run_test_sh") or "")
    if commands:
        score += 40
    if "pytest" in run_test or "unittest" in run_test:
        score += 20
    if project not in {"ansible", "keras", "pandas", "spacy", "scrapy"}:
        score += 15
    if python_required.startswith("3"):
        score += 15
    if python_required.startswith("2"):
        score -= 25
    if "bugsinpy-test" in run_test:
        score -= 10
    return score


def discover_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    projects_root = BUGSINPY_REPO / "projects"
    if not projects_root.exists():
        return []
    for project_dir in sorted(path for path in projects_root.iterdir() if path.is_dir()):
        bugs_dir = project_dir / "bugs"
        if not bugs_dir.exists():
            continue
        for bug_dir in sorted(path for path in bugs_dir.iterdir() if path.is_dir()):
            key = (project_dir.name, bug_dir.name)
            if key in EXCLUDED:
                continue
            metadata = read_metadata(project_dir.name, bug_dir.name)
            commands = direct_commands_from_metadata(metadata)
            score = score_candidate(metadata, commands)
            if not commands or score < 35:
                continue
            candidates.append(
                {
                    "dir_name": f"candidate_{project_dir.name.replace('-', '_')}_{bug_dir.name}",
                    "project": project_dir.name,
                    "bug_id": bug_dir.name,
                    "metadata": metadata,
                    "commands": commands,
                    "readiness_score": score,
                    "selection_reason": "ranked BugsInPy direct-command candidate outside previous failed set",
                }
            )
    return sorted(candidates, key=lambda item: (-int(item["readiness_score"]), item["project"], int(item["bug_id"]) if str(item["bug_id"]).isdigit() else str(item["bug_id"])))[:BUDGET]


def classify(test_text: str, returncode: int | None) -> tuple[str, bool, bool, bool, str]:
    wrapper_contaminated = any(marker in test_text for marker in WRAPPER_BLOCKERS)
    runtime_blocked = any(marker in test_text for marker in IMPORT_OR_RUNTIME_BLOCKERS)
    target_signal = any(marker in test_text for marker in TARGET_FAILURE_MARKERS)
    if wrapper_contaminated:
        return "blocked_runtime_environment_failure", target_signal, wrapper_contaminated, runtime_blocked, "wrapper contamination marker was present"
    if runtime_blocked:
        return "blocked_runtime_environment_failure", target_signal, wrapper_contaminated, runtime_blocked, "dependency/import/runtime blocker marker was present"
    if returncode not in (None, 0) and target_signal:
        return "promoted_ready_for_v2_8_bugsinpy_real_bug", True, wrapper_contaminated, runtime_blocked, "clean direct target-compatible failure matched"
    if returncode == 0:
        return "blocked_target_failure_not_reproduced", False, wrapper_contaminated, runtime_blocked, "direct target command passed"
    return "blocked_target_failure_not_reproduced", False, wrapper_contaminated, runtime_blocked, "direct target command did not produce target-compatible failure"


def write_common_files(directory: Path, candidate: dict[str, Any]) -> None:
    metadata = dict(candidate["metadata"])
    write_json(directory / "candidate_metadata.json", metadata)
    write_json(directory / "selection_reason.json", {"selection_reason": candidate["selection_reason"], "readiness_score": candidate["readiness_score"]})
    write_json(directory / "direct_command_source.json", {"commands": candidate["commands"], "policy": "derived from BugsInPy run_test.sh or bug.info test_file; fixed/gold patches not used"})
    write_json(directory / "dependency_install_plan.json", {"prefer_project_declared_dependencies": True, "source_file_modification_allowed": False, "fixed_or_gold_patch_used_at_decision_time": False})
    write_json(directory / "gold_patch_exclusion_plan.json", {"fixed_revision_used_at_decision_time": False, "gold_patch_used_at_decision_time": False, "corrected_files_used_as_repair_hints": False})


def run_candidate(candidate: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    project = candidate["project"]
    bug_id = candidate["bug_id"]
    directory = ARTIFACT_ROOT / candidate["dir_name"]
    directory.mkdir(parents=True, exist_ok=True)
    write_common_files(directory, candidate)
    workspace_parent = (RUNTIME_ROOT / "workspaces" / candidate["dir_name"]).resolve()
    checkout_dir = workspace_parent / project
    workspace_parent.mkdir(parents=True, exist_ok=True)
    checkout_command = f"bugsinpy-checkout -p {project} -v 0 -i {bug_id} -w {workspace_parent}"
    compile_command = f"bugsinpy-compile -w {checkout_dir}"
    dependency_command = (
        f"cd {checkout_dir} && "
        "for f in requirements.txt requirements-dev.txt test-requirements.txt dev-requirements.txt; do "
        "if [ -f \"$f\" ]; then python -m pip install -r \"$f\" || true; fi; "
        "done && python -m pip install -e ."
    )
    write_text(directory / "checkout_command.txt", checkout_command + "\n")
    checkout_result = run_shell(checkout_command, env, timeout=900)
    log_result(directory / "checkout_log_raw.txt", checkout_result)
    write_text(directory / "compile_command.txt", compile_command + "\n")
    compile_result = run_shell(compile_command, env, timeout=1800) if checkout_result["returncode"] == 0 else {"command": ["bash", "-lc", compile_command], "started_at_utc": now(), "finished_at_utc": now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout failed", "timed_out": False}
    log_result(directory / "compile_log_raw.txt", compile_result)
    write_text(directory / "dependency_install_commands.txt", dependency_command + "\n")
    dependency_result = run_shell(dependency_command, env, timeout=1800) if compile_result["returncode"] == 0 else {"command": ["bash", "-lc", dependency_command], "started_at_utc": now(), "finished_at_utc": now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: compile failed", "timed_out": False}
    log_result(directory / "dependency_install_log_raw.txt", dependency_result)
    direct_logs: list[str] = []
    final_result: dict[str, Any] | None = None
    final_command = ""
    final_status = "blocked_target_failure_not_reproduced"
    final_target = False
    final_wrapper = False
    final_runtime = False
    final_reason = "no direct command attempted"
    if dependency_result["returncode"] == 0:
        for item in candidate["commands"]:
            command = item["command"]
            result = run_shell(command, env, cwd=checkout_dir, timeout=900)
            status, target, wrapper, runtime, reason = classify(f"{result.get('stdout', '')}\n{result.get('stderr', '')}", result.get("returncode"))
            direct_logs.append(
                "\n".join(
                    [
                        f"## command: {command}",
                        f"source={item['source']}",
                        f"promotion_status={status}",
                        f"target_failure_signal_present={target}",
                        f"wrapper_contaminated={wrapper}",
                        f"dependency_or_runtime_blocked={runtime}",
                        f"reason={reason}",
                        "--- raw ---",
                        "$ " + command,
                        str(result.get("stdout", "")),
                        str(result.get("stderr", "")),
                    ]
                )
            )
            final_result = result
            final_command = command
            final_status, final_target, final_wrapper, final_runtime, final_reason = status, target, wrapper, runtime, reason
            if status.startswith("promoted"):
                break
    else:
        final_result = {"returncode": None}
        final_status = "blocked_runtime_environment_failure"
        final_runtime = True
        final_reason = "dependency setup failed"
    write_text(directory / "direct_test_command.txt", final_command + "\n")
    write_text(directory / "direct_test_log_raw.txt", "\n\n".join(direct_logs) + "\n")
    write_text(directory / "failure_signature.txt", f"BUGSINPY_DIRECT_TARGET_REPLAY: {project}:{bug_id}\n" if final_status.startswith("promoted") else f"DIRECT_TARGET_NOT_PROMOTED: {project}:{bug_id}\n")
    write_json(directory / "target_failure_match_check.json", {"project": project, "bug_id": bug_id, "target_failure_matched": final_status.startswith("promoted"), "target_failure_signal_present": final_target, "dependency_or_runtime_blocked": final_runtime, "wrapper_contaminated": final_wrapper, "reason": final_reason, "promotion_status": final_status, "direct_test_returncode": final_result.get("returncode") if final_result else None})
    write_json(directory / "wrapper_contamination_check.json", {"wrapper_path_bypassed": True, "wrapper_contamination_detected": final_wrapper, "promotion_allowed": final_status.startswith("promoted")})
    write_json(directory / "replay_feasibility_result.json", {"project": project, "bug_id": bug_id, "promotion_status": final_status, "checkout_returncode": checkout_result.get("returncode"), "compile_returncode": compile_result.get("returncode"), "dependency_install_returncode": dependency_result.get("returncode"), "direct_test_returncode": final_result.get("returncode") if final_result else None, "runtime_replay_confirmed": final_status.startswith("promoted"), "failing_test_reproduced": final_status.startswith("promoted"), "fixed_or_gold_patch_used_at_decision_time": False})
    write_manifest(directory)
    return {"candidate": f"{project}:{bug_id}", "directory": str(directory), "promotion_status": final_status, "target_failure_matched": final_status.startswith("promoted")}


def main() -> int:
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True)
    RUNTIME_ROOT.mkdir(parents=True)
    env = os.environ.copy()
    write_text(ARTIFACT_ROOT / "runtime_environment.txt", f"generated_at_utc={now()}\nplatform={platform.platform()}\npython={platform.python_version()}\n")
    clone_result = run_raw(["git", "clone", "--depth", "1", BUGSINPY_URL, str(BUGSINPY_REPO)], timeout=900)
    log_result(ARTIFACT_ROOT / "bugsinpy_clone_log_raw.txt", clone_result)
    results: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    if clone_result.get("returncode") == 0:
        env["PATH"] = str((BUGSINPY_REPO / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")
        selected = discover_candidates()
        for candidate in selected:
            result = run_candidate(candidate, env)
            results.append(result)
            if result["target_failure_matched"]:
                break
    write_json(ARTIFACT_ROOT / "candidate_selection_manifest.json", {"budget": BUDGET, "excluded_candidates": sorted(f"{project}:{bug}" for project, bug in EXCLUDED), "selected_candidates": [{"candidate": f"{item['project']}:{item['bug_id']}", "readiness_score": item["readiness_score"], "commands": item["commands"]} for item in selected]})
    write_json(ARTIFACT_ROOT / "third_candidate_runner_summary.json", {"generated_at_utc": now(), "previous_clean_target_matched_candidates": ["youtube-dl:1", "black:8"], "attempted_count": len(results), "newly_promoted_count": sum(1 for item in results if item["target_failure_matched"]), "final_clean_target_matched_count_if_ingested": 2 + sum(1 for item in results if item["target_failure_matched"]), "results": results, "full_scoring_allowed": False, "self_maintaining_software_demonstrated": False, "fixed_or_gold_patch_used_at_decision_time": False})
    write_manifest(ARTIFACT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
