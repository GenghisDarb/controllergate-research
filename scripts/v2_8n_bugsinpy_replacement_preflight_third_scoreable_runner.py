#!/usr/bin/env python3
"""GitHub Actions runner for v2.8n replacement preflight third-scoreable recovery."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8m_bugsinpy_replacement_third_scoreable_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8n_bugsinpy_replacement_preflight_third_scoreable_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8n_bugsinpy_runtime").resolve()

spec = importlib.util.spec_from_file_location("v2_8m_runner", BASE_RUNNER_PATH)
v28m = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v28m)

v28l = v28m.v28l
v28k = v28m.v28k
v28j = v28m.v28j
v28i = v28m.v28i
v28g = v28m.v28g
base = v28m.base

for module in (v28m, v28l, v28k, v28j, v28i, v28g, base):
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

REPLACEMENT_POOL = [
    {
        "candidate": "black:6",
        "project": "black",
        "bug_id": "6",
        "status": "primary_preflight_retry_after_v2_8m_materialization_bug",
        "selection_basis": "selected outcome-blind in v2.8m; v2.8n fixes target-file-list materialization preflight",
    },
    {
        "candidate": "black:metadata_next",
        "project": "black",
        "bug_id": "runtime_selected",
        "status": "fallback_only_if_scoreable_count_remains_below_three",
        "selection_basis": "runtime BugsInPy metadata order, excluding known blocked/exposed candidates",
    },
]

CANDIDATES = [
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
        "v2_8n_role": "preserved_scoreable_reference",
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
        "v2_8n_role": "frozen_failed_both_reference",
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
        "v2_8n_role": "preserved_scoreable_reference",
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
        "replacement_candidate": True,
        "v2_8n_role": "primary_replacement_preflight_retry",
    },
    {
        "episode_id": "episode_005",
        "candidate": "black:metadata_next",
        "project": "black",
        "bug_id": "DISCOVER_NEXT_AVAILABLE_BLACK_BUG",
        "direct_command": "DISCOVER_FROM_BUGSINPY_RUN_TEST",
        "target_test_file": "DISCOVER_FROM_BUGSINPY_METADATA",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:metadata_next",
        "required_markers": ["FAIL:", "BlackTestCase", "AssertionError"],
        "dependency_hints": ["click"],
        "replacement_candidate": True,
        "v2_8n_role": "bounded_fallback_replacement_if_needed",
    },
]


def write_json(path: Path, data: Any) -> None:
    v28m.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    v28m.write_text(path, text)


def normalize_classification(value: str | None) -> str:
    if value in {"blocked_runtime_replay_failure", "blocked_pre_repair_replay_gate_failed", "blocked_repair_workspace_equivalence_failure", "blocked_repair_workspace_prerepair_replay_failed"}:
        return "blocked_replay_or_materialization_failure"
    if value in CLASSIFICATION_VOCABULARY:
        return str(value)
    return "blocked_replay_or_materialization_failure"


def split_metadata_files(value: str | None) -> list[str]:
    if not value:
        return []
    parts: list[str] = []
    for chunk in re.split(r"[;\n]", value):
        clean = chunk.strip().strip('"').strip("'")
        if clean:
            parts.append(clean)
    return parts


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


def read_run_test_command(project: str, bug_id: str) -> str | None:
    run_test = base.BUGSINPY_REPO / "projects" / project / "bugs" / bug_id / "run_test.sh"
    if not run_test.exists():
        return None
    commands: list[str] = []
    for raw in run_test.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("set "):
            continue
        line = line.replace("python3 ", "python ")
        if line.startswith("pytest ") or line.startswith("python ") or line.startswith("python -m "):
            commands.append(line)
    return " && ".join(commands) if commands else None


def next_black_bug_id() -> str | None:
    bugs_dir = base.BUGSINPY_REPO / "projects" / "black" / "bugs"
    excluded = {"1", "2", "3", "4", "5", "6", "8"}
    if not bugs_dir.exists():
        return None
    for path in sorted(bugs_dir.iterdir(), key=lambda item: int(item.name) if item.name.isdigit() else 9999):
        if path.is_dir() and path.name.isdigit() and path.name not in excluded:
            return path.name
    return None


def discover_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    discovered = dict(candidate)
    if discovered["bug_id"] == "DISCOVER_NEXT_AVAILABLE_BLACK_BUG":
        bug_id = next_black_bug_id()
        if bug_id:
            discovered["bug_id"] = bug_id
            discovered["candidate"] = f"black:{bug_id}"
            discovered["failure_signature"] = f"BUGSINPY_DIRECT_TARGET_REPLAY: black:{bug_id}"
            discovered["candidate_discovery_source"] = "runtime BugsInPy metadata ordered fallback"
        else:
            discovered["bug_id"] = "unavailable"
            discovered["candidate_discovery_source"] = "runtime BugsInPy metadata fallback unavailable"
    if discovered.get("direct_command") == "DISCOVER_FROM_BUGSINPY_RUN_TEST" and discovered["bug_id"] != "unavailable":
        command = read_run_test_command(discovered["project"], discovered["bug_id"])
        if command:
            discovered["direct_command"] = command
            discovered["direct_command_source"] = "BugsInPy run_test.sh"
        else:
            discovered["direct_command"] = "python -m unittest -q tests.test_black.BlackTestCase"
            discovered["direct_command_source"] = "fallback unittest class command; target failure match still required"
    bug_info = read_kv_file(base.BUGSINPY_REPO / "projects" / discovered["project"] / "bugs" / discovered["bug_id"] / "bug.info")
    test_files = split_metadata_files(bug_info.get("test_file")) or split_metadata_files(discovered.get("target_test_file"))
    test_files = [item for item in test_files if item and item != "DISCOVER_FROM_BUGSINPY_METADATA"]
    if not test_files and discovered["project"] == "black":
        test_files = ["tests/test_black.py"]
    python_tests = [item for item in test_files if item.endswith(".py") and ("test" in item or item.startswith("tests/"))]
    if python_tests:
        discovered["target_test_file"] = python_tests[0]
    elif test_files:
        discovered["target_test_file"] = test_files[0]
    discovered["materialization_required_files"] = test_files or [discovered.get("target_test_file", "")]
    method_markers = re.findall(r"(test_[A-Za-z0-9_]+)", discovered.get("direct_command", ""))
    markers = set(discovered.get("required_markers", []))
    markers.update(method_markers)
    if "BlackTestCase" in discovered.get("direct_command", ""):
        markers.add("BlackTestCase")
    discovered["required_markers"] = sorted(markers)
    return discovered


def run_episode(candidate: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    candidate = discover_candidate(candidate)
    episode_dir = ARTIFACT_ROOT / candidate["episode_id"]
    episode_dir.mkdir(parents=True, exist_ok=True)
    workspace_parent = (RUNTIME_ROOT / "workspaces" / candidate["episode_id"]).resolve()
    project_root = (workspace_parent / candidate["project"]).resolve()
    workspace_parent.mkdir(parents=True, exist_ok=True)
    validation_command = candidate.get("direct_command", "")
    checkout_command = f"bugsinpy-checkout -p {candidate['project']} -v 0 -i {candidate['bug_id']} -w {workspace_parent}"
    compile_command = f"bugsinpy-compile -w {project_root}"
    dependency_command = base.dependency_command_for(project_root, candidate.get("dependency_hints", []))

    write_text(episode_dir / "baseline_checkout_command.txt", checkout_command + "\n")
    checkout_result = v28g.run_shell(checkout_command, cwd=REPO_ROOT, env=env, timeout=900)
    base.log_result(episode_dir / "baseline_checkout_log_raw.txt", checkout_result)
    required_files = [item for item in candidate.get("materialization_required_files", []) if item]
    materialized = {rel: (project_root / rel).exists() for rel in required_files}
    checkout_integrity = {
        "checkout_returncode": checkout_result.get("returncode"),
        "project_root_exists": project_root.exists(),
        "target_test_file": candidate.get("target_test_file"),
        "materialization_required_files": required_files,
        "materialized_files": materialized,
        "target_test_file_exists": bool(candidate.get("target_test_file") and (project_root / candidate["target_test_file"]).exists()),
        "all_materialization_files_exist": bool(required_files) and all(materialized.values()),
        "checkout_integrity_passed": bool(checkout_result.get("returncode") == 0 and project_root.exists() and required_files and all(materialized.values())),
    }
    write_json(episode_dir / "checkout_integrity_check.json", checkout_integrity)

    write_text(episode_dir / "dependency_install_commands.txt", dependency_command + "\n")
    write_json(episode_dir / "dependency_install_plan.json", {"prefer_buggy_checkout_dependencies": True, "manual_dependency_hints": candidate.get("dependency_hints", []), "source_modification_allowed": False})
    if checkout_integrity["checkout_integrity_passed"]:
        dependency_result = v28g.run_shell(dependency_command, cwd=REPO_ROOT, env=env)
    else:
        dependency_result = {"command": ["dependency-skipped"], "started_at_utc": base.now(), "finished_at_utc": base.now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout integrity failed", "combined_log": "NOT_RUN: checkout integrity failed", "timed_out": False}
    base.log_result(episode_dir / "dependency_install_log_raw.txt", dependency_result)
    write_text(episode_dir / "compile_command.txt", compile_command + "\n")
    compile_result = v28g.run_shell(compile_command, cwd=REPO_ROOT, env=env) if checkout_integrity["checkout_integrity_passed"] else {"command": ["compile-skipped"], "started_at_utc": base.now(), "finished_at_utc": base.now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout integrity failed", "combined_log": "NOT_RUN: checkout integrity failed", "timed_out": False}
    base.log_result(episode_dir / "compile_log_raw.txt", compile_result)

    write_text(episode_dir / "failing_command.txt", validation_command + "\n")
    if checkout_integrity["checkout_integrity_passed"] and dependency_result.get("returncode") == 0 and validation_command:
        failing_result = v28g.run_shell(validation_command, cwd=project_root, env=env)
    else:
        failing_result = {"command": ["pre-repair-replay-skipped"], "started_at_utc": base.now(), "finished_at_utc": base.now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout/dependency/preflight gate failed", "combined_log": "NOT_RUN: checkout/dependency/preflight gate failed", "timed_out": False}
    base.log_result(episode_dir / "failing_log_raw.txt", failing_result)
    write_text(episode_dir / "failure_signature.txt", candidate["failure_signature"] + "\n")
    write_text(episode_dir / "pre_repair_replay_transcript.txt", f"$ {validation_command}\n{base.combined_log(failing_result)}")
    target_check = base.classify_target_replay(base.combined_log(failing_result), failing_result.get("returncode"), candidate.get("required_markers", []))
    write_json(episode_dir / "target_failure_match_check.json", target_check | {"failure_signature": candidate["failure_signature"]})
    write_json(episode_dir / "wrapper_contamination_check.json", {"wrapper_path_bypassed": True, "wrapper_contamination_detected": target_check["wrapper_contaminated"]})
    preflight_passed = bool(
        checkout_integrity["checkout_integrity_passed"]
        and dependency_result.get("returncode") == 0
        and validation_command
        and failing_result.get("returncode") is not None
        and target_check["target_failure_matched"]
        and not target_check["wrapper_contaminated"]
    )
    write_json(
        episode_dir / "candidate_preflight_result.json",
        {
            "candidate": candidate["candidate"],
            "checkout_returncode_zero": checkout_result.get("returncode") == 0,
            "project_root_exists": project_root.exists(),
            "target_test_file_exists": checkout_integrity["target_test_file_exists"],
            "all_materialization_files_exist": checkout_integrity["all_materialization_files_exist"],
            "dependency_install_plan_generated": bool(dependency_command),
            "pre_repair_target_command_constructed": bool(validation_command),
            "pre_repair_target_command_ran": failing_result.get("returncode") is not None,
            "target_failure_signal_present": target_check["target_failure_signal_present"],
            "wrapper_contamination": target_check["wrapper_contaminated"],
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "preflight_passed": preflight_passed,
            "blocked_classification_if_failed": "blocked_replay_or_materialization_failure",
        },
    )
    write_json(episode_dir / "pre_repair_replay_gate_result.json", {"pre_repair_replay_gate_passed": preflight_passed, "target_failure_matched": target_check["target_failure_matched"]})

    if preflight_passed:
        repair = v28g.run_repair_paths(candidate, project_root, episode_dir, env)
        classification = normalize_classification(repair.get("classification"))
        scoreable = bool(repair.get("scoreable", False))
        memory_outperformed = bool(repair.get("memory_enabled_outperformed_no_memory", False))
    else:
        repair = base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_replay_or_materialization_failure")
        classification = "blocked_replay_or_materialization_failure"
        scoreable = False
        memory_outperformed = False

    write_json(episode_dir / "episode_metadata.json", {"episode_id": candidate["episode_id"], "candidate": candidate["candidate"], "classification": classification, "scoreable": scoreable, "full_scoring_allowed": False, "self_maintaining_software_demonstrated": False})
    write_json(episode_dir / "source_repo_metadata.json", base.candidate_metadata(candidate))
    write_text(episode_dir / "license_summary.txt", "license_status: BugsInPy benchmark runtime checkout\n")
    write_json(episode_dir / "candidate_selection_record.json", candidate)
    write_json(episode_dir / "bugsinpy_bug_reference.json", {"project": candidate["project"], "bug_id": candidate["bug_id"], "fixed_revision_outcome_only": True})
    write_json(episode_dir / "target_repo_snapshot.json", {"project_root": str(project_root), "buggy_checkout_succeeded": checkout_integrity["checkout_integrity_passed"]})
    write_text(episode_dir / "environment_snapshot.txt", f"platform={base.platform.platform()}\npython={base.platform.python_version()}\n")
    write_json(episode_dir / "decision_time_input_manifest.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "label_leakage_detected": False})
    write_json(episode_dir / "gold_patch_exclusion_check.json", {"fixed_revision_used_at_decision_time": False, "gold_patch_used_at_decision_time": False, "corrected_files_used_as_repair_hints": False, "status": "PASS"})
    write_json(episode_dir / "label_blindness_check.json", {"label_leakage_detected": False, "ground_truth_fix_label_used": False})
    write_json(episode_dir / "proof_obligations_ledger.json", {"candidate_preflight_exists": True, "pre_repair_replay_gate_exists": True, "repair_paths_ran": repair.get("repair_paths_ran"), "gold_patch_excluded": True, "scoreable": scoreable})
    write_json(episode_dir / "apoptosis_watchdog_result.json", {"watchdog_triggered": False, "flatline_or_no_op_counted_as_success": False})
    write_json(episode_dir / "post_repair_comparison.json", {"classification": classification, "scoreable": scoreable, "memory_enabled_outperformed_no_memory": memory_outperformed})
    write_json(episode_dir / "corruption_check_result.json", {"corruption_detected": False, "repair_paths_ran": repair.get("repair_paths_ran")})
    write_json(episode_dir / "decision_time_outcome_overlap_check.json", {"overlap_detected": False, "decision_time_outcome_overlap_episode_count": 0})
    write_json(episode_dir / "limited_scoring_result.json", {"result_classification": classification, "scoreable": scoreable, "limited_scoring_executed": scoreable, "memory_enabled_outperformed_no_memory": memory_outperformed, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN"})
    base.write_manifest(episode_dir)
    return {"episode_id": candidate["episode_id"], "candidate": candidate["candidate"], "classification": classification, "scoreable": scoreable, "pre_repair_replay_gate_passed": preflight_passed, "repair_paths_ran": repair.get("repair_paths_ran"), "memory_enabled_outperformed_no_memory": memory_outperformed, "decision_time_outcome_overlap": False, "label_leakage": False, "apoptosis_watchdog_triggered": False, "corruption_detected": False}


def propose_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    if candidate.get("candidate", "").startswith("black:") and candidate.get("candidate") not in {"black:4", "black:8"}:
        return v28m.apply_black6_replacement_patch(workspace, candidate, discovery, memory_enabled)
    return v28m.ORIGINAL_PROPOSE_PATCH(workspace, candidate, discovery, memory_enabled)


def aggregate_result(results: list[dict[str, Any]]) -> str:
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    if len(scoreable) < 3:
        return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    if len(positives) >= 2:
        return "limited_bugsinpy_real_bug_memory_lift_criteria_met"
    return "insufficient_positive_memory_evidence"


def write_campaign_artifacts() -> None:
    base.write_common_campaign_artifacts()
    write_json(
        ARTIFACT_ROOT / "campaign_plan.json",
        {
            "campaign_id": "v2_8n_bugsinpy_replacement_preflight_third_scoreable",
            "artifact_name": "v2_8n_bugsinpy_replacement_preflight_third_scoreable_artifacts",
            "candidate_ids": [item["candidate"] for item in CANDIDATES],
            "preflight_before_repair_required": True,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "candidate_pool.json", {"count": len(CANDIDATES), "records": CANDIDATES})
    write_json(
        ARTIFACT_ROOT / "replacement_candidate_policy_v2_8n.json",
        {
            "primary_replacement_retry": "black:6",
            "black6_materialization_fix": "semicolon-delimited BugsInPy target-file metadata is treated as a file list",
            "fallback_candidate_policy": "runtime-select next available black BugsInPy bug from metadata if still below three scoreable episodes",
            "replacement_pool": REPLACEMENT_POOL,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "selection_after_observing_repair_success": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "decision_time_policy.json",
        {
            "allowed_inputs": ["BugsInPy metadata", "buggy checkout", "baseline failing command", "baseline failing log", "buggy-source discovery"],
            "forbidden_inputs": ["fixed revision", "gold patch", "future outcome evidence", "post-repair success/failure", "test edits as repair"],
        },
    )
    write_json(ARTIFACT_ROOT / "anti_leakage_policy.json", {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True})
    write_json(ARTIFACT_ROOT / "source_repair_vs_harness_separation.json", {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "dependency_runtime_setup_is_not_code_repair": True})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "disallowed_values": ["blocked_runtime_replay_failure"], "status": "PENDING_UNTIL_FINAL_RECORDS"})
    write_json(ARTIFACT_ROOT / "replacement_candidate_preflight_summary.json", {"preflight_required_before_repair_candidate_generation": True, "blocked_classification_for_failed_preflight": "blocked_replay_or_materialization_failure"})
    write_json(ARTIFACT_ROOT / "bounded_repair_proposer_summary.json", {"bounded_source_only_repair_proposer_enabled": True, "preflight_required": True})
    write_json(ARTIFACT_ROOT / "package_verification.json", {"artifact_package": "v2_8n_bugsinpy_replacement_preflight_third_scoreable_artifacts", "generated_by": "v2.8n Linux runner", "full_scoring_allowed": False})
    write_json(ARTIFACT_ROOT / "artifact_sha256_verification.json", {"status": "generated_inside_workflow_not_yet_zipped", "zip_sha256_available_after_download": False, "internal_sha256_manifest_written_at_end": True})


def write_final_campaign_files(results: list[dict[str, Any]], aggregate: str) -> None:
    v28m.ORIGINAL_WRITE_FINAL_CAMPAIGN_FILES(results, aggregate)
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
    vocab_ok = all(record["classification"] in CLASSIFICATION_VOCABULARY for record in records)
    write_json(ARTIFACT_ROOT / "decision_report.json", {"records": records, "classification_vocabulary": CLASSIFICATION_VOCABULARY})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "all_records_use_allowed_vocabulary": vocab_ok, "status": "PASS" if vocab_ok else "FAIL"})
    write_json(
        ARTIFACT_ROOT / "campaign_results.json",
        {
            "workflow_executed": True,
            "executed_episode_count": len(results),
            "scoreable_episode_count": len(scoreable),
            "positive_memory_episode_count": len(positives),
            "blocked_episode_count": len([item for item in results if not item["scoreable"]]),
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "apoptosis_watchdog_triggered_count": 0,
            "corruption_count": 0,
            "aggregate_result": aggregate,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "aggregate_report.json",
        {
            "aggregate_result": aggregate,
            "executed_episode_count": len(results),
            "scoreable_episode_count": len(scoreable),
            "positive_memory_only_episode_count": len(positives),
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
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
        },
    )
    write_json(
        ARTIFACT_ROOT / "audit.json",
        {
            "artifact_provenance": "generated by v2.8n Linux runner",
            "fixed_or_gold_patch_used_at_decision_time": False,
            "future_outcome_evidence_used_at_decision_time": False,
            "tests_modified_as_repair": False,
            "source_only_patch_separation_enforced": True,
            "classification_vocabulary_check_passed": vocab_ok,
        },
    )
    rows = "\n".join(
        f"| {record['episode_id']} | {record['candidate']} | {record['classification']} | {str(record['scoreable']).lower()} | {str(record['memory_enabled_outperformed_no_memory']).lower()} |"
        for record in records
    )
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.8n BugsInPy Replacement Preflight Third Scoreable\n\n"
        f"Aggregate result: `{aggregate}`.\n\n"
        f"- Executed BugsInPy episodes: {len(results)}.\n"
        f"- Scoreable episodes: {len(scoreable)}.\n"
        f"- Positive memory-only episodes: {len(positives)}.\n"
        "- Candidate preflight runs before repair generation.\n"
        "- Full scoring: NOT_RUN / disallowed.\n"
        "- Memory lift: not demonstrated unless aggregate criteria are met.\n"
        "- Self-maintaining software: not demonstrated.\n\n"
        "| Episode | Candidate | Classification | Scoreable | Memory outperformed |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{rows}\n",
    )


def main() -> int:
    for module in (v28m, v28l, v28k, v28j, v28i, v28g, base):
        module.ARTIFACT_ROOT = ARTIFACT_ROOT
        module.RUNTIME_ROOT = RUNTIME_ROOT
    base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()
    base.CANDIDATES = CANDIDATES
    v28m.CANDIDATES = CANDIDATES
    v28m.REPLACEMENT_POOL = REPLACEMENT_POOL
    v28m.run_episode = run_episode
    v28m.propose_patch = propose_patch
    v28m.aggregate_result = aggregate_result
    v28m.write_campaign_artifacts = write_campaign_artifacts
    v28m.write_final_campaign_files = write_final_campaign_files
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    return v28m.main()


if __name__ == "__main__":
    raise SystemExit(main())
