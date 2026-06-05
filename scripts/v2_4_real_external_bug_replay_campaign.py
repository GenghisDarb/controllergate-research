#!/usr/bin/env python3
"""Generate v2.4 SWE-bench/BugsInPy real external bug replay campaign artifacts.

This campaign intentionally fails closed when a real-bug source is acquired but
the local deterministic replay harness cannot be run under the current
environment. It does not run repair scoring.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "inputs" / "v2_4_real_external_bug_sources.json"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_4_real_external_bug_replay_campaign"
BUGSINPY_REPO = REPO_ROOT / "external_repos" / "v2_4_candidate_bugsinpy"
SWE_BENCH_REPO = REPO_ROOT / "external_repos" / "v2_4_candidate_swe_bench"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"


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


def run_probe(command: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
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


def bugsinpy_descriptor(candidate_id: str, project: str, bug_id: str, expected_signature: str) -> dict[str, Any]:
    project_dir = BUGSINPY_REPO / "projects" / project
    bug_dir = project_dir / "bugs" / bug_id
    project_info = read_kv_file(project_dir / "project.info")
    bug_info = read_kv_file(bug_dir / "bug.info")
    run_test = read_optional(bug_dir / "run_test.sh")
    return {
        "base_commit": None,
        "bug_id": bug_id,
        "buggy_commit_or_revision": bug_info.get("buggy_commit_id"),
        "candidate_id": candidate_id,
        "dataset_reference": f"BugsInPy project {project} bug {bug_id}",
        "expected_failing_command": run_test,
        "expected_failure_signature": expected_signature,
        "expected_setup_command": "bugsinpy-checkout followed by bugsinpy-compile, or dataset bug setup.sh where required",
        "expected_test_files": [bug_info.get("test_file")] if bug_info.get("test_file") else [],
        "fixed_commit_or_reference_outcome_only": bug_info.get("fixed_commit_id"),
        "instance_id": f"{project}:{bug_id}",
        "language_hint": "python",
        "license_hint": "dataset/source license must be checked before execution; BugsInPy repo itself did not expose a top-level LICENSE in this checkout",
        "notes": "Concrete BugsInPy metadata was acquired locally, but local replay was not promoted because Bash/WSL and Docker execution were unavailable and the requested old Python runtime was not present.",
        "project": project,
        "repo_url": project_info.get("github_url"),
        "runtime_risk": "moderate",
        "source_family": "bugsinpy",
        "upstream_issue_url": None,
        "upstream_pr_url": None,
    }


def source_descriptors() -> list[dict[str, Any]]:
    swe_head = git_head(SWE_BENCH_REPO)
    bugs_head = git_head(BUGSINPY_REPO)
    return [
        {
            "base_commit": None,
            "bug_id": None,
            "buggy_commit_or_revision": None,
            "candidate_id": "v2_4_source_001_swe_bench_verified_family",
            "dataset_reference": "SWE-bench Verified dataset family",
            "expected_failing_command": "python -m swebench.harness.run_evaluation --dataset_name SWE-bench/SWE-bench_Verified --instance_ids <task> --predictions_path <prediction> --run_id <run>",
            "expected_failure_signature": None,
            "expected_setup_command": "Docker-based SWE-bench harness setup",
            "expected_test_files": [],
            "fixed_commit_or_reference_outcome_only": "gold patch and test patch are outcome-only and excluded from decision-time inputs",
            "instance_id": None,
            "language_hint": "python",
            "license_hint": "SWE-bench repository LICENSE present in local checkout; task repository licenses must be checked per instance",
            "local_path": str(SWE_BENCH_REPO) if SWE_BENCH_REPO.exists() else None,
            "local_source_head": swe_head,
            "notes": "Real GitHub issue task family. No concrete safe instance was locally instantiated in this pass.",
            "project": None,
            "repo_url": "https://github.com/SWE-bench/SWE-bench",
            "resource_risk": "heavy",
            "runtime_risk": "heavy",
            "source_family": "swe_bench_verified",
            "upstream_issue_url": None,
            "upstream_pr_url": None,
        },
        {
            "base_commit": None,
            "bug_id": None,
            "buggy_commit_or_revision": None,
            "candidate_id": "v2_4_source_002_swe_bench_lite_family",
            "dataset_reference": "SWE-bench Lite dataset family",
            "expected_failing_command": "python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Lite --instance_ids <task> --predictions_path <prediction> --run_id <run>",
            "expected_failure_signature": None,
            "expected_setup_command": "Docker-based SWE-bench harness setup",
            "expected_test_files": [],
            "fixed_commit_or_reference_outcome_only": "gold patch and test patch are outcome-only and excluded from decision-time inputs",
            "instance_id": None,
            "language_hint": "python",
            "license_hint": "SWE-bench repository LICENSE present in local checkout; task repository licenses must be checked per instance",
            "local_path": str(SWE_BENCH_REPO) if SWE_BENCH_REPO.exists() else None,
            "local_source_head": swe_head,
            "notes": "Real GitHub issue task family. No concrete safe instance was locally instantiated in this pass.",
            "project": None,
            "repo_url": "https://github.com/SWE-bench/SWE-bench",
            "resource_risk": "heavy",
            "runtime_risk": "heavy",
            "source_family": "swe_bench_lite",
            "upstream_issue_url": None,
            "upstream_pr_url": None,
        },
        {
            **bugsinpy_descriptor(
                "v2_4_source_003_bugsinpy_black_2",
                "black",
                "2",
                "BUGSINPY_REAL_BUG_REPLAY: black:2",
            ),
            "local_path": str(BUGSINPY_REPO) if BUGSINPY_REPO.exists() else None,
            "local_source_head": bugs_head,
        },
        {
            **bugsinpy_descriptor(
                "v2_4_source_004_bugsinpy_youtube_dl_1",
                "youtube-dl",
                "1",
                "BUGSINPY_REAL_BUG_REPLAY: youtube-dl:1",
            ),
            "local_path": str(BUGSINPY_REPO) if BUGSINPY_REPO.exists() else None,
            "local_source_head": bugs_head,
        },
        {
            "base_commit": None,
            "bug_id": None,
            "buggy_commit_or_revision": "v2.3 QuixBugs checkout preserved separately",
            "candidate_id": "v2_4_source_005_quixbugs_preserved_not_organic",
            "dataset_reference": "QuixBugs already used in v2.3",
            "expected_failing_command": None,
            "expected_failure_signature": None,
            "expected_setup_command": None,
            "expected_test_files": [],
            "fixed_commit_or_reference_outcome_only": "correct_python_programs excluded from decision-time inputs in v2.3",
            "instance_id": None,
            "language_hint": "python",
            "license_hint": "checked in v2.3 artifacts",
            "local_path": str(REPO_ROOT / "external_repos" / "v2_3_candidate_quixbugs"),
            "notes": "Preserved as algorithmic benchmark evidence only. It is not eligible for v2.4 real external bug evidence.",
            "project": "QuixBugs",
            "repo_url": "https://github.com/jkoppel/QuixBugs.git",
            "resource_risk": "safe",
            "runtime_risk": "low",
            "source_family": "quixbugs_preserved_not_organic",
            "upstream_issue_url": None,
            "upstream_pr_url": None,
        },
    ]


def preflight_records(descriptors: list[dict[str, Any]], probes: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    docker_available = probes["docker_info"].get("returncode") == 0
    bash_available = probes["bash_version"].get("returncode") == 0
    for descriptor in descriptors:
        family = descriptor["source_family"]
        if family in {"swe_bench_verified", "swe_bench_lite"}:
            blocker = (
                "SWE-bench source repository was acquired, but no bounded concrete task metadata was locally "
                "instantiated and the Docker evaluation daemon is unavailable in this environment."
            )
            record = {
                "artifact_custody_feasibility": False,
                "base_or_buggy_state_known": False,
                "blocker_if_not_promoted": blocker,
                "candidate_class": "known_organic_external_issue",
                "candidate_id": descriptor["candidate_id"],
                "corruption_check_feasibility": False,
                "decision_time_input_policy": "gold patches and test patches are outcome-only and barred from decision-time inputs",
                "environment_reproducibility": "failed" if not docker_available else "unknown",
                "failing_command_known": False,
                "fixed_reference_outcome_only": descriptor["fixed_commit_or_reference_outcome_only"],
                "gold_patch_exclusion_plan": "do not load gold patch, test patch, fixed diff, or oracle patch into no-memory or memory-enabled decision-time inputs",
                "issue_or_bug_reference": descriptor["dataset_reference"],
                "local_replay_feasibility": "failed" if not docker_available else "unknown",
                "memory_enabled_path_feasibility": False,
                "memory_relevance_score": 70,
                "no_memory_baseline_feasibility": False,
                "promotion_status": "blocked_environment_too_heavy",
                "readiness_score": 35,
                "resource_feasibility": "heavy",
                "setup_command_known": True,
                "source_family": family,
                "candidate_descriptor": descriptor,
            }
        elif family == "bugsinpy":
            python_required = "3.8" if descriptor["project"] == "black" else "3.7"
            blocker = (
                f"BugsInPy metadata for {descriptor['project']} bug {descriptor['bug_id']} was acquired, but "
                f"local deterministic replay was not confirmed: BugsInPy framework scripts require a Unix shell "
                f"or Docker container, Docker daemon is unavailable, and Python {python_required} runtime is not "
                f"available in the bundled environment."
            )
            record = {
                "artifact_custody_feasibility": False,
                "base_or_buggy_state_known": True,
                "blocker_if_not_promoted": blocker,
                "candidate_class": "real_bug_benchmark_entry",
                "candidate_id": descriptor["candidate_id"],
                "corruption_check_feasibility": True,
                "decision_time_input_policy": "bug_patch.txt, fixed commit, and fixed diff are outcome-only and barred from decision-time inputs",
                "environment_reproducibility": "failed" if (not docker_available and not bash_available) else "unknown",
                "failing_command_known": bool(descriptor.get("expected_failing_command")),
                "fixed_reference_outcome_only": True,
                "gold_patch_exclusion_plan": "exclude bug_patch.txt, fixed_commit_id, fixed source tree, and any repair patch from decision-time inputs",
                "issue_or_bug_reference": descriptor["dataset_reference"],
                "local_replay_feasibility": "failed",
                "memory_enabled_path_feasibility": False,
                "memory_relevance_score": 72,
                "no_memory_baseline_feasibility": False,
                "promotion_status": "blocked_no_deterministic_replay",
                "readiness_score": 58,
                "resource_feasibility": "moderate",
                "setup_command_known": True,
                "source_family": family,
                "candidate_descriptor": descriptor,
            }
        else:
            record = {
                "artifact_custody_feasibility": True,
                "base_or_buggy_state_known": True,
                "blocker_if_not_promoted": "QuixBugs is already preserved as v2.3 algorithmic benchmark evidence and is not eligible as v2.4 real external bug evidence.",
                "candidate_class": "algorithmic_benchmark_only",
                "candidate_id": descriptor["candidate_id"],
                "corruption_check_feasibility": True,
                "decision_time_input_policy": "not considered for v2.4 real external bug decision-time inputs",
                "environment_reproducibility": "confirmed",
                "failing_command_known": False,
                "fixed_reference_outcome_only": True,
                "gold_patch_exclusion_plan": "preserve v2.3 outcome-only corrected-file exclusion; do not count QuixBugs for v2.4",
                "issue_or_bug_reference": descriptor["dataset_reference"],
                "local_replay_feasibility": "confirmed",
                "memory_enabled_path_feasibility": False,
                "memory_relevance_score": 0,
                "no_memory_baseline_feasibility": False,
                "promotion_status": "rejected_after_triage",
                "readiness_score": 0,
                "resource_feasibility": "safe",
                "setup_command_known": False,
                "source_family": family,
                "candidate_descriptor": descriptor,
            }
        records.append(record)
    return records


def summarize_promotions(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record["promotion_status"]] = counts.get(record["promotion_status"], 0) + 1
    return {
        "promotion_counts": counts,
        "promoted_swe_bench_count": sum(
            1 for record in records if record["promotion_status"] == "promoted_ready_for_v2_4_swe_bench_issue"
        ),
        "promoted_bugsinpy_count": sum(
            1 for record in records if record["promotion_status"] == "promoted_ready_for_v2_4_bugsinpy_real_bug"
        ),
        "promoted_known_or_real_bug_count": sum(
            1
            for record in records
            if record["promotion_status"]
            in {
                "promoted_ready_for_v2_4_swe_bench_issue",
                "promoted_ready_for_v2_4_bugsinpy_real_bug",
            }
        ),
        "promoted_candidates": [
            record for record in records if record["promotion_status"].startswith("promoted_ready_for_v2_4")
        ],
    }


def update_shareable_summary() -> None:
    section = """## v2.4 SWE-bench/BugsInPy Real External Bug Replay Campaign

SWE-bench-style tasks are real GitHub issue tasks when reproduced safely. BugsInPy-style entries are real Python bug benchmark entries.

- Source families acquired/preflighted: SWE-bench Verified/Lite repository metadata and BugsInPy repository metadata.
- Promoted candidates count: 0.
- Executed episodes count: 0.
- Scoreable episodes count: 0.
- Positive memory episodes: 0.
- Inconclusive/negative episodes: 0.
- Blocked candidates: 4 real-bug source descriptors plus QuixBugs preserved as non-organic benchmark evidence.
- Aggregate result: `blocked_real_external_bug_candidate_acquisition_failure`.
- Claim boundary: real external bug memory lift remains untested in v2.4.

Gold/corrected patches are outcome-only and excluded from decision-time inputs. Benchmark evidence must be labeled as benchmark evidence. QuixBugs remains algorithmic benchmark evidence only and does not prove organic external bug repair.

The current blockers are execution-environment and task-instantiation blockers, not negative capability evidence: SWE-bench requires a concrete bounded task plus Docker-based evaluation resources, and BugsInPy requires a Unix-style framework or Docker plus project-specific Python runtimes. The next required dataset/source action is to provide or enable a bounded SWE-bench Lite/Verified task workspace or a runnable BugsInPy container/shell environment with exact failing commands.

Self-maintaining software remains undemonstrated. Full scoring remains disallowed. Broad organic external memory lift remains undemonstrated.
"""
    if SHAREABLE_SUMMARY.exists():
        text = SHAREABLE_SUMMARY.read_text(encoding="utf-8")
        marker = "## v2.4 SWE-bench/BugsInPy Real External Bug Replay Campaign"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n\n" + section
        else:
            text = text.rstrip() + "\n\n" + section
    else:
        text = section
    write_text(SHAREABLE_SUMMARY, text)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    descriptors = source_descriptors()
    probes = {
        "generated_at_utc": now(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "docker_info": run_probe(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=10),
        "bash_version": run_probe(["bash", "--version"], timeout=10),
        "swe_bench_local_checkout": {
            "path": str(SWE_BENCH_REPO),
            "exists": SWE_BENCH_REPO.exists(),
            "head": git_head(SWE_BENCH_REPO),
            "license_present": (SWE_BENCH_REPO / "LICENSE").exists(),
        },
        "bugsinpy_local_checkout": {
            "path": str(BUGSINPY_REPO),
            "exists": BUGSINPY_REPO.exists(),
            "head": git_head(BUGSINPY_REPO),
            "top_level_license_present": any((BUGSINPY_REPO / name).exists() for name in ["LICENSE", "LICENSE.txt", "COPYING"]),
            "framework_bin_present": (BUGSINPY_REPO / "framework" / "bin" / "bugsinpy-checkout").exists(),
        },
    }
    records = preflight_records(descriptors, probes)
    promotions = summarize_promotions(records)
    promoted_count = promotions["promoted_known_or_real_bug_count"]

    write_json(
        INPUT_PATH,
        {
            "input_id": "v2_4_real_external_bug_sources",
            "schema_version": "1.0",
            "description": "SWE-bench/BugsInPy real external bug source descriptors. These descriptors do not authorize full scoring.",
            "candidates": descriptors,
        },
    )
    write_json(
        OUTPUT_DIR / "source_acquisition_log.json",
        {
            "campaign_id": "v2_4_real_external_bug_replay_campaign",
            "generated_at_utc": now(),
            "source_strategy": "SWE-bench Verified/Lite and BugsInPy first; QuixBugs preserved only as prior benchmark evidence",
            "runtime_probes": probes,
            "source_descriptors_count": len(descriptors),
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_preflight_results.json",
        {
            "campaign_id": "v2_4_real_external_bug_replay_campaign",
            "candidate_count": len(records),
            "records": records,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_promotion_table.json",
        {
            "campaign_id": "v2_4_real_external_bug_replay_campaign",
            **promotions,
            "execution_gate": "do_not_execute_v2_4_no_promoted_candidates" if promoted_count == 0 else "execute_if_safe",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
        },
    )
    write_json(
        OUTPUT_DIR / "v2_4_ready_swe_bench_candidate_pool.json",
        {
            "records": [
                record
                for record in records
                if record["promotion_status"] == "promoted_ready_for_v2_4_swe_bench_issue"
            ],
            "count": 0,
        },
    )
    write_json(
        OUTPUT_DIR / "v2_4_ready_bugsinpy_candidate_pool.json",
        {
            "records": [
                record
                for record in records
                if record["promotion_status"] == "promoted_ready_for_v2_4_bugsinpy_real_bug"
            ],
            "count": 0,
        },
    )
    gap_report = """# v2.4 Candidate Gap Report

Result: `blocked_real_external_bug_candidate_acquisition_failure`.

No SWE-bench or BugsInPy candidate promoted to v2.4 execution. This is blocked acquisition evidence, not negative repair-capability evidence.

## SWE-bench Blocker

The SWE-bench repository was acquired, but no bounded concrete Verified/Lite task metadata was locally instantiated and Docker evaluation resources are unavailable in the current environment. SWE-bench gold patches and test patches remain outcome-only and must be excluded from decision-time inputs.

## BugsInPy Blocker

BugsInPy repository metadata was acquired and concrete bug entries were identified for `black:2` and `youtube-dl:1`. Their buggy/fixed revisions and failing commands are known from dataset metadata, but local deterministic replay was not confirmed because the BugsInPy framework requires a Unix-style shell or Docker container, Docker daemon is unavailable, and project-specific old Python runtimes are not available in the bundled environment.

## QuixBugs Boundary

QuixBugs remains preserved as v2.3 algorithmic benchmark evidence only. It is not counted as v2.4 real external bug or organic GitHub issue evidence.

## Next Required Dataset/Source Action

Provide or enable one of:

- a bounded SWE-bench Lite/Verified task workspace with Docker running and exact instance IDs;
- a runnable BugsInPy Docker container or Unix shell environment plus required Python runtimes;
- pre-extracted BugsInPy task worktrees with buggy revision, failing command, and logs captured without fixed-patch leakage.
"""
    write_text(OUTPUT_DIR / "v2_4_candidate_gap_report.md", gap_report)
    write_json(
        OUTPUT_DIR / "v2_4_handoff_recommendations.json",
        {
            "handoff": "enable_real_bug_replay_environment_before_v2_4_execution",
            "promoted_candidate_count": promoted_count,
            "execute_v2_4_limited_replay": False,
            "blocker": "blocked_real_external_bug_candidate_acquisition_failure",
            "exact_next_actions": [
                "Start Docker Desktop or provide an equivalent Docker daemon for SWE-bench/BugsInPy harnesses.",
                "Provide a bounded SWE-bench Lite/Verified task subset with instance IDs and resource budget.",
                "Provide a runnable BugsInPy container/shell environment with project-specific Python runtimes.",
                "Keep gold/corrected patches outcome-only and out of decision-time inputs.",
            ],
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "campaign_results.json",
        {
            "campaign_id": "v2_4_real_external_bug_replay_campaign",
            "promoted_candidate_count": promoted_count,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "inconclusive_episode_count": 0,
            "negative_episode_count": 0,
            "blocked_candidate_count": 4,
            "quixbugs_preserved_not_counted_count": 1,
            "decision_time_outcome_overlap_count": 0,
            "corruption_in_positive_memory_episode_count": 0,
            "aggregate_result": "blocked_real_external_bug_candidate_acquisition_failure",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_real_external_bug_memory_lift_assessment.json",
        {
            "aggregate_result": "blocked_real_external_bug_candidate_acquisition_failure",
            "limited_swe_bench_known_issue_memory_lift_criteria_met": False,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "limited_real_external_bug_benchmark_memory_lift_criteria_met": False,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "decision_time_outcome_overlap_count": 0,
            "corruption_in_positive_memory_episode_count": 0,
            "gold_corrected_patches_excluded_from_decision_time_inputs": True,
            "quixbugs_counted_as_real_external_bug_evidence": False,
            "fallback_controlled_fixtures_counted": False,
            "broad_organic_external_memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "interpretation": "No v2.4 real external bug capability test occurred because no SWE-bench/BugsInPy candidate promoted under replay and environment gates.",
        },
    )
    campaign_summary = """# v2.4 SWE-bench/BugsInPy Real External Bug Replay Campaign

SWE-bench-style tasks are real GitHub issue tasks when reproduced safely. BugsInPy-style entries are real Python bug benchmark entries.

## Result

`blocked_real_external_bug_candidate_acquisition_failure`

## Counts

- Promoted candidates: 0.
- Executed episodes: 0.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Inconclusive/negative episodes: 0.
- Decision-time/outcome overlap: 0.
- Corruption in positive memory episodes: 0.

## What Happened

The campaign acquired real-bug source families but did not promote any candidate to execution.

- SWE-bench Verified/Lite source was acquired as a source family, but local task execution is Docker/resource dependent and no bounded concrete task was locally instantiated.
- BugsInPy source was acquired and concrete bug metadata was identified for `black:2` and `youtube-dl:1`, but local deterministic replay was blocked by missing Unix-shell/container/runtime support.
- QuixBugs remains preserved as v2.3 algorithmic benchmark evidence only.

Gold/corrected patches are outcome-only and excluded from decision-time inputs. Benchmark evidence must be labeled as benchmark evidence. QuixBugs-only evidence is not counted as real external bug evidence. Fallback controlled fixtures are not counted as real external bug evidence.

## Claim Boundary

This is blocked acquisition evidence, not negative capability evidence. Self-maintaining software remains undemonstrated. Full scoring remains disallowed. Broad organic external memory lift remains undemonstrated.

## Next Required Dataset/Source Action

Enable a bounded replay environment before v2.4 execution: Docker or equivalent container execution for SWE-bench/BugsInPy, exact SWE-bench instance IDs or BugsInPy bug worktrees, project-specific runtimes, and failing logs captured without gold/fixed patch leakage.
"""
    write_text(OUTPUT_DIR / "campaign_summary.md", campaign_summary)
    update_shareable_summary()
    write_manifest(OUTPUT_DIR)
    print("v2.4 real external bug replay campaign artifacts generated")
    print("promoted candidates: 0")
    print("aggregate: blocked_real_external_bug_candidate_acquisition_failure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
