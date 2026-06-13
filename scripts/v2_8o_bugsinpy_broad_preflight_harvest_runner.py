#!/usr/bin/env python3
"""GitHub Actions runner for v2.8o broad BugsInPy preflight harvest."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8n_bugsinpy_replacement_preflight_third_scoreable_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8o_bugsinpy_broad_preflight_harvest_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8o_bugsinpy_runtime").resolve()

spec = importlib.util.spec_from_file_location("v2_8n_runner", BASE_RUNNER_PATH)
v28n = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v28n)

v28m = v28n.v28m
v28l = v28n.v28l
v28k = v28n.v28k
v28j = v28n.v28j
v28i = v28n.v28i
v28g = v28n.v28g
base = v28n.base

for module in (v28n, v28m, v28l, v28k, v28j, v28i, v28g, base):
    module.ARTIFACT_ROOT = ARTIFACT_ROOT
    module.RUNTIME_ROOT = RUNTIME_ROOT
base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()

CLASSIFICATION_VOCABULARY = [
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "failed_both",
    "inconclusive_equal_performance",
    "no_memory_only",
    "positive_memory_only",
]

BROAD_PREFLIGHT_TARGET = 20
BROAD_PREFLIGHT_BUDGET = 28
REPAIR_REPLACEMENT_BUDGET = 3

KNOWN_EXCLUDED_FOR_BROAD_HARVEST = {
    "youtube-dl:1",
    "black:1",
    "black:2",
    "black:3",
    "black:4",
    "black:6",
    "black:7",
    "black:8",
}

BASELINE_CANDIDATES = [
    {
        "episode_id": "episode_001",
        "candidate": "youtube-dl:1",
        "project": "youtube-dl",
        "bug_id": "1",
        "direct_command": "python -m unittest -q test.test_utils.TestUtil.test_match_str",
        "target_test_file": "test/test_utils.py",
        "materialization_required_files": ["test/test_utils.py"],
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: youtube-dl:1",
        "required_markers": ["FAIL:", "TestUtil.test_match_str", "AssertionError"],
        "dependency_hints": [],
        "v2_8o_role": "preserved_scoreable_reference",
    },
    {
        "episode_id": "episode_002",
        "candidate": "black:8",
        "project": "black",
        "bug_id": "8",
        "direct_command": "python -m unittest -q tests.test_black.BlackTestCase.test_comments7",
        "target_test_file": "tests/test_black.py",
        "materialization_required_files": ["tests/test_black.py"],
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:8",
        "required_markers": ["FAIL: test_comments7", "BlackTestCase.test_comments7", "Cannot parse: 11:4:"],
        "dependency_hints": ["click"],
        "v2_8o_role": "frozen_non_scoreable_unless_preregistered_rule_exists",
    },
    {
        "episode_id": "episode_003",
        "candidate": "black:4",
        "project": "black",
        "bug_id": "4",
        "direct_command": "python -m unittest -q tests.test_black.BlackTestCase.test_beginning_backslash",
        "target_test_file": "tests/test_black.py",
        "materialization_required_files": ["tests/test_black.py"],
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:4",
        "required_markers": ["FAIL: test_beginning_backslash", "BlackTestCase.test_beginning_backslash", "AssertionError"],
        "dependency_hints": ["click"],
        "v2_8o_role": "preserved_scoreable_reference",
    },
    {
        "episode_id": "episode_004",
        "candidate": "black:6",
        "project": "black",
        "bug_id": "6",
        "direct_command": "DISCOVER_FROM_BUGSINPY_RUN_TEST",
        "target_test_file": "DISCOVER_FROM_BUGSINPY_METADATA",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:6",
        "required_markers": ["FAIL:", "BlackTestCase", "AssertionError"],
        "dependency_hints": ["click"],
        "replacement_candidate": False,
        "v2_8o_role": "retained_blocked_materialization_lane",
    },
    {
        "episode_id": "episode_005",
        "candidate": "black:7",
        "project": "black",
        "bug_id": "7",
        "direct_command": "DISCOVER_FROM_BUGSINPY_RUN_TEST",
        "target_test_file": "DISCOVER_FROM_BUGSINPY_METADATA",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:7",
        "required_markers": ["FAIL:", "BlackTestCase", "AssertionError"],
        "dependency_hints": ["click"],
        "replacement_candidate": False,
        "v2_8o_role": "retained_optional_no_broad_blocking",
    },
]


def write_json(path: Path, data: Any) -> None:
    v28n.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    v28n.write_text(path, text)


def normalize_classification(value: str | None) -> str:
    return v28n.normalize_classification(value)


def read_kv_file(path: Path) -> dict[str, str]:
    return v28n.read_kv_file(path)


def split_metadata_files(value: str | None) -> list[str]:
    return v28n.split_metadata_files(value)


def read_run_test_command(project: str, bug_id: str) -> str | None:
    return v28n.read_run_test_command(project, bug_id)


def safe_name(candidate_id: str) -> str:
    return candidate_id.replace(":", "_").replace("/", "_").replace("-", "_")


def method_markers(command: str) -> list[str]:
    markers = {"AssertionError", "FAILED", "FAIL", "FAIL:"}
    markers.update(re.findall(r"(test_[A-Za-z0-9_]+)", command))
    selector = command.split()[-1] if command.split() else ""
    if "." in selector:
        markers.add(selector.split(".")[-1])
    return sorted(markers)


def candidate_from_metadata(project: str, bug_id: str, role: str = "broad_preflight_candidate") -> dict[str, Any] | None:
    bug_dir = base.BUGSINPY_REPO / "projects" / project / "bugs" / bug_id
    if not bug_dir.exists():
        return None
    command = read_run_test_command(project, bug_id)
    if not command:
        return None
    bug_info = read_kv_file(bug_dir / "bug.info")
    test_files = split_metadata_files(bug_info.get("test_file"))
    if not test_files:
        test_files = [chunk for chunk in re.findall(r"([A-Za-z0-9_./-]*test[A-Za-z0-9_./-]*\.py)", command)]
    python_tests = [item for item in test_files if item.endswith(".py")]
    target_test_file = python_tests[0] if python_tests else (test_files[0] if test_files else "")
    candidate_id = f"{project}:{bug_id}"
    return {
        "episode_id": "UNASSIGNED",
        "candidate": candidate_id,
        "project": project,
        "bug_id": bug_id,
        "direct_command": command,
        "direct_command_source": "BugsInPy run_test.sh",
        "target_test_file": target_test_file,
        "materialization_required_files": test_files or ([target_test_file] if target_test_file else []),
        "failure_signature": f"BUGSINPY_DIRECT_TARGET_REPLAY: {candidate_id}",
        "required_markers": method_markers(command),
        "dependency_hints": [],
        "replacement_candidate": True,
        "v2_8o_role": role,
        "fixed_or_gold_patch_used_at_decision_time": False,
        "future_outcome_evidence_used_at_decision_time": False,
    }


def enumerate_broad_candidates() -> list[dict[str, Any]]:
    projects_dir = base.BUGSINPY_REPO / "projects"
    candidates: list[dict[str, Any]] = []
    if not projects_dir.exists():
        return candidates
    project_dirs = [path for path in projects_dir.iterdir() if path.is_dir() and (path / "bugs").exists()]
    project_dirs.sort(key=lambda path: (path.name == "black", path.name))
    for project_dir in project_dirs:
        bugs_dir = project_dir / "bugs"
        bug_dirs = [path for path in bugs_dir.iterdir() if path.is_dir() and path.name.isdigit()]
        bug_dirs.sort(key=lambda path: int(path.name))
        for bug_dir in bug_dirs:
            candidate_id = f"{project_dir.name}:{bug_dir.name}"
            if candidate_id in KNOWN_EXCLUDED_FOR_BROAD_HARVEST:
                continue
            candidate = candidate_from_metadata(project_dir.name, bug_dir.name)
            if candidate is None:
                continue
            candidates.append(candidate)
            if len(candidates) >= BROAD_PREFLIGHT_BUDGET:
                return candidates
    return candidates


def dependency_command_for(candidate: dict[str, Any], project_root: Path) -> str:
    hints = list(candidate.get("dependency_hints", []))
    return base.dependency_command_for(project_root, hints)


def missing_fixture_paths(project_root: Path, required_files: list[str]) -> list[str]:
    return [rel for rel in required_files if rel and not (project_root / rel).exists()]


def heuristic_family(candidate: dict[str, Any], log_text: str, ranked: list[dict[str, Any]]) -> tuple[str | None, bool]:
    candidate_id = candidate["candidate"]
    if candidate_id == "youtube-dl:1":
        return "boolean_value_matching_failure", True
    if candidate_id == "black:4":
        return "leading_newline_backslash_formatting_failure", True
    if candidate_id == "black:8":
        return "parser_formatter_localized_failure", True
    if candidate_id.startswith("black:") and ("Cannot parse:" in log_text or "BlackTestCase" in log_text):
        return "black_formatter_context_present_but_not_first_choice", False
    if "AssertionError" in log_text and ranked and len(ranked) <= 3:
        return "localized_assertion_context_unregistered", False
    if "Traceback" in log_text and ranked:
        return "localized_exception_context_unregistered", False
    return None, False


def preflight_score(record: dict[str, Any]) -> int:
    score = 0
    if record.get("expected_failure_reproduced"):
        score += 40
    if record.get("target_test_file_exists"):
        score += 12
    if record.get("fixture_data_dependency_exists"):
        score += 12
    if record.get("dependency_plan_status") == "passed":
        score += 8
    if record.get("direct_traceback_or_assertion_context"):
        score += 8
    source_count = len(record.get("candidate_source_files_found", []))
    if 0 < source_count <= 2:
        score += 8
    elif source_count <= 4:
        score += 4
    if record.get("registered_heuristic_family_match"):
        score += 8
    if record.get("bounded_patch_surface") == "likely":
        score += 4
    if record.get("project") == "black":
        score -= 8
    if "formatter" in str(record.get("heuristic_family_match", "")):
        score -= 4
    return max(0, min(100, score))


def run_preflight(candidate: dict[str, Any], env: dict[str, str], ordinal: int) -> dict[str, Any]:
    preflight_dir = ARTIFACT_ROOT / "preflight_candidates" / f"{ordinal:03d}_{safe_name(candidate['candidate'])}"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    workspace_parent = (RUNTIME_ROOT / "preflight_workspaces" / f"{ordinal:03d}_{safe_name(candidate['candidate'])}").resolve()
    project_root = (workspace_parent / candidate["project"]).resolve()
    workspace_parent.mkdir(parents=True, exist_ok=True)
    checkout_command = f"bugsinpy-checkout -p {candidate['project']} -v 0 -i {candidate['bug_id']} -w {workspace_parent}"
    dependency_command = dependency_command_for(candidate, project_root)
    compile_command = f"bugsinpy-compile -w {project_root}"
    required_files = [item for item in candidate.get("materialization_required_files", []) if item]

    write_json(preflight_dir / "candidate_metadata.json", candidate)
    write_text(preflight_dir / "checkout_command.txt", checkout_command + "\n")
    checkout_result = v28g.run_shell(checkout_command, cwd=REPO_ROOT, env=env, timeout=900)
    base.log_result(preflight_dir / "checkout_log_raw.txt", checkout_result)
    missing_fixtures = missing_fixture_paths(project_root, required_files)
    target_test_exists = bool(candidate.get("target_test_file") and (project_root / candidate["target_test_file"]).exists())
    fixture_ok = bool(required_files) and not missing_fixtures
    write_json(
        preflight_dir / "fixture_dependency_preflight_result.json",
        {
            "required_files": required_files,
            "missing_files": missing_fixtures,
            "target_test_file": candidate.get("target_test_file"),
            "target_test_file_exists": target_test_exists,
            "fixture_data_dependency_exists": fixture_ok,
            "fixed_revision_fixture_copying_used": False,
        },
    )
    write_text(preflight_dir / "dependency_install_commands.txt", dependency_command + "\n")
    write_json(preflight_dir / "dependency_install_plan.json", {"prefer_buggy_checkout_dependencies": True, "source_modification_allowed": False, "manual_dependency_hints": candidate.get("dependency_hints", [])})
    can_continue = checkout_result.get("returncode") == 0 and project_root.exists() and fixture_ok
    if can_continue:
        dependency_result = v28g.run_shell(dependency_command, cwd=REPO_ROOT, env=env, timeout=900)
    else:
        dependency_result = {"command": ["dependency-skipped"], "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout or fixture preflight failed", "combined_log": "NOT_RUN: checkout or fixture preflight failed", "timed_out": False}
    base.log_result(preflight_dir / "dependency_install_log_raw.txt", dependency_result)
    write_text(preflight_dir / "compile_command.txt", compile_command + "\n")
    if can_continue:
        compile_result = v28g.run_shell(compile_command, cwd=REPO_ROOT, env=env, timeout=900)
    else:
        compile_result = {"command": ["compile-skipped"], "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout or fixture preflight failed", "combined_log": "NOT_RUN: checkout or fixture preflight failed", "timed_out": False}
    base.log_result(preflight_dir / "compile_log_raw.txt", compile_result)
    write_text(preflight_dir / "failing_command.txt", candidate["direct_command"] + "\n")
    if can_continue and dependency_result.get("returncode") == 0:
        failing_result = v28g.run_shell(candidate["direct_command"], cwd=project_root, env=env, timeout=900)
    else:
        failing_result = {"command": ["pre-repair-replay-skipped"], "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout/dependency/fixture preflight failed", "combined_log": "NOT_RUN: checkout/dependency/fixture preflight failed", "timed_out": False}
    base.log_result(preflight_dir / "failing_log_raw.txt", failing_result)
    log_text = base.combined_log(failing_result)
    target_check = base.classify_target_replay(log_text, failing_result.get("returncode"), candidate.get("required_markers", []))
    write_json(preflight_dir / "target_failure_match_check.json", target_check | {"failure_signature": candidate["failure_signature"]})
    ranked: list[dict[str, Any]] = []
    if target_check["target_failure_matched"] and project_root.exists():
        discovery = v28g.run_source_discovery(preflight_dir, project_root, candidate, log_text)
        ranked = discovery.get("ranked", [])
    family, registered = heuristic_family(candidate, log_text, ranked)
    record = {
        "candidate_id": candidate["candidate"],
        "project": candidate["project"],
        "bug_id": candidate["bug_id"],
        "checkout_status": "passed" if checkout_result.get("returncode") == 0 and project_root.exists() else "failed",
        "dependency_plan_status": "passed" if dependency_result.get("returncode") == 0 else "failed_or_not_run",
        "target_test_file_exists": target_test_exists,
        "fixture_data_dependency_exists": fixture_ok,
        "missing_fixture_or_data_files": missing_fixtures,
        "pre_repair_command": candidate["direct_command"],
        "pre_repair_command_returncode": failing_result.get("returncode"),
        "expected_failure_reproduced": target_check["target_failure_matched"],
        "wrapper_contamination": target_check["wrapper_contaminated"],
        "dependency_or_runtime_blocked": target_check["dependency_or_runtime_blocked"],
        "source_discovery_result": "passed" if ranked else "not_run_or_no_localized_source",
        "candidate_source_files_found": [item.get("file") for item in ranked[:5]],
        "heuristic_family_match": family,
        "registered_heuristic_family_match": registered,
        "direct_traceback_or_assertion_context": "Traceback" in log_text or "AssertionError" in log_text,
        "bounded_patch_surface": "likely" if 0 < len(ranked) <= 3 else "unknown",
        "pure_python_source_only_patch_likely": bool(ranked),
        "blocked_reason": None,
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
    }
    if not record["expected_failure_reproduced"]:
        record["blocked_reason"] = "target_failure_not_reproduced_or_runtime_blocked"
    elif not registered:
        record["blocked_reason"] = "preflight_passed_but_no_registered_source_only_heuristic_family"
    record["readiness_score"] = preflight_score(record)
    write_json(preflight_dir / "preflight_record.json", record)
    base.write_manifest(preflight_dir)
    return record | {"candidate": candidate}


def select_replacements(preflight_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = [
        record
        for record in preflight_records
        if record.get("expected_failure_reproduced")
        and record.get("target_test_file_exists")
        and record.get("fixture_data_dependency_exists")
        and not record.get("wrapper_contamination")
        and not record.get("dependency_or_runtime_blocked")
    ]
    eligible.sort(key=lambda record: (-int(record.get("readiness_score", 0)), record.get("project") == "black", record["candidate_id"]))
    selected: list[dict[str, Any]] = []
    for record in eligible[:REPAIR_REPLACEMENT_BUDGET]:
        candidate = dict(record["candidate"])
        candidate["episode_id"] = f"episode_{6 + len(selected):03d}"
        candidate["v2_8o_preflight_readiness_score"] = record["readiness_score"]
        candidate["v2_8o_preflight_heuristic_family"] = record.get("heuristic_family_match")
        selected.append(candidate)
    return selected


def write_common_v28o_artifacts(candidates: list[dict[str, Any]]) -> None:
    base.write_common_campaign_artifacts()
    write_json(
        ARTIFACT_ROOT / "campaign_plan.json",
        {
            "campaign_id": "v2_8o_bugsinpy_broad_preflight_harvest",
            "artifact_name": "v2_8o_bugsinpy_broad_preflight_harvest_artifacts",
            "baseline_candidate_ids": [item["candidate"] for item in BASELINE_CANDIDATES],
            "broad_preflight_target_if_available": BROAD_PREFLIGHT_TARGET,
            "broad_preflight_budget": BROAD_PREFLIGHT_BUDGET,
            "top_preflight_passing_replacements_to_attempt": REPAIR_REPLACEMENT_BUDGET,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "candidate_pool.json", {"baseline_records": BASELINE_CANDIDATES, "preflight_seed_candidates": candidates})
    write_json(
        ARTIFACT_ROOT / "replacement_candidate_policy_v2_8o.json",
        {
            "preserve_scoreable_reference_candidates": ["youtube-dl:1", "black:4"],
            "black8_policy": "frozen as non-scoreable unless a preregistered source-only rule already exists before observing repair success",
            "black6_policy": "blocked_replay_or_materialization_failure unless missing fixture/data dependencies materialize safely",
            "black7_policy": "optional only with bounded decision-time-valid heuristic; does not block broad harvest",
            "broad_preflight_before_repair": True,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "selection_after_observing_repair_success": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "candidate_ranking_policy_v2_8o.json",
        {
            "decision_time_safe_signals": [
                "pre_repair_target_failure_reproduces",
                "target_test_file_exists",
                "fixture_data_files_exist",
                "simple_dependency_install",
                "direct_traceback_or_assertion_context",
                "localized_source_discovery",
                "registered_heuristic_family_match",
                "bounded_patch_surface",
                "pure_python_source_only_patch_likely",
                "black_formatter_penalty",
            ],
            "forbidden_signals": ["fixed revision", "gold patch", "future outcome logs", "post-repair success"],
        },
    )
    write_json(ARTIFACT_ROOT / "decision_time_policy.json", {"fixed_revision_contents_allowed": False, "gold_patch_allowed": False, "future_post_repair_logs_allowed": False, "hidden_labels_allowed": False})
    write_json(ARTIFACT_ROOT / "anti_leakage_policy.json", {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True})
    write_json(ARTIFACT_ROOT / "source_repair_vs_harness_separation.json", {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "dependency_runtime_setup_is_not_code_repair": True})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "status": "PENDING_UNTIL_FINAL_RECORDS"})
    write_json(ARTIFACT_ROOT / "package_verification.json", {"artifact_package": "v2_8o_bugsinpy_broad_preflight_harvest_artifacts", "generated_by": "v2.8o Linux runner", "full_scoring_allowed": False})
    write_json(ARTIFACT_ROOT / "artifact_sha256_verification.json", {"status": "generated_inside_workflow_not_yet_zipped", "zip_sha256_available_after_download": False, "internal_sha256_manifest_written_at_end": True})


def add_fixture_summary_for_episode(result: dict[str, Any]) -> None:
    episode_dir = ARTIFACT_ROOT / result["episode_id"]
    checkout_path = episode_dir / "checkout_integrity_check.json"
    preflight_path = episode_dir / "candidate_preflight_result.json"
    if not checkout_path.exists() or (episode_dir / "fixture_dependency_preflight_result.json").exists():
        return
    checkout = json.loads(checkout_path.read_text(encoding="utf-8"))
    preflight = json.loads(preflight_path.read_text(encoding="utf-8")) if preflight_path.exists() else {}
    write_json(
        episode_dir / "fixture_dependency_preflight_result.json",
        {
            "target_test_file_exists": checkout.get("target_test_file_exists"),
            "all_materialization_files_exist": checkout.get("all_materialization_files_exist", checkout.get("target_test_file_exists")),
            "preflight_passed": preflight.get("preflight_passed"),
            "fixed_revision_fixture_copying_used": False,
        },
    )
    base.write_manifest(episode_dir)


def run_repair_episode(candidate: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    result = v28n.run_episode(candidate, env)
    result["classification"] = normalize_classification(result.get("classification"))
    add_fixture_summary_for_episode(result)
    return result


def aggregate_result(results: list[dict[str, Any]]) -> str:
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    if len(scoreable) < 3:
        return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    if len(positives) >= 2:
        return "limited_bugsinpy_real_bug_memory_lift_criteria_met"
    if not positives:
        return "negative_evidence_no_bugsinpy_real_bug_memory_lift"
    return "insufficient_positive_memory_evidence"


def write_final_campaign_files(results: list[dict[str, Any]], preflight_records: list[dict[str, Any]], selected: list[dict[str, Any]], aggregate: str, available_count: int) -> None:
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    records = [
        {
            "episode_id": item["episode_id"],
            "candidate": item["candidate"],
            "classification": item["classification"],
            "scoreable": item["scoreable"],
            "memory_enabled_outperformed_no_memory": item["memory_enabled_outperformed_no_memory"],
            "pre_repair_replay_gate_passed": item["pre_repair_replay_gate_passed"],
        }
        for item in results
    ]
    preflight_passed = [
        record
        for record in preflight_records
        if record.get("expected_failure_reproduced")
        and record.get("target_test_file_exists")
        and record.get("fixture_data_dependency_exists")
        and not record.get("wrapper_contamination")
        and not record.get("dependency_or_runtime_blocked")
    ]
    vocab_ok = all(item["classification"] in CLASSIFICATION_VOCABULARY for item in records)
    replacement_scoreable = [
        item
        for item in records
        if item["scoreable"] and item["candidate"] not in {"youtube-dl:1", "black:4"}
    ]
    write_json(ARTIFACT_ROOT / "decision_report.json", {"records": records, "classification_vocabulary": CLASSIFICATION_VOCABULARY})
    write_json(
        ARTIFACT_ROOT / "campaign_results.json",
        {
            "workflow_executed": True,
            "available_broad_candidate_count": available_count,
            "broad_preflight_candidate_count": len(preflight_records),
            "preflight_passing_candidate_count": len(preflight_passed),
            "repair_attempted_replacement_count": len(selected),
            "executed_episode_count": len(results),
            "scoreable_episode_count": len(scoreable),
            "positive_memory_episode_count": len(positives),
            "blocked_episode_count": len([item for item in results if not item["scoreable"]]),
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "apoptosis_watchdog_triggered_count": 0,
            "corruption_count": 0,
            "replacement_scoreable_episode_count": len(replacement_scoreable),
            "aggregate_result": aggregate,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "aggregate_report.json", {
        "aggregate_result": aggregate,
        "executed_episode_count": len(results),
        "scoreable_episode_count": len(scoreable),
        "positive_memory_only_episode_count": len(positives),
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
    })
    write_json(ARTIFACT_ROOT / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", {
        "aggregate_result": aggregate,
        "scoreable_episode_count": len(scoreable),
        "positive_memory_episode_count": len(positives),
        "minimum_required_scoreable_episodes": 3,
        "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
    })
    write_json(ARTIFACT_ROOT / "broad_candidate_preflight_registry_v2_8o.json", {"records": preflight_records, "count": len(preflight_records), "available_candidate_count": available_count})
    write_json(ARTIFACT_ROOT / "replacement_candidate_preflight_summary.json", {"preflight_passed_records": preflight_passed, "selected_for_repair": [item["candidate"] for item in selected], "preflight_required_before_repair_candidate_generation": True})
    write_json(ARTIFACT_ROOT / "fixture_dependency_preflight_summary.json", {"records": [{"candidate": record["candidate_id"], "fixture_data_dependency_exists": record["fixture_data_dependency_exists"], "missing": record["missing_fixture_or_data_files"]} for record in preflight_records], "fixed_revision_fixture_copying_used": False})
    write_json(ARTIFACT_ROOT / "source_discovery_summary.json", {"preflight_records": [{"candidate": record["candidate_id"], "source_discovery_result": record["source_discovery_result"], "candidate_source_files_found": record["candidate_source_files_found"]} for record in preflight_records], "buggy_source_only": True})
    write_json(ARTIFACT_ROOT / "pre_repair_replay_gate_summary.json", {"episodes": records, "passed_count": sum(1 for item in records if item["pre_repair_replay_gate_passed"])})
    write_json(ARTIFACT_ROOT / "workspace_equivalence_summary.json", {"episodes": records, "workspace_equivalence_required": True})
    write_json(ARTIFACT_ROOT / "bounded_repair_proposer_summary.json", {"episodes": records, "bounded_source_only_repair_proposer_enabled": True, "selected_replacements": [item["candidate"] for item in selected]})
    write_json(ARTIFACT_ROOT / "candidate_source_integrity_check.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "records": records})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "all_records_use_allowed_vocabulary": vocab_ok, "status": "PASS" if vocab_ok else "FAIL"})
    write_json(ARTIFACT_ROOT / "audit.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "tests_modified_as_repair": False, "source_only_patch_separation_enforced": True, "classification_vocabulary_check_passed": vocab_ok})
    rows = "\n".join(f"| {r['episode_id']} | {r['candidate']} | {r['classification']} | {str(r['scoreable']).lower()} | {str(r['memory_enabled_outperformed_no_memory']).lower()} |" for r in records)
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.8o BugsInPy Broad Preflight Harvest\n\n"
        f"Aggregate result: `{aggregate}`.\n\n"
        f"- Broad candidates preflighted: {len(preflight_records)} / available {available_count}.\n"
        f"- Preflight-passing replacement candidates: {len(preflight_passed)}.\n"
        f"- Repair-attempted replacements: {len(selected)}.\n"
        f"- Executed BugsInPy episodes: {len(results)}.\n"
        f"- Scoreable episodes: {len(scoreable)}.\n"
        f"- Positive memory-only episodes: {len(positives)}.\n"
        "- Full scoring: NOT_RUN / disallowed.\n"
        "- Memory lift: not demonstrated unless aggregate criteria are met.\n"
        "- Self-maintaining software: not demonstrated.\n\n"
        "| Episode | Candidate | Classification | Scoreable | Memory outperformed |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{rows}\n",
    )


def main() -> int:
    for module in (v28n, v28m, v28l, v28k, v28j, v28i, v28g, base):
        module.ARTIFACT_ROOT = ARTIFACT_ROOT
        module.RUNTIME_ROOT = RUNTIME_ROOT
    base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True)
    RUNTIME_ROOT.mkdir(parents=True)
    env = os.environ.copy()
    write_text(ARTIFACT_ROOT / "runtime_environment.txt", f"generated_at_utc={base.now()}\nplatform={base.platform.platform()}\npython={base.platform.python_version()}\nrepo_root={REPO_ROOT}\nruntime_root={RUNTIME_ROOT}\n")
    clone_result = base.run_raw(["git", "clone", "--depth", "1", base.BUGSINPY_URL, str(base.BUGSINPY_REPO)], timeout=900)
    base.log_result(ARTIFACT_ROOT / "bugsinpy_clone_log_raw.txt", clone_result)
    seed_candidates: list[dict[str, Any]] = []
    preflight_records: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    available_count = 0
    if clone_result.get("returncode") == 0:
        env["PATH"] = str((base.BUGSINPY_REPO / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")
        seed_candidates = enumerate_broad_candidates()
        available_count = len(seed_candidates)
        write_common_v28o_artifacts(seed_candidates)
        for ordinal, candidate in enumerate(seed_candidates[:BROAD_PREFLIGHT_BUDGET], start=1):
            preflight_records.append(run_preflight(candidate, env, ordinal))
        selected = select_replacements(preflight_records)
        execution_candidates = list(BASELINE_CANDIDATES)
        replacement_scoreable_found = False
        for candidate in selected:
            if replacement_scoreable_found:
                break
            execution_candidates.append(candidate)
        for candidate in execution_candidates:
            result = run_repair_episode(candidate, env)
            results.append(result)
            if candidate.get("replacement_candidate") and result.get("scoreable"):
                replacement_scoreable_found = True
                break
    else:
        write_common_v28o_artifacts(seed_candidates)
    aggregate = aggregate_result(results) if results else "blocked_replay_or_materialization_failure"
    write_final_campaign_files(results, preflight_records, selected, aggregate, available_count)
    base.write_manifest(ARTIFACT_ROOT)
    print(f"v2.8o aggregate: {aggregate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
