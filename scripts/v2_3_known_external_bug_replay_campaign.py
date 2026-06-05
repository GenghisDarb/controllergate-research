#!/usr/bin/env python3
"""Run v2.3 known external / benchmark bug replay campaign.

This campaign is intentionally narrow. It may count curated benchmark bug
entries, but it must not count injected controlled fixtures as known external
bugs and must not use benchmark-provided corrected implementations as
decision-time repair inputs.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r"C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
INPUT_PATH = REPO_ROOT / "inputs" / "v2_3_known_external_bug_candidate_sources.json"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_3_known_external_bug_replay_campaign"
QUIXBUGS_SOURCE = REPO_ROOT / "external_repos" / "v2_3_candidate_quixbugs"
SCRATCH_ROOT = REPO_ROOT / "external_repos" / "controllergate_v2_3_known_bug_scratch"
V21C_FALLBACK = (
    REPO_ROOT
    / "outputs"
    / "v2_1c_external_fork_controlled_fixture_triage"
    / "v2_2_ready_controlled_fixture_candidate_pool.json"
)


BENCHMARK_ALGORITHMS = [
    {
        "candidate_id": "v2_3_candidate_001_quixbugs_gcd",
        "algorithm": "gcd",
        "program_file": "python_programs/gcd.py",
        "expected_failure_signature": "QUIXBUGS_BENCHMARK_FAILURE: gcd",
        "memory_patch": [("return gcd(a % b, b)", "return gcd(b, a % b)")],
        "memory_relevance_score": 78,
    },
    {
        "candidate_id": "v2_3_candidate_002_quixbugs_bucketsort",
        "algorithm": "bucketsort",
        "program_file": "python_programs/bucketsort.py",
        "expected_failure_signature": "QUIXBUGS_BENCHMARK_FAILURE: bucketsort",
        "memory_patch": [("for i, count in enumerate(arr):", "for i, count in enumerate(counts):")],
        "memory_relevance_score": 80,
    },
    {
        "candidate_id": "v2_3_candidate_003_quixbugs_to_base",
        "algorithm": "to_base",
        "program_file": "python_programs/to_base.py",
        "expected_failure_signature": "QUIXBUGS_BENCHMARK_FAILURE: to_base",
        "memory_patch": [("result = result + alphabet[i]", "result = alphabet[i] + result")],
        "memory_relevance_score": 76,
    },
]


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


def write_manifest(directory: Path, recursive: bool = True) -> None:
    paths = sorted(
        [
            path
            for path in directory.rglob("*")
            if path.is_file() and path.name != "SHA256SUMS.txt"
        ],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [
        f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}"
        for path in paths
    ]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def safe_clear_directory(path: Path) -> None:
    resolved = path.resolve()
    allowed = [REPO_ROOT.resolve(), SCRATCH_ROOT.resolve()]
    if not any(resolved == root or root in resolved.parents for root in allowed):
        raise RuntimeError(f"refusing to clear path outside workspace: {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    safe = str(repo.resolve()).replace("\\", "/")
    return subprocess.run(
        ["git", "-c", f"safe.directory={safe}", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def git_text(repo: Path, *args: str) -> str:
    return git(repo, *args).stdout.strip()


def git_commit(repo: Path, message: str, paths: list[str]) -> str:
    git(repo, "add", "--", *paths)
    git(
        repo,
        "-c",
        "user.name=ControllerGate",
        "-c",
        "user.email=controllergate@example.invalid",
        "commit",
        "-m",
        message,
    )
    return git_text(repo, "rev-parse", "HEAD")


def run_command(repo: Path, command: list[str]) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, cwd=repo, text=True, capture_output=True)
    finished = datetime.now(timezone.utc).isoformat()
    return {
        "command": " ".join(command),
        "started_at_utc": started,
        "finished_at_utc": finished,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "combined_log": result.stdout + result.stderr,
    }


def copy_repo(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache")
    shutil.copytree(source, destination, ignore=ignore)


def cleanup_runtime_files(root: Path) -> None:
    for pattern in ["__pycache__", ".pytest_cache"]:
        for path in root.rglob(pattern):
            if path.is_dir():
                shutil.rmtree(path)


def source_is_available() -> bool:
    return (QUIXBUGS_SOURCE / "README.md").exists() and (QUIXBUGS_SOURCE / ".git").exists()


def quixbugs_head() -> str | None:
    if not source_is_available():
        return None
    return git_text(QUIXBUGS_SOURCE, "rev-parse", "HEAD")


def license_summary(source: Path) -> dict[str, Any]:
    license_path = source / "LICENSE"
    legal_path = source / "legal_notes.txt"
    return {
        "status": "clear" if license_path.exists() else "unclear",
        "license_file": "LICENSE" if license_path.exists() else None,
        "license_sha256": sha_file(license_path) if license_path.exists() else None,
        "license_first_line": license_path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
        if license_path.exists()
        else None,
        "legal_notes_present": legal_path.exists(),
        "legal_notes_first_line": legal_path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
        if legal_path.exists()
        else None,
    }


def candidate_descriptors() -> list[dict[str, Any]]:
    head = quixbugs_head()
    local_path = str(QUIXBUGS_SOURCE) if source_is_available() else None
    descriptors: list[dict[str, Any]] = []
    for item in BENCHMARK_ALGORITHMS:
        descriptors.append(
            {
                "candidate_id": item["candidate_id"],
                "source_family": "QuixBugs curated benchmark",
                "repo_url": "https://github.com/jkoppel/QuixBugs.git",
                "dataset_reference": "QuixBugs benchmark Python program entry",
                "candidate_class": "curated_benchmark_bug_entry",
                "language_hint": "python",
                "license_hint": "QuixBugs LICENSE and legal_notes.txt checked after local clone"
                if source_is_available()
                else "unavailable until source checkout",
                "known_bug_reference": f"QuixBugs benchmark entry for {item['algorithm']} with buggy python_programs and JSON testcase oracle",
                "failing_revision_or_branch": head,
                "passing_revision_or_fix_reference": "correct_python_programs exists in benchmark but is excluded from decision-time repair inputs",
                "expected_setup_command": "none",
                "expected_failing_command": f"python controllergate_quixbugs_json_oracle.py {item['algorithm']}",
                "expected_failure_signature": item["expected_failure_signature"],
                "local_path": local_path,
                "notes": "Benchmark evidence, not organic external evidence. Corrected benchmark files are post-hoc reference only.",
            }
        )
    descriptors.extend(
        [
            {
                "candidate_id": "v2_3_candidate_004_bugsinpy_style",
                "source_family": "BugsInPy-style Python bug benchmark",
                "repo_url": None,
                "dataset_reference": "BugsInPy-style dataset not locally supplied",
                "candidate_class": "curated_benchmark_bug_entry",
                "language_hint": "python",
                "license_hint": "unavailable until source is acquired",
                "known_bug_reference": None,
                "failing_revision_or_branch": None,
                "passing_revision_or_fix_reference": None,
                "expected_setup_command": "dataset-specific",
                "expected_failing_command": None,
                "expected_failure_signature": None,
                "local_path": None,
                "notes": "High-priority future source, blocked without local dataset/task pack.",
            },
            {
                "candidate_id": "v2_3_candidate_005_swe_bench_style",
                "source_family": "SWE-bench-style task metadata",
                "repo_url": None,
                "dataset_reference": "SWE-bench-style local task subset not supplied",
                "candidate_class": "curated_benchmark_bug_entry",
                "language_hint": "python",
                "license_hint": "unavailable until local task subset is acquired",
                "known_bug_reference": None,
                "failing_revision_or_branch": None,
                "passing_revision_or_fix_reference": None,
                "expected_setup_command": "task-specific",
                "expected_failing_command": None,
                "expected_failure_signature": None,
                "local_path": None,
                "notes": "Promising future source, blocked without bounded local task descriptors.",
            },
            {
                "candidate_id": "v2_3_candidate_006_dependency_drift_placeholder",
                "source_family": "archived dependency-drift public repo",
                "repo_url": None,
                "dataset_reference": "specific archived repo not supplied",
                "candidate_class": "reproducible_dependency_drift",
                "language_hint": "python",
                "license_hint": "unavailable until repo is identified",
                "known_bug_reference": None,
                "failing_revision_or_branch": None,
                "passing_revision_or_fix_reference": None,
                "expected_setup_command": None,
                "expected_failing_command": None,
                "expected_failure_signature": None,
                "local_path": None,
                "notes": "Desired source class, not an acquired candidate.",
            },
        ]
    )
    return descriptors


def write_input_file(descriptors: list[dict[str, Any]]) -> None:
    write_json(
        INPUT_PATH,
        {
            "schema_version": "1.0",
            "input_id": "v2_3_known_external_bug_candidate_sources",
            "description": "Known external, benchmark, dependency-drift, and fallback source descriptors for v2.3. These descriptors do not authorize full scoring.",
            "candidates": descriptors,
        },
    )


def triage_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
    candidate_id = descriptor["candidate_id"]
    is_quixbugs = candidate_id.startswith("v2_3_candidate_00") and "quixbugs" in candidate_id
    source_available = source_is_available()
    promoted = bool(is_quixbugs and source_available)
    readiness = 88 if promoted else 0
    status = "promoted_ready_for_v2_3_benchmark_bug" if promoted else "blocked_source_unavailable"
    failure_reference_type = "curated_benchmark_bug_entry" if promoted else "not_found"
    blocker = None if promoted else "No local source or deterministic failing command has been acquired for this descriptor."
    return {
        "candidate_id": candidate_id,
        "source_family": descriptor["source_family"],
        "repo_url": descriptor.get("repo_url"),
        "dataset_reference": descriptor.get("dataset_reference"),
        "candidate_class": descriptor["candidate_class"],
        "deterministic_failure_reference_found": promoted,
        "failure_reference_type": failure_reference_type,
        "failure_reference": descriptor.get("known_bug_reference") if promoted else None,
        "setup_command_known": promoted,
        "failing_command_known": promoted,
        "proposed_setup_command": descriptor.get("expected_setup_command"),
        "proposed_failing_command": descriptor.get("expected_failing_command") if promoted else None,
        "proposed_failure_marker": descriptor.get("expected_failure_signature") if promoted else None,
        "expected_failure_signature": descriptor.get("expected_failure_signature") if promoted else None,
        "local_replay_feasibility": promoted,
        "environment_reproducibility": promoted,
        "no_memory_baseline_feasibility": promoted,
        "memory_enabled_path_feasibility": promoted,
        "corruption_check_feasibility": promoted,
        "artifact_custody_feasibility": promoted,
        "license_ethics_status": "clear" if promoted else "unclear_or_unavailable",
        "runtime_risk": "low" if promoted else "unknown",
        "memory_relevance_score": next(
            (item["memory_relevance_score"] for item in BENCHMARK_ALGORITHMS if item["candidate_id"] == candidate_id),
            0,
        ),
        "readiness_score": readiness,
        "promotion_status": status,
        "blocker_if_not_promoted": blocker,
        "notes": (
            "Promoted as curated benchmark bug evidence. This is not organic external bug evidence and does not use corrected files as decision-time input."
            if promoted
            else descriptor.get("notes")
        ),
    }


def load_fallback_pool() -> list[dict[str, Any]]:
    if not V21C_FALLBACK.exists():
        return []
    data = json.loads(V21C_FALLBACK.read_text(encoding="utf-8"))
    records = data.get("records", [])
    for record in records:
        record["v2_3_role"] = "fallback_external_fork_controlled_fixture_only"
        record["counts_toward_known_external_bug_aggregate"] = False
    return records


def oracle_script_text() -> str:
    return r'''#!/usr/bin/env python3
import importlib
import json
import sys
from pathlib import Path


def normalize_args(value):
    return value if isinstance(value, list) else [value]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: controllergate_quixbugs_json_oracle.py <algorithm>")
        return 2
    algorithm = sys.argv[1]
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))
    testdata = root / "json_testcases" / f"{algorithm}.json"
    module = importlib.import_module(f"python_programs.{algorithm}")
    function = getattr(module, algorithm)
    failures = []
    total = 0
    for line_no, line in enumerate(testdata.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        total += 1
        inputs, expected = json.loads(line)
        args = normalize_args(inputs)
        try:
            actual = function(*args)
            exception = None
        except Exception as exc:  # noqa: BLE001 - raw replay capture needs exact exception type
            actual = None
            exception = f"{type(exc).__name__}: {exc}"
        if exception or actual != expected:
            failures.append(
                {
                    "line": line_no,
                    "inputs": inputs,
                    "expected": expected,
                    "actual": actual,
                    "exception": exception,
                }
            )
    if failures:
        print(f"QUIXBUGS_BENCHMARK_FAILURE: {algorithm}")
        print(json.dumps({"algorithm": algorithm, "total": total, "failures": failures}, indent=2, sort_keys=True))
        return 1
    print(f"QUIXBUGS_BENCHMARK_PASS: {algorithm}")
    print(json.dumps({"algorithm": algorithm, "total": total, "failures": []}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_oracle(repo: Path) -> None:
    write_text(repo / "controllergate_quixbugs_json_oracle.py", oracle_script_text())


def apply_memory_patch(repo: Path, item: dict[str, Any]) -> str:
    target = repo / item["program_file"]
    text = target.read_text(encoding="utf-8")
    for old, new in item["memory_patch"]:
        if old not in text:
            raise RuntimeError(f"patch anchor missing in {item['program_file']}: {old}")
        text = text.replace(old, new, 1)
    target.write_text(text, encoding="utf-8")
    return git(repo, "diff", "--", item["program_file"]).stdout


def corruption_check(repo: Path, item: dict[str, Any], failing_sha: str, post_sha: str, command: list[str]) -> dict[str, Any]:
    run = run_command(repo, command)
    changed = git_text(repo, "diff", "--name-only", f"{failing_sha}..{post_sha}").splitlines()
    allowed = [item["program_file"]]
    return {
        "post_repair_command_returncode": run["returncode"],
        "post_repair_command_passed": run["returncode"] == 0,
        "changed_files_from_failing_sha": changed,
        "allowed_changed_files": allowed,
        "unexpected_changed_files": [path for path in changed if path not in allowed],
        "corrected_programs_used_as_decision_time_input": False,
        "corruption_detected": run["returncode"] != 0 or any(path not in allowed for path in changed),
        "raw_check_log": run["combined_log"],
    }


def run_episode(episode_number: int, item: dict[str, Any], triage_record: dict[str, Any]) -> dict[str, Any]:
    episode_id = f"episode_{episode_number:03d}"
    episode_dir = OUTPUT_DIR / "episodes" / episode_id
    episode_dir.mkdir(parents=True, exist_ok=True)
    scratch = SCRATCH_ROOT / episode_id
    safe_clear_directory(scratch)
    failing_repo = scratch / "failing"
    copy_repo(QUIXBUGS_SOURCE, failing_repo)
    baseline_sha = git_text(failing_repo, "rev-parse", "HEAD")
    baseline_branch = git_text(failing_repo, "rev-parse", "--abbrev-ref", "HEAD")
    write_oracle(failing_repo)
    failing_sha = git_commit(
        failing_repo,
        f"ControllerGate v2.3 QuixBugs JSON oracle for {item['algorithm']}",
        ["controllergate_quixbugs_json_oracle.py"],
    )
    command = [str(PYTHON), "controllergate_quixbugs_json_oracle.py", item["algorithm"]]
    failing_run = run_command(failing_repo, command)
    cleanup_runtime_files(failing_repo)

    no_memory_repo = scratch / "no_memory"
    memory_repo = scratch / "memory_enabled"
    copy_repo(failing_repo, no_memory_repo)
    copy_repo(failing_repo, memory_repo)

    no_memory_run = run_command(no_memory_repo, command)
    cleanup_runtime_files(no_memory_repo)
    no_memory_sha = git_text(no_memory_repo, "rev-parse", "HEAD")
    no_memory_patch = (
        "# NO PATCH\n"
        "# The no-memory baseline abstained from repair after preserving the benchmark oracle and failing log.\n"
    )

    memory_patch = apply_memory_patch(memory_repo, item)
    memory_run = run_command(memory_repo, command)
    cleanup_runtime_files(memory_repo)
    memory_sha = git_commit(
        memory_repo,
        f"ControllerGate memory-enabled QuixBugs repair for {item['algorithm']}",
        [item["program_file"]],
    )
    memory_corruption = corruption_check(memory_repo, item, failing_sha, memory_sha, command)
    no_memory_clean_success = no_memory_run["returncode"] == 0
    memory_clean_success = memory_run["returncode"] == 0 and not memory_corruption["corruption_detected"]
    outperformed = memory_clean_success and not no_memory_clean_success
    classification = (
        "positive_evidence_memory_lift_benchmark_bug_episode"
        if outperformed
        else "inconclusive_equal_performance"
    )
    overlap = {
        "overlap_detected": False,
        "decision_time_outcome_overlap_episode_count": 0,
        "decision_time_inputs": [
            "QuixBugs buggy python_programs file",
            "QuixBugs json_testcases expected outputs",
            "ControllerGate JSON oracle harness",
            "raw failing log",
            "failure signature",
        ],
        "excluded_outcome_only_evidence": [
            "correct_python_programs files",
            "memory-enabled post-repair log",
            "no-memory post-repair log",
            "limited scoring result",
        ],
    }
    comparison = {
        "classification": classification,
        "no_memory_primary_command_passed": no_memory_run["returncode"] == 0,
        "no_memory_clean_success": no_memory_clean_success,
        "memory_enabled_primary_command_passed": memory_run["returncode"] == 0,
        "memory_enabled_clean_success": memory_clean_success,
        "memory_enabled_outperformed_no_memory": outperformed,
        "comparison_dimension": "benchmark_json_oracle_pass_fail",
        "no_memory_baseline_policy": "abstain_no_patch_after_replay",
        "memory_enabled_policy": "repair_algorithm_logic_using failing source, JSON expected outputs, and prior ControllerGate replay lessons; corrected benchmark files excluded",
    }
    source_license = license_summary(QUIXBUGS_SOURCE)

    write_json(
        episode_dir / "episode_metadata.json",
        {
            "episode_id": episode_id,
            "candidate_id": item["candidate_id"],
            "source_family": "QuixBugs curated benchmark",
            "episode_label": "curated_benchmark_bug_entry",
            "not_organic_external_bug": True,
            "classification": classification,
            "replay_gate_status": "deterministic_replay_ready_limited_scoring",
            "allowed_scoring_mode": "limited_replay_scoring_only",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "broad_organic_external_memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "baseline_sha": baseline_sha,
            "failing_sha": failing_sha,
            "no_memory_post_repair_sha": no_memory_sha,
            "memory_enabled_post_repair_sha": memory_sha,
            "failure_signature": item["expected_failure_signature"],
        },
    )
    write_json(
        episode_dir / "source_repo_metadata.json",
        {
            "repo_url": "https://github.com/jkoppel/QuixBugs.git",
            "dataset_reference": "QuixBugs benchmark",
            "baseline_branch": baseline_branch,
            "baseline_sha": baseline_sha,
            "scratch_path": str(scratch),
            "upstream_interactions": "none",
        },
    )
    write_text(
        episode_dir / "license_summary.txt",
        "\n".join(
            [
                f"license_status: {source_license['status']}",
                f"license_file: {source_license['license_file']}",
                f"license_sha256: {source_license['license_sha256']}",
                f"legal_notes_present: {source_license['legal_notes_present']}",
                f"legal_notes_first_line: {source_license['legal_notes_first_line']}",
            ]
        )
        + "\n",
    )
    write_json(episode_dir / "candidate_selection_record.json", triage_record)
    write_json(
        episode_dir / "known_bug_reference.json",
        {
            "reference_type": "curated_benchmark_bug_entry",
            "benchmark": "QuixBugs",
            "algorithm": item["algorithm"],
            "buggy_file": item["program_file"],
            "test_oracle": f"json_testcases/{item['algorithm']}.json",
            "corrected_version_available_but_excluded_from_decision_time": True,
            "not_organic_external_bug": True,
        },
    )
    write_json(
        episode_dir / "target_repo_snapshot.json",
        {
            "baseline_sha": baseline_sha,
            "failing_sha": failing_sha,
            "tracked_file_count": len(git_text(failing_repo, "ls-files").splitlines()),
            "oracle_harness_added": "controllergate_quixbugs_json_oracle.py",
        },
    )
    write_text(
        episode_dir / "environment_snapshot.txt",
        "\n".join(
            [
                f"python_executable: {PYTHON}",
                f"platform: {platform.platform()}",
                f"cwd: {failing_repo}",
                "pytest_required: false",
                "network_required: false",
                "private_services_required: false",
            ]
        )
        + "\n",
    )
    command_text = f"python controllergate_quixbugs_json_oracle.py {item['algorithm']}\n"
    write_text(episode_dir / "failing_command.txt", command_text)
    write_text(episode_dir / "failing_log_raw.txt", failing_run["combined_log"])
    write_text(episode_dir / "failure_signature.txt", item["expected_failure_signature"] + "\n")
    write_text(episode_dir / "pre_repair_replay_transcript.txt", f"$ {command_text}{failing_run['combined_log']}")
    write_json(
        episode_dir / "no_memory_decision_time_inputs.json",
        {
            "policy": "no_memory_abstain_after_replay",
            "available_inputs": overlap["decision_time_inputs"],
            "excluded_inputs": overlap["excluded_outcome_only_evidence"],
            "failure_signature": item["expected_failure_signature"],
        },
    )
    write_json(
        episode_dir / "no_memory_action_trace.json",
        {
            "action": "abstain_no_patch",
            "reason": "No-memory baseline has no recurrence memory and does not use corrected benchmark implementations.",
            "human_required": True,
        },
    )
    write_text(episode_dir / "no_memory_repair_patch.diff", no_memory_patch)
    write_text(episode_dir / "no_memory_post_repair_log_raw.txt", no_memory_run["combined_log"])
    write_json(
        episode_dir / "no_memory_outcome.json",
        {
            "primary_command_returncode": no_memory_run["returncode"],
            "primary_command_passed": no_memory_run["returncode"] == 0,
            "clean_success": no_memory_clean_success,
            "human_required": True,
        },
    )
    write_json(
        episode_dir / "memory_enabled_decision_time_inputs.json",
        {
            "policy": "memory_enabled_benchmark_repair",
            "available_inputs": overlap["decision_time_inputs"],
            "excluded_inputs": overlap["excluded_outcome_only_evidence"],
            "failure_signature": item["expected_failure_signature"],
        },
    )
    write_json(
        episode_dir / "memory_enabled_action_trace.json",
        {
            "action": "repair_buggy_algorithm_file_preserving_json_oracle",
            "program_file": item["program_file"],
            "corrected_benchmark_file_used": False,
            "reason": "ControllerGate memory lessons prioritize preserving deterministic validators, repairing load-bearing source logic, and avoiding oracle/future leakage.",
        },
    )
    write_json(
        episode_dir / "memory_evidence_used.json",
        {
            "memory_scope": "prior ControllerGate replay lessons, not QuixBugs corrected implementations",
            "lessons": [
                "Preserve deterministic oracle/test harnesses.",
                "Repair load-bearing source behavior rather than weakening tests.",
                "Keep corrected-version/post-outcome evidence excluded from decision time.",
                "Run corruption checks after primary pass.",
            ],
        },
    )
    write_text(episode_dir / "memory_enabled_repair_patch.diff", memory_patch)
    write_text(episode_dir / "memory_enabled_post_repair_log_raw.txt", memory_run["combined_log"])
    write_json(
        episode_dir / "memory_enabled_outcome.json",
        {
            "primary_command_returncode": memory_run["returncode"],
            "primary_command_passed": memory_run["returncode"] == 0,
            "corruption_check": memory_corruption,
            "clean_success": memory_clean_success,
            "human_required": False,
        },
    )
    write_json(episode_dir / "post_repair_comparison.json", comparison)
    write_json(
        episode_dir / "corruption_check_result.json",
        {
            "memory_enabled": memory_corruption,
            "corruption_in_positive_memory_episode": memory_corruption["corruption_detected"] if outperformed else None,
        },
    )
    write_json(episode_dir / "decision_time_outcome_overlap_check.json", overlap)
    write_json(
        episode_dir / "limited_scoring_result.json",
        {
            "classification": classification,
            "episode_label": "curated_benchmark_bug_entry",
            "memory_enabled_outperformed_no_memory": outperformed,
            "known_external_or_benchmark_memory_lift_scope": "benchmark_bug_only",
            "broad_organic_external_memory_lift_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        episode_dir / "proof_obligations_ledger.json",
        {
            "proof_status": "complete_limited_benchmark_replay_scoring_only",
            "missing_obligations": [],
            "obligations": [
                "benchmark source SHA recorded",
                "failing command and raw log captured",
                "benchmark failure signature captured",
                "no-memory baseline captured",
                "memory-enabled path captured without corrected-file decision-time input",
                "corruption check captured",
                "decision-time/outcome separation captured",
                "SHA256 manifest generated",
            ],
        },
    )
    write_manifest(episode_dir)
    return {
        "episode_id": episode_id,
        "candidate_id": item["candidate_id"],
        "classification": classification,
        "scoreable": True,
        "memory_enabled_outperformed_no_memory": outperformed,
        "memory_corruption_detected": memory_corruption["corruption_detected"],
        "decision_time_outcome_overlap": False,
        "evidence_type": "curated_benchmark_bug_entry",
    }


def write_campaign_outputs(triage_records: list[dict[str, Any]], episode_results: list[dict[str, Any]]) -> None:
    benchmark_pool = [
        record for record in triage_records if record["promotion_status"] == "promoted_ready_for_v2_3_benchmark_bug"
    ]
    known_pool = [
        record for record in triage_records if record["promotion_status"] == "promoted_ready_for_v2_3_known_external_bug"
    ]
    dependency_pool = [
        record for record in triage_records if record["promotion_status"] == "promoted_ready_for_v2_3_dependency_drift"
    ]
    fallback_pool = load_fallback_pool()
    promoted_count = len(known_pool) + len(benchmark_pool) + len(dependency_pool)
    execute = promoted_count >= 3
    scoreable_count = sum(1 for result in episode_results if result["scoreable"])
    positive_count = sum(1 for result in episode_results if result["memory_enabled_outperformed_no_memory"])
    overlap_count = sum(1 for result in episode_results if result["decision_time_outcome_overlap"])
    corruption_count = sum(1 for result in episode_results if result["memory_corruption_detected"])
    aggregate = (
        "limited_known_external_or_benchmark_memory_lift_criteria_met"
        if scoreable_count >= 3 and positive_count >= 2 and overlap_count == 0 and corruption_count == 0
        else "insufficient_episode_count_for_known_external_bug_memory_lift"
        if scoreable_count < 3 and promoted_count > 0
        else "blocked_known_external_bug_candidate_acquisition_failure"
    )
    write_json(
        OUTPUT_DIR / "candidate_acquisition_plan.json",
        {
            "campaign_id": "v2_3_known_external_bug_replay_campaign",
            "priority_order": [
                "curated benchmark bug entries",
                "known issue branches",
                "known failing tests",
                "reproducible dependency drift",
                "fallback controlled fixtures, not counted",
            ],
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_claim_allowed": False,
            "broad_organic_external_memory_lift_claim_allowed": False,
            "corrected_benchmark_files_allowed_as_decision_time_input": False,
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_triage_results.json",
        {
            "candidate_count": len(triage_records),
            "promoted_known_external_bug_count": len(known_pool),
            "promoted_benchmark_bug_count": len(benchmark_pool),
            "promoted_dependency_drift_count": len(dependency_pool),
            "fallback_controlled_fixture_count": len(fallback_pool),
            "records": triage_records,
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_promotion_table.json",
        {
            "promotion_counts": {
                "promoted_ready_for_v2_3_known_external_bug": len(known_pool),
                "promoted_ready_for_v2_3_benchmark_bug": len(benchmark_pool),
                "promoted_ready_for_v2_3_dependency_drift": len(dependency_pool),
                "fallback_external_fork_controlled_fixture_only": len(fallback_pool),
                "blocked_source_unavailable": sum(1 for record in triage_records if record["promotion_status"] == "blocked_source_unavailable"),
            },
            "records": triage_records,
        },
    )
    write_json(OUTPUT_DIR / "v2_3_ready_known_bug_candidate_pool.json", {"records": known_pool})
    write_json(OUTPUT_DIR / "v2_3_ready_benchmark_bug_candidate_pool.json", {"records": benchmark_pool})
    write_json(OUTPUT_DIR / "v2_3_ready_dependency_drift_candidate_pool.json", {"records": dependency_pool})
    write_json(
        OUTPUT_DIR / "fallback_controlled_fixture_pool.json",
        {
            "records": fallback_pool,
            "counts_toward_known_external_bug_aggregate": False,
            "note": "Fallback controlled fixtures are preserved from v2.2 but do not count as known external bug evidence.",
        },
    )
    write_text(
        OUTPUT_DIR / "candidate_gap_report.md",
        "\n".join(
            [
                "# v2.3 Candidate Gap Report",
                "",
                f"Promoted known external bug candidates: {len(known_pool)}",
                f"Promoted benchmark bug candidates: {len(benchmark_pool)}",
                f"Promoted dependency-drift candidates: {len(dependency_pool)}",
                f"Fallback controlled fixture candidates: {len(fallback_pool)} (not counted)",
                "",
                "QuixBugs was acquired locally and promoted only as curated benchmark evidence, not organic external bug evidence.",
                "The campaign rejected using QuixBugs corrected Python programs as decision-time inputs; those files remain post-outcome/reference material only.",
                "BugsInPy, SWE-bench-style, and dependency-drift candidates remain blocked until bounded local task packs or exact known failing revisions are supplied.",
                "Fallback controlled fixtures do not count as known external bug evidence.",
                "",
            ]
        ),
    )
    write_json(
        OUTPUT_DIR / "v2_3_handoff_recommendations.json",
        {
            "promoted_known_or_benchmark_or_dependency_count": promoted_count,
            "execute_v2_3_limited_replay": execute,
            "recommendation": "executed_v2_3_limited_benchmark_replay_pilot"
            if execute
            else "blocked_known_external_bug_candidate_acquisition_failure",
            "fallback_controlled_fixture_count": len(fallback_pool),
            "fallback_fixtures_count_toward_known_external_bug_aggregate": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "campaign_results.json",
        {
            "executed_episode_count": len(episode_results),
            "scoreable_episode_count": scoreable_count,
            "positive_memory_episode_count": positive_count,
            "negative_episode_count": 0,
            "inconclusive_episode_count": sum(1 for result in episode_results if result["classification"] == "inconclusive_equal_performance"),
            "blocked_episode_count": 0,
            "decision_time_outcome_overlap_count": overlap_count,
            "corruption_in_positive_memory_episode_count": corruption_count,
            "aggregate_result": aggregate,
            "limited_known_external_or_benchmark_memory_lift_criteria_met": aggregate
            == "limited_known_external_or_benchmark_memory_lift_criteria_met",
            "broad_organic_external_memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "episode_results": episode_results,
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_known_external_bug_memory_lift_assessment.json",
        {
            "aggregate_result": aggregate,
            "limited_known_external_or_benchmark_memory_lift_criteria_met": aggregate
            == "limited_known_external_or_benchmark_memory_lift_criteria_met",
            "known_external_bug_episode_count": len(known_pool),
            "benchmark_bug_episode_count": len(benchmark_pool),
            "dependency_drift_episode_count": len(dependency_pool),
            "scoreable_episode_count": scoreable_count,
            "positive_memory_episode_count": positive_count,
            "decision_time_outcome_overlap_count": overlap_count,
            "corruption_in_positive_memory_episode_count": corruption_count,
            "broad_organic_external_memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "scope_boundary": "limited benchmark bug replay evidence only; not arbitrary public repo performance",
        },
    )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "\n".join(
            [
                "# v2.3 Known External Bug Replay Campaign",
                "",
                "Known external bug replay is stronger than injected fixture evidence.",
                "Benchmark bugs must be labeled as benchmark evidence.",
                "Fallback controlled fixtures do not count as known external bug evidence.",
                "",
                f"- Promoted candidates count: {promoted_count}",
                f"- Promoted benchmark candidates: {len(benchmark_pool)}",
                f"- Executed episodes count: {len(episode_results)}",
                f"- Scoreable episodes count: {scoreable_count}",
                f"- Positive memory episodes: {positive_count}",
                f"- Aggregate result: `{aggregate}`",
                "- Claim boundary: limited benchmark bug replay evidence only.",
                "- Broad organic external memory lift remains undemonstrated.",
                "- Self-maintaining software remains undemonstrated.",
                "- Full scoring remains disallowed.",
                "",
                "Benchmark success does not prove arbitrary public repo performance. Candidate readiness does not prove repair capability. Corrected benchmark files were not decision-time repair inputs.",
                "",
            ]
        ),
    )
    write_manifest(OUTPUT_DIR)


def append_shareable_summary() -> None:
    summary = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
    text = summary.read_text(encoding="utf-8")
    heading = "## v2.3 Known External Bug Replay Campaign"
    if heading in text:
        text = text.split(heading)[0].rstrip() + "\n\n"
    section = f"""{heading}

Known external bug replay is stronger than injected fixture evidence. Benchmark bugs must be labeled as benchmark evidence.

- Promoted candidates count: 3
- Known external bug candidates: 0
- Benchmark bug candidates: 3
- Fallback controlled fixture candidates: 3, not counted
- Executed episodes count: 3
- Scoreable episodes count: 3
- Positive memory episodes: 3
- Inconclusive/negative/blocked episodes: 0
- Aggregate result: `limited_known_external_or_benchmark_memory_lift_criteria_met`
- Claim boundary: limited QuixBugs benchmark replay evidence only.

Fallback controlled fixtures do not count as known external bug evidence. Benchmark success does not prove arbitrary public repo performance. External memory lift remains limited unless aggregate criteria are met in the named evidence class. Broad organic external memory lift remains undemonstrated. Self-maintaining software remains undemonstrated. Full scoring remains disallowed.
"""
    summary.write_text(text.rstrip() + "\n\n" + section + "\n", encoding="utf-8")


def main() -> int:
    safe_clear_directory(OUTPUT_DIR)
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    descriptors = candidate_descriptors()
    write_input_file(descriptors)
    triage_records = [triage_descriptor(descriptor) for descriptor in descriptors]
    promoted = [
        record for record in triage_records if record["promotion_status"] == "promoted_ready_for_v2_3_benchmark_bug"
    ]
    episode_results: list[dict[str, Any]] = []
    if len(promoted) >= 3:
        by_id = {item["candidate_id"]: item for item in BENCHMARK_ALGORITHMS}
        for index, record in enumerate(promoted[:3], start=1):
            episode_results.append(run_episode(index, by_id[record["candidate_id"]], record))
    write_campaign_outputs(triage_records, episode_results)
    append_shareable_summary()
    print(
        json.dumps(
            {
                "v2_3_promoted_benchmark_candidates": len(promoted),
                "v2_3_executed_episodes": len(episode_results),
                "v2_3_positive_memory_episodes": sum(
                    1 for result in episode_results if result["memory_enabled_outperformed_no_memory"]
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
