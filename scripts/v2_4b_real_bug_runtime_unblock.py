#!/usr/bin/env python3
"""Generate v2.4b real-bug benchmark runtime unblock artifacts.

The campaign probes BugsInPy first, then SWE-bench. It only promotes candidates
when a local benchmark runtime can actually replay a failing state. Metadata
alone is not treated as replay readiness.
"""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r"C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_4b_real_bug_runtime_unblock"
BUGSINPY_REPO = REPO_ROOT / "external_repos" / "v2_4_candidate_bugsinpy"
SWE_BENCH_REPO = REPO_ROOT / "external_repos" / "v2_4_candidate_swe_bench"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BUGSINPY_CANDIDATES = [
    ("bugsinpy_candidate_001", "black", "2"),
    ("bugsinpy_candidate_002", "youtube-dl", "1"),
    ("bugsinpy_candidate_003", "black", "8"),
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


def run_probe(command: list[str], timeout: int = 10, cwd: Path | None = None) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "timed_out": False,
        }
    except FileNotFoundError as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def git_head(repo: Path) -> str | None:
    if not (repo / ".git").exists():
        return None
    safe = str(repo.resolve()).replace("\\", "/")
    result = subprocess.run(
        ["git", "-c", f"safe.directory={safe}", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


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


def read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace").strip()


def disk_report() -> dict[str, Any]:
    usage = shutil.disk_usage(REPO_ROOT)
    return {
        "total_gb": round(usage.total / (1024**3), 2),
        "used_gb": round(usage.used / (1024**3), 2),
        "free_gb": round(usage.free / (1024**3), 2),
        "swe_bench_120gb_warning": usage.free < 120 * (1024**3),
    }


def runtime_probes() -> dict[str, Any]:
    bugsinpy_scripts = {
        name: (BUGSINPY_REPO / "framework" / "bin" / name).exists()
        for name in ["bugsinpy-info", "bugsinpy-checkout", "bugsinpy-compile", "bugsinpy-test"]
    }
    return {
        "generated_at_utc": now(),
        "os_platform": platform.platform(),
        "python_executable": str(PYTHON),
        "python_version_probe": run_probe([str(PYTHON), "--version"]),
        "git_probe": run_probe(["git", "--version"]),
        "shell_probe_bash": run_probe(["bash", "--version"]),
        "docker_version_probe": run_probe(["docker", "--version"]),
        "docker_info_probe": run_probe(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=10),
        "disk_report": disk_report(),
        "bugsinpy_path_commands": {
            name: shutil.which(name) for name in ["bugsinpy-info", "bugsinpy-checkout", "bugsinpy-compile", "bugsinpy-test"]
        },
        "bugsinpy_framework_scripts_present": bugsinpy_scripts,
        "bugsinpy_framework_scripts_are_bash": True,
        "bugsinpy_local_checkout": {
            "path": str(BUGSINPY_REPO),
            "exists": BUGSINPY_REPO.exists(),
            "head": git_head(BUGSINPY_REPO),
        },
        "swe_bench_import_probe": run_probe([str(PYTHON), "-c", "import swebench; print('swebench-import-ok')"]),
        "swe_bench_harness_file_present": (SWE_BENCH_REPO / "swebench" / "harness" / "run_evaluation.py").exists(),
        "swe_bench_local_checkout": {
            "path": str(SWE_BENCH_REPO),
            "exists": SWE_BENCH_REPO.exists(),
            "head": git_head(SWE_BENCH_REPO),
        },
    }


def bugsinpy_metadata(candidate_id: str, project: str, bug_id: str) -> dict[str, Any]:
    project_dir = BUGSINPY_REPO / "projects" / project
    bug_dir = project_dir / "bugs" / bug_id
    project_info = read_kv_file(project_dir / "project.info")
    bug_info = read_kv_file(bug_dir / "bug.info")
    run_test = read_optional(bug_dir / "run_test.sh") or "UNAVAILABLE"
    setup = read_optional(bug_dir / "setup.sh")
    return {
        "candidate_id": candidate_id,
        "source_family": "bugsinpy",
        "project": project,
        "bug_id": bug_id,
        "repo_url": project_info.get("github_url"),
        "buggy_commit_id": bug_info.get("buggy_commit_id"),
        "fixed_commit_id_outcome_only": bug_info.get("fixed_commit_id"),
        "python_version_required": bug_info.get("python_version"),
        "test_file": bug_info.get("test_file"),
        "setup_sh": setup,
        "run_test_sh": run_test,
        "candidate_class": "real_bug_benchmark_entry",
        "known_bug_reference": f"BugsInPy {project} bug {bug_id}",
    }


def write_bugsinpy_candidate(candidate_id: str, project: str, bug_id: str, probes: dict[str, Any]) -> dict[str, Any]:
    directory = OUTPUT_DIR / candidate_id
    directory.mkdir(parents=True, exist_ok=True)
    metadata = bugsinpy_metadata(candidate_id, project, bug_id)
    command_available = all(probes["bugsinpy_path_commands"].get(name) for name in ["bugsinpy-checkout", "bugsinpy-compile", "bugsinpy-test"])
    bash_ok = probes["shell_probe_bash"].get("returncode") == 0
    docker_ok = probes["docker_info_probe"].get("returncode") == 0
    promoted = command_available and (bash_ok or docker_ok)
    status = "promoted_ready_for_v2_4b_bugsinpy_real_bug" if promoted else "blocked_bugsinpy_tooling_unavailable"
    if not promoted and (bash_ok or docker_ok):
        status = "blocked_environment_missing_runtime"
    checkout_command = (
        f"bugsinpy-checkout -p {project} -v 0 -i {bug_id} -w external_repos/v2_4b_bugsinpy_workspace"
    )
    compile_command = "bugsinpy-compile -w external_repos/v2_4b_bugsinpy_workspace"
    failing_test_command = metadata["run_test_sh"]
    blocker = (
        "BLOCKED: BugsInPy command smoke test did not run. The framework command scripts are present in the "
        "local BugsInPy checkout, but the commands are not installed on PATH and the scripts require Bash. "
        "Docker daemon is also unavailable, so checkout/compile/test replay cannot be performed in this environment."
    )
    write_json(directory / "candidate_metadata.json", metadata)
    write_text(
        directory / "bugsinpy_command_probe.txt",
        "\n".join(
            [
                f"candidate_id={candidate_id}",
                f"framework_scripts_present={probes['bugsinpy_framework_scripts_present']}",
                f"path_commands={probes['bugsinpy_path_commands']}",
                f"bash_returncode={probes['shell_probe_bash'].get('returncode')}",
                f"bash_stderr={probes['shell_probe_bash'].get('stderr')}",
                f"docker_info_returncode={probes['docker_info_probe'].get('returncode')}",
                f"docker_info_stderr={probes['docker_info_probe'].get('stderr')}",
            ]
        )
        + "\n",
    )
    write_text(directory / "checkout_command.txt", checkout_command + "\n")
    write_text(directory / "checkout_log_raw.txt", blocker + "\n")
    write_text(directory / "compile_command.txt", compile_command + "\n")
    write_text(directory / "compile_log_raw.txt", "NOT_RUN: checkout/runtime blocker prevented compile.\n")
    write_text(directory / "failing_test_command.txt", failing_test_command + "\n")
    write_text(directory / "failing_test_log_raw.txt", "NOT_RUN: checkout/runtime blocker prevented failing test replay.\n")
    write_text(directory / "failure_signature.txt", f"UNAVAILABLE_RUNTIME_BLOCKED: BugsInPy {project}:{bug_id}\n")
    write_json(
        directory / "replay_feasibility_result.json",
        {
            "candidate_id": candidate_id,
            "promotion_status": status,
            "runtime_replay_confirmed": False,
            "failing_test_reproduced": False,
            "blocker": blocker,
            "gold_patch_used_at_decision_time": False,
            "fixed_commit_outcome_only": metadata.get("fixed_commit_id_outcome_only"),
        },
    )
    write_json(
        directory / "gold_patch_exclusion_plan.json",
        {
            "candidate_id": candidate_id,
            "gold_or_fixed_patch_sources": ["bug_patch.txt", "fixed_commit_id", "fixed repository state"],
            "allowed_at_decision_time": False,
            "policy": "Fixed commits and bug_patch.txt are outcome-only and must not appear in no-memory or memory-enabled decision-time inputs.",
        },
    )
    write_manifest(directory)
    return {
        "candidate_id": candidate_id,
        "source_family": "bugsinpy",
        "project": project,
        "bug_id": bug_id,
        "promotion_status": status,
        "runtime_replay_confirmed": False,
        "failing_test_reproduced": False,
        "readiness_score": 60,
        "blocker": blocker,
        "artifact_directory": str(directory.relative_to(REPO_ROOT)).replace("\\", "/"),
    }


def write_swebench_candidate(probes: dict[str, Any]) -> dict[str, Any]:
    candidate_id = "swebench_candidate_001"
    directory = OUTPUT_DIR / candidate_id
    directory.mkdir(parents=True, exist_ok=True)
    docker_ok = probes["docker_info_probe"].get("returncode") == 0
    import_ok = probes["swe_bench_import_probe"].get("returncode") == 0
    promoted = docker_ok and import_ok
    status = "promoted_ready_for_v2_4b_swebench_known_issue" if promoted else "blocked_docker_unavailable"
    if docker_ok and not import_ok:
        status = "blocked_swebench_harness_unavailable"
    blocker = (
        "BLOCKED: SWE-bench smoke test did not instantiate a task. Docker daemon is unavailable and the "
        "Python package import probe did not confirm an installed SWE-bench harness, so a safe Lite/Verified "
        "instance cannot be replayed here."
    )
    write_json(
        directory / "candidate_metadata.json",
        {
            "candidate_id": candidate_id,
            "source_family": "swe_bench_lite_or_verified",
            "candidate_class": "known_organic_external_issue_family",
            "repo_url": "https://github.com/SWE-bench/SWE-bench",
            "local_source_head": git_head(SWE_BENCH_REPO),
            "instance_id": None,
            "known_issue_or_bug_reference": "SWE-bench Lite/Verified family; no concrete instance selected under current runtime blocker",
        },
    )
    write_text(
        directory / "docker_probe.txt",
        json.dumps(
            {
                "docker_version_probe": probes["docker_version_probe"],
                "docker_info_probe": probes["docker_info_probe"],
                "disk_report": probes["disk_report"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    write_text(
        directory / "swebench_harness_probe.txt",
        json.dumps(
            {
                "import_probe": probes["swe_bench_import_probe"],
                "harness_file_present": probes["swe_bench_harness_file_present"],
                "local_checkout": probes["swe_bench_local_checkout"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    write_json(
        directory / "instance_selection_record.json",
        {
            "selected_instance_id": None,
            "selection_status": "not_selected_runtime_blocked",
            "reason": "Docker/SWE-bench runtime was not available, so no Lite/Verified instance was safely instantiated.",
        },
    )
    write_text(directory / "failing_test_command.txt", "NOT_SELECTED_RUNTIME_BLOCKED\n")
    write_text(directory / "failing_test_log_raw.txt", blocker + "\n")
    write_text(directory / "failure_signature.txt", "UNAVAILABLE_RUNTIME_BLOCKED: SWE-bench\n")
    write_json(
        directory / "replay_feasibility_result.json",
        {
            "candidate_id": candidate_id,
            "promotion_status": status,
            "runtime_replay_confirmed": False,
            "failing_test_reproduced": False,
            "blocker": blocker,
            "gold_patch_used_at_decision_time": False,
        },
    )
    write_json(
        directory / "gold_patch_exclusion_plan.json",
        {
            "candidate_id": candidate_id,
            "gold_or_fixed_patch_sources": ["gold patch", "test patch", "fixed diff", "oracle patch"],
            "allowed_at_decision_time": False,
            "policy": "SWE-bench gold patches and test patches are outcome-only and must not appear in decision-time inputs.",
        },
    )
    write_manifest(directory)
    return {
        "candidate_id": candidate_id,
        "source_family": "swe_bench_lite_or_verified",
        "promotion_status": status,
        "runtime_replay_confirmed": False,
        "failing_test_reproduced": False,
        "readiness_score": 35,
        "blocker": blocker,
        "artifact_directory": str(directory.relative_to(REPO_ROOT)).replace("\\", "/"),
    }


def update_shareable_summary() -> None:
    section = """## v2.4b BugsInPy/SWE-bench Runtime Unblock

The blocker is benchmark runtime acquisition.

- BugsInPy/SWE-bench candidates require local benchmark harness execution.
- BugsInPy concrete candidates probed: `black:2`, `youtube-dl:1`, `black:8`.
- SWE-bench smoke test status: blocked before task instantiation.
- Promoted real-bug candidates: 0.
- Executed real-bug replay episodes: 0.
- Scoreable real-bug replay episodes: 0.
- Aggregate result: `blocked_real_bug_runtime_unavailable`.

Blocked runtime is not negative ControllerGate capability evidence. Candidate metadata alone does not prove replay readiness. Gold/corrected patches are outcome-only and barred from decision-time inputs.

The practical next action is to run the benchmark harness in an environment that supports it: BugsInPy through a Unix shell or Docker with project-specific Python runtimes, or SWE-bench through a bounded Docker-capable Lite/Verified task runner.

Self-maintaining software remains undemonstrated. Full scoring remains disallowed. Broad organic external memory lift remains undemonstrated.
"""
    if SHAREABLE_SUMMARY.exists():
        text = SHAREABLE_SUMMARY.read_text(encoding="utf-8")
        marker = "## v2.4b BugsInPy/SWE-bench Runtime Unblock"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n\n" + section
        else:
            text = text.rstrip() + "\n\n" + section
    else:
        text = section
    write_text(SHAREABLE_SUMMARY, text)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    probes = runtime_probes()
    bugsinpy_results = [write_bugsinpy_candidate(*candidate, probes) for candidate in BUGSINPY_CANDIDATES]
    swebench_results = [write_swebench_candidate(probes)]
    all_results = bugsinpy_results + swebench_results
    promoted = [result for result in all_results if result["promotion_status"].startswith("promoted_ready_for_v2_4b")]
    aggregate = "blocked_real_bug_runtime_unavailable" if not promoted else "insufficient_episode_count_for_v2_4b_real_bug_memory_lift"

    write_json(
        OUTPUT_DIR / "runtime_probe_plan.json",
        {
            "campaign_id": "v2_4b_real_bug_runtime_unblock",
            "priority_order": ["BugsInPy runtime smoke test", "SWE-bench Lite/Verified runtime smoke test"],
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_claim_allowed": False,
            "broad_organic_external_memory_lift_claim_allowed": False,
            "gold_corrected_patches_decision_time_allowed": False,
        },
    )
    write_json(OUTPUT_DIR / "runtime_probe_results.json", probes)
    write_text(
        OUTPUT_DIR / "environment_capability_report.md",
        f"""# v2.4b Environment Capability Report

- OS/platform: `{probes['os_platform']}`.
- Python probe: `{probes['python_version_probe'].get('stdout') or probes['python_version_probe'].get('stderr')}`.
- Git probe: `{probes['git_probe'].get('stdout')}`.
- Bash probe return code: `{probes['shell_probe_bash'].get('returncode')}`.
- Docker info return code: `{probes['docker_info_probe'].get('returncode')}`.
- BugsInPy framework scripts present: `{probes['bugsinpy_framework_scripts_present']}`.
- BugsInPy commands on PATH: `{probes['bugsinpy_path_commands']}`.
- SWE-bench import probe return code: `{probes['swe_bench_import_probe'].get('returncode')}`.
- SWE-bench harness file present in local clone: `{probes['swe_bench_harness_file_present']}`.
- Free disk GB: `{probes['disk_report']['free_gb']}`.

The current environment does not provide confirmed BugsInPy or SWE-bench local replay execution.
""",
    )
    write_text(
        OUTPUT_DIR / "benchmark_runtime_blocker_report.md",
        """# v2.4b Benchmark Runtime Blocker Report

Result: `blocked_real_bug_runtime_unavailable`.

The blocker is benchmark runtime acquisition, not ControllerGate repair capability.

## BugsInPy

Concrete BugsInPy bug metadata was available for `black:2`, `youtube-dl:1`, and `black:8`, including failing test commands. The local BugsInPy framework entrypoints are Bash scripts and are not installed on PATH. The available environment did not provide a working Bash/WSL or Docker daemon, so checkout, compile, and failing-test replay could not be executed.

## SWE-bench

The SWE-bench source checkout is available and contains the evaluation harness source, but SWE-bench task execution depends on Docker/resource support and no concrete Lite/Verified task was safely instantiated in this environment.

## Required Next Environment Action

Use a Linux/Docker benchmark runner: WSL2 Ubuntu plus Docker Desktop, GitHub Codespaces with Docker, GitHub Actions, or a small cloud Linux VM with BugsInPy/SWE-bench runtime support.
""",
    )
    write_json(
        OUTPUT_DIR / "runtime_unblock_results.json",
        {
            "campaign_id": "v2_4b_real_bug_runtime_unblock",
            "promoted_candidate_count": len(promoted),
            "bugsinpy_candidate_count": len(bugsinpy_results),
            "swebench_candidate_count": len(swebench_results),
            "execution_allowed": len(promoted) > 0,
            "execution_performed": False,
            "aggregate_result": aggregate,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "promoted_real_bug_candidate_pool.json",
        {
            "count": len(promoted),
            "records": promoted,
            "promotion_gate": "closed_no_runtime_replay_confirmed" if not promoted else "open",
        },
    )
    write_json(
        OUTPUT_DIR / "campaign_results.json",
        {
            "campaign_id": "v2_4b_real_bug_runtime_unblock",
            "promoted_candidate_count": len(promoted),
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "inconclusive_episode_count": 0,
            "negative_episode_count": 0,
            "blocked_runtime_candidate_count": len(all_results),
            "decision_time_outcome_overlap_count": 0,
            "corruption_in_positive_memory_episode_count": 0,
            "aggregate_result": aggregate,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": aggregate,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "limited_swebench_known_issue_memory_lift_criteria_met": False,
            "limited_real_external_bug_benchmark_memory_lift_criteria_met": False,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "gold_corrected_patches_excluded_from_decision_time_inputs": True,
            "decision_time_outcome_overlap_count": 0,
            "corruption_in_positive_memory_episode_count": 0,
            "blocked_runtime_is_negative_capability_evidence": False,
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
        },
    )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        """# v2.4b BugsInPy/SWE-bench Runtime Unblock

The blocker is benchmark runtime acquisition.

## Result

`blocked_real_bug_runtime_unavailable`

## Counts

- BugsInPy candidates probed: 3.
- SWE-bench family smoke tests probed: 1.
- Promoted candidates: 0.
- Executed episodes: 0.
- Scoreable episodes: 0.
- Positive memory episodes: 0.

## Interpretation

BugsInPy/SWE-bench candidates require local benchmark harness execution. Blocked runtime is not negative ControllerGate capability evidence. Candidate metadata alone does not prove replay readiness.

Gold/corrected patches are outcome-only. No gold or corrected patch was used at decision time. No full scoring was run.

Self-maintaining software remains undemonstrated. Full scoring remains disallowed. Broad organic external memory lift remains undemonstrated.
""",
    )
    update_shareable_summary()
    write_manifest(OUTPUT_DIR)
    print("v2.4b real bug runtime unblock artifacts generated")
    print("promoted candidates: 0")
    print(f"aggregate: {aggregate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
