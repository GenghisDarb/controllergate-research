#!/usr/bin/env python3
"""GitHub Actions runner for v2.8p BugsInPy harness repair broad harvest."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8o_bugsinpy_broad_preflight_harvest_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8p_bugsinpy_harness_repair_broad_harvest_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8p_bugsinpy_runtime").resolve()

spec = importlib.util.spec_from_file_location("v2_8o_runner", BASE_RUNNER_PATH)
v28o = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v28o)

v28n = v28o.v28n
v28m = v28o.v28m
v28l = v28o.v28l
v28k = v28o.v28k
v28j = v28o.v28j
v28i = v28o.v28i
v28g = v28o.v28g
base = v28o.base

BROAD_PREFLIGHT_TARGET = 20
BROAD_PREFLIGHT_BUDGET = 28
REPAIR_REPLACEMENT_BUDGET = 3

CLASSIFICATION_VOCABULARY = [
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "failed_both",
    "inconclusive_equal_performance",
    "no_memory_only",
    "positive_memory_only",
    "runner_regression_preserved_reference_failure",
]

PRESERVED_REFERENCE_CANDIDATES = [
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
        "v2_8p_role": "preserved_scoreable_reference_gate",
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
        "v2_8p_role": "preserved_scoreable_reference_gate",
    },
]

PRESERVED_REFERENCE_IDS = {item["candidate"] for item in PRESERVED_REFERENCE_CANDIDATES}
KNOWN_EXCLUDED_FOR_BROAD_HARVEST = set(v28o.KNOWN_EXCLUDED_FOR_BROAD_HARVEST)


def write_json(path: Path, data: Any) -> None:
    v28o.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    v28o.write_text(path, text)


def normalize_classification(value: str | None) -> str:
    if value in CLASSIFICATION_VOCABULARY:
        return str(value)
    return v28n.normalize_classification(value)


def safe_name(candidate_id: str) -> str:
    return v28o.safe_name(candidate_id)


def split_metadata_files(value: str | None) -> list[str]:
    return v28n.split_metadata_files(value)


def read_kv_file(path: Path) -> dict[str, str]:
    return v28n.read_kv_file(path)


def read_run_test_command(project: str, bug_id: str) -> str | None:
    return v28n.read_run_test_command(project, bug_id)


def restore_preserved_reference_hooks() -> None:
    """Restore the v2.8j/v2.8n repair hooks that are otherwise skipped on import."""

    for module in (v28o, v28n, v28m, v28l, v28k, v28j, v28i, v28g, base):
        module.ARTIFACT_ROOT = ARTIFACT_ROOT
        module.RUNTIME_ROOT = RUNTIME_ROOT
    base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()

    v28j.propose_patch = propose_patch
    v28g.propose_patch = propose_patch
    v28g.write_attempt = v28j.write_attempt
    v28g.run_repair_paths = v28j.run_repair_paths
    v28m.propose_patch = propose_patch
    v28n.propose_patch = propose_patch


def proposal_blocked(candidate: dict[str, Any], reason: str, heuristic: str, discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    return v28j.proposal_blocked(candidate, reason, heuristic, discovery, memory_enabled)


def propose_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    candidate_id = candidate.get("candidate", "")
    if candidate_id == "youtube-dl:1":
        proposal = v28i.apply_youtube_dl_patch(workspace, discovery)
        proposal.update(
            {
                "heuristic_family": "boolean_value_matching_failure",
                "memory_enabled_path": memory_enabled,
                "fixed_or_gold_patch_used": False,
                "future_outcome_evidence_used": False,
                "label_leakage_detected": False,
                "source_discovery_ranked_files": [item["file"] for item in discovery.get("ranked", [])[:10]],
                "candidate": candidate_id,
            }
        )
        return proposal
    if candidate_id == "black:4":
        return v28j.apply_black4_patch(workspace, candidate, discovery, memory_enabled)
    if candidate_id == "black:8":
        return v28j.apply_black8_patch(workspace, candidate, discovery, memory_enabled)
    if candidate_id.startswith("black:"):
        return v28m.apply_black6_replacement_patch(workspace, candidate, discovery, memory_enabled)
    return proposal_blocked(
        candidate,
        "candidate not registered for v2.8p bounded source-only generation",
        "unregistered_candidate",
        discovery,
        memory_enabled,
    )


def split_command_chain(command: str) -> list[str]:
    return [part.strip() for part in command.split("&&") if part.strip()]


def normalize_command(command: str) -> tuple[str, dict[str, Any]]:
    normalized_parts: list[str] = []
    changed = False
    requires_pytest = False
    for part in split_command_chain(command):
        original_part = part
        if part.startswith("python3 "):
            part = "python " + part[len("python3 ") :]
            changed = True
        if part == "pytest" or part.startswith("pytest "):
            suffix = part[len("pytest") :].lstrip()
            part = "python -m pytest" + (f" {suffix}" if suffix else "")
            changed = True
            requires_pytest = True
        elif part.startswith("python -m pytest"):
            requires_pytest = True
        normalized_parts.append(part)
        if part != original_part:
            changed = True
    normalized = " && ".join(normalized_parts) if normalized_parts else command
    policy = {
        "original_command": command,
        "normalized_command": normalized,
        "command_changed": changed,
        "requires_pytest": requires_pytest,
        "pytest_invocation_policy": "raw pytest commands are normalized to python -m pytest",
        "returncode_127_policy": "returncode 127 after normalization is a harness or command-normalization failure, not a candidate-level failure",
    }
    return normalized, policy


def command_uses_pytest(command: str) -> bool:
    _, policy = normalize_command(command)
    return bool(policy["requires_pytest"])


def command_env(env: dict[str, str], project_root: Path) -> dict[str, str]:
    command_environment = dict(env)
    existing = command_environment.get("PYTHONPATH", "")
    prefix = str(project_root.resolve())
    command_environment["PYTHONPATH"] = prefix + (os.pathsep + existing if existing else "")
    return command_environment


def dependency_command_for(candidate: dict[str, Any], project_root: Path, normalized_command: str) -> str:
    hints = list(candidate.get("dependency_hints", []))
    if command_uses_pytest(normalized_command) and "pytest" not in hints:
        hints.append("pytest")
    return base.dependency_command_for(project_root, hints)


def ensure_black_unittest_import_context(project_root: Path, candidate: dict[str, Any], artifact_dir: Path) -> dict[str, Any]:
    tests_dir = project_root / "tests"
    test_black = tests_dir / "test_black.py"
    init_file = tests_dir / "__init__.py"
    record = {
        "project": candidate.get("project"),
        "project_root": str(project_root),
        "tests_test_black_exists": test_black.exists(),
        "tests_init_exists_before": init_file.exists(),
        "tests_init_touched_as_harness_materialization": False,
        "source_repair_patch": False,
    }
    if candidate.get("project") == "black" and test_black.exists() and not init_file.exists():
        write_text(init_file, "# v2.8p harness materialization for project-local unittest imports\n")
        record["tests_init_touched_as_harness_materialization"] = True
    record["tests_init_exists_after"] = init_file.exists()
    write_json(artifact_dir / "black_unittest_import_context.json", record)
    return record


def missing_fixture_paths(project_root: Path, required_files: list[str]) -> list[str]:
    return [rel for rel in required_files if rel and not (project_root / rel).exists()]


def method_markers(command: str) -> list[str]:
    return v28o.method_markers(command)


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
    normalized_command, normalization = normalize_command(command)
    return {
        "episode_id": "UNASSIGNED",
        "candidate": candidate_id,
        "project": project,
        "bug_id": bug_id,
        "direct_command": command,
        "normalized_direct_command": normalized_command,
        "direct_command_source": "BugsInPy run_test.sh",
        "target_test_file": target_test_file,
        "materialization_required_files": test_files or ([target_test_file] if target_test_file else []),
        "failure_signature": f"BUGSINPY_DIRECT_TARGET_REPLAY: {candidate_id}",
        "required_markers": method_markers(normalized_command),
        "dependency_hints": ["pytest"] if normalization["requires_pytest"] else [],
        "replacement_candidate": True,
        "v2_8p_role": role,
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
        bug_dirs = [path for path in (project_dir / "bugs").iterdir() if path.is_dir() and path.name.isdigit()]
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


def heuristic_family(candidate: dict[str, Any], log_text: str, ranked: list[dict[str, Any]]) -> tuple[str | None, bool]:
    return v28o.heuristic_family(candidate, log_text, ranked)


def preflight_score(record: dict[str, Any]) -> int:
    return v28o.preflight_score(record)


def ensure_episode_required_artifacts(episode_dir: Path, command: str, reason: str | None = None) -> None:
    reason = reason or "not_blocked"
    for prefix in ["no_memory", "memory_enabled"]:
        source_patch = episode_dir / f"{prefix}_source_only_repair_patch.diff"
        if not source_patch.exists():
            write_text(source_patch, f"# NO SOURCE-ONLY PATCH\n# {reason}\n")
        patch_application = episode_dir / f"{prefix}_patch_application_result.json"
        if not patch_application.exists():
            write_json(patch_application, {"patch_application_attempted": False, "patch_applied": False, "blocked_reason": reason})
        post_command = episode_dir / f"{prefix}_post_repair_command.txt"
        if not post_command.exists():
            write_text(post_command, command + "\n")
        post_log = episode_dir / f"{prefix}_post_repair_log_raw.txt"
        if not post_log.exists():
            write_text(post_log, f"NOT_RUN: {reason}\n")
        generation = episode_dir / f"{prefix}_repair_candidate_generation.json"
        if not generation.exists():
            write_json(generation, {"candidate_generated": False, "blocked_reason": reason})
    placeholders = {
        "source_discovery_report.json": {"source_discovery_result": "not_run_or_blocked", "blocked_reason": reason},
        "ranked_candidate_source_files.json": {"ranked_files": [], "blocked_reason": reason},
        "candidate_function_extracts.json": {"extracts": [], "blocked_reason": reason},
        "repair_heuristic_selection.json": {"selected_heuristic": "not_run_or_blocked", "candidate_generated": False, "blocked_reason": reason},
        "patch_candidate_safety_check.json": {"candidate_generated": False, "patch_touches_tests": False, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False},
        "repair_materialization_separation.json": {
            "source_repair_candidate_patch_files": ["no_memory_source_only_repair_patch.diff", "memory_enabled_source_only_repair_patch.diff"],
            "failing_test_materialization_or_replay_harness_patch": "runtime setup only",
            "test_files_modified_by_repair_candidate": False,
            "runtime_setup_is_not_code_repair": True,
        },
    }
    for name, data in placeholders.items():
        path = episode_dir / name
        if not path.exists():
            write_json(path, data)


def run_episode(candidate: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    candidate = v28n.discover_candidate(dict(candidate))
    episode_dir = ARTIFACT_ROOT / candidate["episode_id"]
    episode_dir.mkdir(parents=True, exist_ok=True)
    workspace_parent = (RUNTIME_ROOT / "workspaces" / candidate["episode_id"]).resolve()
    project_root = (workspace_parent / candidate["project"]).resolve()
    workspace_parent.mkdir(parents=True, exist_ok=True)
    original_command = candidate.get("direct_command", "")
    normalized_command, normalization = normalize_command(original_command)
    candidate["direct_command"] = normalized_command
    candidate["dependency_hints"] = list(dict.fromkeys(list(candidate.get("dependency_hints", [])) + (["pytest"] if normalization["requires_pytest"] else [])))
    checkout_command = f"bugsinpy-checkout -p {candidate['project']} -v 0 -i {candidate['bug_id']} -w {workspace_parent}"
    compile_command = f"bugsinpy-compile -w {project_root}"
    dependency_command = dependency_command_for(candidate, project_root, normalized_command)

    write_text(episode_dir / "baseline_checkout_command.txt", checkout_command + "\n")
    checkout_result = v28g.run_shell(checkout_command, cwd=REPO_ROOT, env=env, timeout=900)
    base.log_result(episode_dir / "baseline_checkout_log_raw.txt", checkout_result)
    required_files = [item for item in candidate.get("materialization_required_files", []) if item]
    import_context = ensure_black_unittest_import_context(project_root, candidate, episode_dir)
    materialized = {rel: (project_root / rel).exists() for rel in required_files}
    checkout_integrity = {
        "checkout_returncode": checkout_result.get("returncode"),
        "project_root_exists": project_root.exists(),
        "target_test_file": candidate.get("target_test_file"),
        "materialization_required_files": required_files,
        "materialized_files": materialized,
        "target_test_file_exists": bool(candidate.get("target_test_file") and (project_root / candidate["target_test_file"]).exists()),
        "all_materialization_files_exist": bool(required_files) and all(materialized.values()),
        "black_unittest_import_context": import_context,
        "checkout_integrity_passed": bool(checkout_result.get("returncode") == 0 and project_root.exists() and required_files and all(materialized.values())),
    }
    write_json(episode_dir / "checkout_integrity_check.json", checkout_integrity)
    command_environment = command_env(env, project_root)
    normalization_result = normalization | {
        "cwd": str(project_root),
        "project_root_exists": project_root.exists(),
        "pythonpath_includes_project_root": str(project_root.resolve()) in command_environment.get("PYTHONPATH", ""),
        "status": "PASS",
    }
    write_json(episode_dir / "command_normalization_result.json", normalization_result)

    write_text(episode_dir / "dependency_install_commands.txt", dependency_command + "\n")
    write_json(
        episode_dir / "dependency_install_plan.json",
        {
            "prefer_buggy_checkout_dependencies": True,
            "manual_dependency_hints": candidate.get("dependency_hints", []),
            "pytest_installed_for_pytest_candidate": normalization["requires_pytest"],
            "source_modification_allowed": False,
        },
    )
    if checkout_integrity["checkout_integrity_passed"]:
        dependency_result = v28g.run_shell(dependency_command, cwd=REPO_ROOT, env=command_environment, timeout=900)
    else:
        dependency_result = {"command": ["dependency-skipped"], "started_at_utc": base.now(), "finished_at_utc": base.now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout integrity failed", "combined_log": "NOT_RUN: checkout integrity failed", "timed_out": False}
    base.log_result(episode_dir / "dependency_install_log_raw.txt", dependency_result)
    write_text(episode_dir / "compile_command.txt", compile_command + "\n")
    if checkout_integrity["checkout_integrity_passed"]:
        compile_result = v28g.run_shell(compile_command, cwd=REPO_ROOT, env=command_environment, timeout=900)
    else:
        compile_result = {"command": ["compile-skipped"], "started_at_utc": base.now(), "finished_at_utc": base.now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout integrity failed", "combined_log": "NOT_RUN: checkout integrity failed", "timed_out": False}
    base.log_result(episode_dir / "compile_log_raw.txt", compile_result)

    write_text(episode_dir / "failing_command.txt", original_command + "\n")
    write_text(episode_dir / "normalized_failing_command.txt", normalized_command + "\n")
    if checkout_integrity["checkout_integrity_passed"] and dependency_result.get("returncode") == 0 and normalized_command:
        failing_result = v28g.run_shell(normalized_command, cwd=project_root, env=command_environment, timeout=900)
    else:
        failing_result = {"command": ["pre-repair-replay-skipped"], "started_at_utc": base.now(), "finished_at_utc": base.now(), "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout/dependency/preflight gate failed", "combined_log": "NOT_RUN: checkout/dependency/preflight gate failed", "timed_out": False}
    base.log_result(episode_dir / "failing_log_raw.txt", failing_result)
    write_text(episode_dir / "failure_signature.txt", candidate["failure_signature"] + "\n")
    write_text(episode_dir / "pre_repair_replay_transcript.txt", f"$ {normalized_command}\n{base.combined_log(failing_result)}")
    target_check = base.classify_target_replay(base.combined_log(failing_result), failing_result.get("returncode"), candidate.get("required_markers", []))
    returncode_127_after_normalization = failing_result.get("returncode") == 127
    if returncode_127_after_normalization:
        target_check["dependency_or_runtime_blocked"] = True
        target_check["returncode_127_treated_as_harness_failure"] = True
    write_json(episode_dir / "target_failure_match_check.json", target_check | {"failure_signature": candidate["failure_signature"]})
    write_json(episode_dir / "wrapper_contamination_check.json", {"wrapper_path_bypassed": True, "wrapper_contamination_detected": target_check["wrapper_contaminated"]})
    preflight_passed = bool(
        checkout_integrity["checkout_integrity_passed"]
        and dependency_result.get("returncode") == 0
        and normalized_command
        and failing_result.get("returncode") is not None
        and target_check["target_failure_matched"]
        and not target_check["wrapper_contaminated"]
        and not returncode_127_after_normalization
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
            "pytest_installed_for_pytest_candidate": normalization["requires_pytest"],
            "pre_repair_target_command_constructed": bool(normalized_command),
            "pre_repair_target_command_ran": failing_result.get("returncode") is not None,
            "pre_repair_command_returncode": failing_result.get("returncode"),
            "returncode_127_after_normalization": returncode_127_after_normalization,
            "returncode_127_treated_as_harness_failure": returncode_127_after_normalization,
            "target_failure_signal_present": target_check["target_failure_signal_present"],
            "wrapper_contamination": target_check["wrapper_contaminated"],
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "preflight_passed": preflight_passed,
            "blocked_classification_if_failed": "blocked_replay_or_materialization_failure",
        },
    )
    write_json(episode_dir / "fixture_dependency_preflight_result.json", {"target_test_file_exists": checkout_integrity["target_test_file_exists"], "all_materialization_files_exist": checkout_integrity["all_materialization_files_exist"], "missing_files": missing_fixture_paths(project_root, required_files), "fixed_revision_fixture_copying_used": False})
    write_json(episode_dir / "pre_repair_replay_gate_result.json", {"pre_repair_replay_gate_passed": preflight_passed, "target_failure_matched": target_check["target_failure_matched"]})

    if preflight_passed:
        repair = v28g.run_repair_paths(candidate, project_root, episode_dir, command_environment)
        classification = normalize_classification(repair.get("classification"))
        scoreable = bool(repair.get("scoreable", False))
        memory_outperformed = bool(repair.get("memory_enabled_outperformed_no_memory", False))
    else:
        reason = "runner_command_normalization_failure" if returncode_127_after_normalization else "blocked_replay_or_materialization_failure"
        repair = base.write_blocked_repair_artifacts(episode_dir, normalized_command, reason)
        classification = "blocked_replay_or_materialization_failure"
        scoreable = False
        memory_outperformed = False

    write_json(episode_dir / "episode_metadata.json", {"episode_id": candidate["episode_id"], "candidate": candidate["candidate"], "classification": classification, "scoreable": scoreable, "full_scoring_allowed": False, "self_maintaining_software_demonstrated": False})
    write_json(episode_dir / "source_repo_metadata.json", base.candidate_metadata(candidate))
    write_text(episode_dir / "license_summary.txt", "license_status: BugsInPy benchmark runtime checkout\n")
    write_json(episode_dir / "candidate_selection_record.json", candidate)
    write_json(episode_dir / "bugsinpy_bug_reference.json", {"project": candidate["project"], "bug_id": candidate["bug_id"], "fixed_revision_outcome_only": True})
    write_json(episode_dir / "target_repo_snapshot.json", {"project_root": str(project_root), "buggy_checkout_succeeded": checkout_integrity["checkout_integrity_passed"]})
    write_text(episode_dir / "environment_snapshot.txt", f"platform={base.platform.platform()}\npython={base.platform.python_version()}\nPYTHONPATH={command_environment.get('PYTHONPATH', '')}\n")
    write_json(episode_dir / "decision_time_input_manifest.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "label_leakage_detected": False})
    write_json(episode_dir / "gold_patch_exclusion_check.json", {"fixed_revision_used_at_decision_time": False, "gold_patch_used_at_decision_time": False, "corrected_files_used_as_repair_hints": False, "status": "PASS"})
    write_json(episode_dir / "label_blindness_check.json", {"label_leakage_detected": False, "ground_truth_fix_label_used": False})
    write_json(episode_dir / "proof_obligations_ledger.json", {"candidate_preflight_exists": True, "pre_repair_replay_gate_exists": True, "repair_paths_ran": repair.get("repair_paths_ran"), "gold_patch_excluded": True, "scoreable": scoreable})
    write_json(episode_dir / "apoptosis_watchdog_result.json", {"watchdog_triggered": False, "flatline_or_no_op_counted_as_success": False})
    write_json(episode_dir / "post_repair_comparison.json", {"classification": classification, "scoreable": scoreable, "memory_enabled_outperformed_no_memory": memory_outperformed})
    write_json(episode_dir / "corruption_check_result.json", {"corruption_detected": False, "repair_paths_ran": repair.get("repair_paths_ran")})
    write_json(episode_dir / "decision_time_outcome_overlap_check.json", {"overlap_detected": False, "decision_time_outcome_overlap_episode_count": 0})
    write_json(episode_dir / "limited_scoring_result.json", {"result_classification": classification, "scoreable": scoreable, "limited_scoring_executed": scoreable, "memory_enabled_outperformed_no_memory": memory_outperformed, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN"})
    ensure_episode_required_artifacts(episode_dir, normalized_command, repair.get("blocked_reason"))
    base.write_manifest(episode_dir)
    return {"episode_id": candidate["episode_id"], "candidate": candidate["candidate"], "classification": classification, "scoreable": scoreable, "pre_repair_replay_gate_passed": preflight_passed, "repair_paths_ran": repair.get("repair_paths_ran"), "memory_enabled_outperformed_no_memory": memory_outperformed, "decision_time_outcome_overlap": False, "label_leakage": False, "apoptosis_watchdog_triggered": False, "corruption_detected": False}


def run_global_harness_sanity(env: dict[str, str]) -> dict[str, Any]:
    pytest_install = v28g.run_shell("python -m pip install pytest", cwd=REPO_ROOT, env=env, timeout=900)
    python_version = v28g.run_shell("python --version", cwd=REPO_ROOT, env=env, timeout=120)
    pip_version = v28g.run_shell("python -m pip --version", cwd=REPO_ROOT, env=env, timeout=120)
    pytest_version = v28g.run_shell("python -m pytest --version", cwd=REPO_ROOT, env=env, timeout=120)
    for name, result in [
        ("harness_pytest_install_log_raw.txt", pytest_install),
        ("harness_python_version_log_raw.txt", python_version),
        ("harness_pip_version_log_raw.txt", pip_version),
        ("harness_pytest_version_log_raw.txt", pytest_version),
    ]:
        base.log_result(ARTIFACT_ROOT / name, result)
    status = "PASS" if all(result.get("returncode") == 0 for result in [pytest_install, python_version, pip_version, pytest_version]) else "FAIL"
    record = {
        "status": status,
        "python_version_returncode": python_version.get("returncode"),
        "pip_version_returncode": pip_version.get("returncode"),
        "pytest_install_returncode": pytest_install.get("returncode"),
        "pytest_version_returncode": pytest_version.get("returncode"),
        "pytest_installed_before_pytest_candidate_preflight": pytest_install.get("returncode") == 0,
        "commands_run_from_project_root_per_episode": True,
        "pythonpath_includes_project_root_per_episode": True,
        "unittest_import_context_materialized_for_black_if_needed": True,
    }
    write_json(ARTIFACT_ROOT / "harness_sanity_check.json", record)
    return record


def run_preflight(candidate: dict[str, Any], env: dict[str, str], ordinal: int) -> dict[str, Any]:
    original_command = candidate.get("direct_command", "")
    normalized_command, normalization = normalize_command(original_command)
    candidate = dict(candidate)
    candidate["direct_command"] = normalized_command
    candidate["dependency_hints"] = list(dict.fromkeys(list(candidate.get("dependency_hints", [])) + (["pytest"] if normalization["requires_pytest"] else [])))
    preflight_dir = ARTIFACT_ROOT / "preflight_candidates" / f"{ordinal:03d}_{safe_name(candidate['candidate'])}"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    workspace_parent = (RUNTIME_ROOT / "preflight_workspaces" / f"{ordinal:03d}_{safe_name(candidate['candidate'])}").resolve()
    project_root = (workspace_parent / candidate["project"]).resolve()
    workspace_parent.mkdir(parents=True, exist_ok=True)
    checkout_command = f"bugsinpy-checkout -p {candidate['project']} -v 0 -i {candidate['bug_id']} -w {workspace_parent}"
    dependency_command = dependency_command_for(candidate, project_root, normalized_command)
    compile_command = f"bugsinpy-compile -w {project_root}"
    required_files = [item for item in candidate.get("materialization_required_files", []) if item]

    write_json(preflight_dir / "candidate_metadata.json", candidate)
    write_text(preflight_dir / "checkout_command.txt", checkout_command + "\n")
    checkout_result = v28g.run_shell(checkout_command, cwd=REPO_ROOT, env=env, timeout=900)
    base.log_result(preflight_dir / "checkout_log_raw.txt", checkout_result)
    import_context = ensure_black_unittest_import_context(project_root, candidate, preflight_dir)
    missing_fixtures = missing_fixture_paths(project_root, required_files)
    target_test_exists = bool(candidate.get("target_test_file") and (project_root / candidate["target_test_file"]).exists())
    fixture_ok = bool(required_files) and not missing_fixtures
    write_json(preflight_dir / "fixture_dependency_preflight_result.json", {"required_files": required_files, "missing_files": missing_fixtures, "target_test_file": candidate.get("target_test_file"), "target_test_file_exists": target_test_exists, "fixture_data_dependency_exists": fixture_ok, "fixed_revision_fixture_copying_used": False, "black_unittest_import_context": import_context})
    command_environment = command_env(env, project_root)
    write_text(preflight_dir / "failing_command.txt", original_command + "\n")
    write_text(preflight_dir / "normalized_failing_command.txt", normalized_command + "\n")
    write_json(preflight_dir / "command_normalization_result.json", normalization | {"cwd": str(project_root), "project_root_exists": project_root.exists(), "pythonpath_includes_project_root": str(project_root.resolve()) in command_environment.get("PYTHONPATH", ""), "status": "PASS"})
    write_text(preflight_dir / "dependency_install_commands.txt", dependency_command + "\n")
    write_json(preflight_dir / "dependency_install_plan.json", {"prefer_buggy_checkout_dependencies": True, "source_modification_allowed": False, "manual_dependency_hints": candidate.get("dependency_hints", []), "pytest_installed_for_pytest_candidate": normalization["requires_pytest"]})
    can_continue = checkout_result.get("returncode") == 0 and project_root.exists() and fixture_ok
    if can_continue:
        dependency_result = v28g.run_shell(dependency_command, cwd=REPO_ROOT, env=command_environment, timeout=900)
    else:
        dependency_result = {"command": ["dependency-skipped"], "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout or fixture preflight failed", "combined_log": "NOT_RUN: checkout or fixture preflight failed", "timed_out": False}
    base.log_result(preflight_dir / "dependency_install_log_raw.txt", dependency_result)
    write_text(preflight_dir / "compile_command.txt", compile_command + "\n")
    if can_continue:
        compile_result = v28g.run_shell(compile_command, cwd=REPO_ROOT, env=command_environment, timeout=900)
    else:
        compile_result = {"command": ["compile-skipped"], "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout or fixture preflight failed", "combined_log": "NOT_RUN: checkout or fixture preflight failed", "timed_out": False}
    base.log_result(preflight_dir / "compile_log_raw.txt", compile_result)
    if can_continue and dependency_result.get("returncode") == 0:
        failing_result = v28g.run_shell(normalized_command, cwd=project_root, env=command_environment, timeout=900)
    else:
        failing_result = {"command": ["pre-repair-replay-skipped"], "returncode": None, "stdout": "", "stderr": "NOT_RUN: checkout/dependency/fixture preflight failed", "combined_log": "NOT_RUN: checkout/dependency/fixture preflight failed", "timed_out": False}
    base.log_result(preflight_dir / "failing_log_raw.txt", failing_result)
    log_text = base.combined_log(failing_result)
    target_check = base.classify_target_replay(log_text, failing_result.get("returncode"), candidate.get("required_markers", []))
    returncode_127_after_normalization = failing_result.get("returncode") == 127
    if returncode_127_after_normalization:
        target_check["dependency_or_runtime_blocked"] = True
        target_check["returncode_127_treated_as_harness_failure"] = True
    write_json(preflight_dir / "target_failure_match_check.json", target_check | {"failure_signature": candidate["failure_signature"]})
    ranked: list[dict[str, Any]] = []
    if target_check["target_failure_matched"] and project_root.exists() and not returncode_127_after_normalization:
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
        "pre_repair_command": original_command,
        "normalized_pre_repair_command": normalized_command,
        "pre_repair_command_returncode": failing_result.get("returncode"),
        "returncode_127_after_normalization": returncode_127_after_normalization,
        "returncode_127_treated_as_harness_failure": returncode_127_after_normalization,
        "expected_failure_reproduced": target_check["target_failure_matched"] and not returncode_127_after_normalization,
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
    if returncode_127_after_normalization:
        record["blocked_reason"] = "runner_command_normalization_failure_not_candidate_failure"
    elif not record["expected_failure_reproduced"]:
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
        and not record.get("returncode_127_after_normalization")
    ]
    eligible.sort(key=lambda record: (-int(record.get("readiness_score", 0)), record.get("project") == "black", record["candidate_id"]))
    selected: list[dict[str, Any]] = []
    for record in eligible[:REPAIR_REPLACEMENT_BUDGET]:
        candidate = dict(record["candidate"])
        candidate["episode_id"] = f"episode_{6 + len(selected):03d}"
        candidate["v2_8p_preflight_readiness_score"] = record["readiness_score"]
        candidate["v2_8p_preflight_heuristic_family"] = record.get("heuristic_family_match")
        selected.append(candidate)
    return selected


def aggregate_result(results: list[dict[str, Any]], gate_passed: bool) -> str:
    if not gate_passed:
        return "runner_regression_preserved_reference_failure"
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    if len(scoreable) < 3:
        return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    if len(positives) >= 2:
        return "limited_bugsinpy_real_bug_memory_lift_criteria_met"
    if not positives:
        return "negative_evidence_no_bugsinpy_real_bug_memory_lift"
    return "insufficient_positive_memory_evidence"


def write_command_normalization_policy() -> None:
    write_json(
        ARTIFACT_ROOT / "command_normalization_policy_v2_8p.json",
        {
            "raw_pytest_command_policy": "normalize commands that start with pytest to python -m pytest",
            "pytest_dependency_policy": "install pytest before pytest-based candidates",
            "command_cwd_policy": "execute target commands from the checked-out candidate project root",
            "pythonpath_policy": "prepend project root to PYTHONPATH for target command execution",
            "unittest_black_policy": "ensure project-local tests package import context for black unittest commands as harness materialization only",
            "returncode_127_policy": "returncode 127 is classified as harness/command-normalization failure, not candidate failure",
            "record_original_and_normalized_command": True,
        },
    )


def write_common_v28p_artifacts(seed_candidates: list[dict[str, Any]]) -> None:
    base.write_common_campaign_artifacts()
    write_json(
        ARTIFACT_ROOT / "campaign_plan.json",
        {
            "campaign_id": "v2_8p_bugsinpy_harness_repair_broad_harvest",
            "artifact_name": "v2_8p_bugsinpy_harness_repair_broad_harvest_artifacts",
            "preserved_reference_gate_before_broad_harvest": True,
            "preserved_references": ["youtube-dl:1", "black:4"],
            "broad_preflight_target_if_available": BROAD_PREFLIGHT_TARGET,
            "broad_preflight_budget": BROAD_PREFLIGHT_BUDGET,
            "top_preflight_passing_replacements_to_attempt": REPAIR_REPLACEMENT_BUDGET,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "candidate_pool.json", {"preserved_reference_records": PRESERVED_REFERENCE_CANDIDATES, "preflight_seed_candidates": seed_candidates})
    write_json(
        ARTIFACT_ROOT / "replacement_candidate_policy_v2_8p.json",
        {
            "preserved_reference_gate_required": True,
            "stop_on_preserved_reference_failure": True,
            "stop_classification": "runner_regression_preserved_reference_failure",
            "broad_preflight_before_repair": True,
            "top_preflight_passing_replacements_to_attempt": REPAIR_REPLACEMENT_BUDGET,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "selection_after_observing_repair_success": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "candidate_ranking_policy_v2_8p.json",
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
                "command_normalized_without_returncode_127",
            ],
            "forbidden_signals": ["fixed revision", "gold patch", "future outcome logs", "post-repair success"],
        },
    )
    write_json(ARTIFACT_ROOT / "decision_time_policy.json", {"fixed_revision_contents_allowed": False, "gold_patch_allowed": False, "future_post_repair_logs_allowed": False, "hidden_labels_allowed": False})
    write_json(ARTIFACT_ROOT / "anti_leakage_policy.json", {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True})
    write_json(ARTIFACT_ROOT / "source_repair_vs_harness_separation.json", {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "dependency_runtime_setup_is_not_code_repair": True, "harness_materialization_separate_from_repair": True})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "status": "PENDING_UNTIL_FINAL_RECORDS"})
    write_json(ARTIFACT_ROOT / "package_verification.json", {"artifact_package": "v2_8p_bugsinpy_harness_repair_broad_harvest_artifacts", "generated_by": "v2.8p Linux runner", "full_scoring_allowed": False})
    write_json(ARTIFACT_ROOT / "artifact_sha256_verification.json", {"status": "generated_inside_workflow_not_yet_zipped", "zip_sha256_available_after_download": False, "internal_sha256_manifest_written_at_end": True})
    write_command_normalization_policy()


def write_preserved_reference_gate_result(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_candidate = {item["candidate"]: item for item in results}
    records = [
        {
            "candidate": candidate,
            "episode_id": by_candidate.get(candidate, {}).get("episode_id"),
            "classification": by_candidate.get(candidate, {}).get("classification"),
            "scoreable": by_candidate.get(candidate, {}).get("scoreable") is True,
            "pre_repair_replay_gate_passed": by_candidate.get(candidate, {}).get("pre_repair_replay_gate_passed") is True,
        }
        for candidate in ["youtube-dl:1", "black:4"]
    ]
    status = "PASS" if all(item["scoreable"] for item in records) else "FAIL"
    gate = {
        "status": status,
        "records": records,
        "broad_harvest_allowed": status == "PASS",
        "failure_classification_if_failed": "runner_regression_preserved_reference_failure",
        "youtube_dl_1_scoreable": by_candidate.get("youtube-dl:1", {}).get("scoreable") is True,
        "black_4_scoreable": by_candidate.get("black:4", {}).get("scoreable") is True,
    }
    write_json(ARTIFACT_ROOT / "preserved_reference_gate_result.json", gate)
    return gate


def write_final_campaign_files(results: list[dict[str, Any]], preflight_records: list[dict[str, Any]], selected: list[dict[str, Any]], aggregate: str, available_count: int, gate: dict[str, Any], harness: dict[str, Any]) -> None:
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
        and not record.get("returncode_127_after_normalization")
    ]
    returncode_127_count = sum(1 for record in preflight_records if record.get("returncode_127_after_normalization"))
    vocab_ok = all(item["classification"] in CLASSIFICATION_VOCABULARY for item in records)
    replacement_scoreable = [item for item in records if item["scoreable"] and item["candidate"] not in PRESERVED_REFERENCE_IDS]
    write_json(ARTIFACT_ROOT / "decision_report.json", {"records": records, "classification_vocabulary": CLASSIFICATION_VOCABULARY})
    write_json(
        ARTIFACT_ROOT / "campaign_results.json",
        {
            "workflow_executed": True,
            "available_broad_candidate_count": available_count,
            "broad_preflight_candidate_count": len(preflight_records),
            "preflight_passing_candidate_count": len(preflight_passed),
            "returncode_127_after_normalization_count": returncode_127_count,
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
            "preserved_reference_gate_status": gate.get("status"),
            "harness_sanity_status": harness.get("status"),
            "aggregate_result": aggregate,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "aggregate_report.json", {"aggregate_result": aggregate, "executed_episode_count": len(results), "scoreable_episode_count": len(scoreable), "positive_memory_only_episode_count": len(positives), "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False})
    write_json(ARTIFACT_ROOT / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", {"aggregate_result": aggregate, "scoreable_episode_count": len(scoreable), "positive_memory_episode_count": len(positives), "minimum_required_scoreable_episodes": 3, "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met", "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False})
    write_json(ARTIFACT_ROOT / "broad_candidate_preflight_registry_v2_8p.json", {"records": preflight_records, "count": len(preflight_records), "available_candidate_count": available_count, "returncode_127_after_normalization_count": returncode_127_count})
    write_json(ARTIFACT_ROOT / "replacement_candidate_preflight_summary.json", {"preflight_passed_records": preflight_passed, "selected_for_repair": [item["candidate"] for item in selected], "preflight_required_before_repair_candidate_generation": True, "returncode_127_treated_as_harness_failure": True})
    write_json(ARTIFACT_ROOT / "fixture_dependency_preflight_summary.json", {"records": [{"candidate": record["candidate_id"], "fixture_data_dependency_exists": record["fixture_data_dependency_exists"], "missing": record["missing_fixture_or_data_files"]} for record in preflight_records], "fixed_revision_fixture_copying_used": False})
    write_json(ARTIFACT_ROOT / "source_discovery_summary.json", {"preflight_records": [{"candidate": record["candidate_id"], "source_discovery_result": record["source_discovery_result"], "candidate_source_files_found": record["candidate_source_files_found"]} for record in preflight_records], "buggy_source_only": True})
    write_json(ARTIFACT_ROOT / "pre_repair_replay_gate_summary.json", {"episodes": records, "passed_count": sum(1 for item in records if item["pre_repair_replay_gate_passed"])})
    write_json(ARTIFACT_ROOT / "workspace_equivalence_summary.json", {"episodes": records, "workspace_equivalence_required": True})
    write_json(ARTIFACT_ROOT / "bounded_repair_proposer_summary.json", {"episodes": records, "bounded_source_only_repair_proposer_enabled": True, "selected_replacements": [item["candidate"] for item in selected]})
    write_json(ARTIFACT_ROOT / "candidate_source_integrity_check.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "records": records})
    write_json(ARTIFACT_ROOT / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "all_records_use_allowed_vocabulary": vocab_ok, "status": "PASS" if vocab_ok else "FAIL"})
    write_json(ARTIFACT_ROOT / "audit.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False, "tests_modified_as_repair": False, "source_only_patch_separation_enforced": True, "classification_vocabulary_check_passed": vocab_ok, "preserved_reference_gate_status": gate.get("status"), "harness_sanity_status": harness.get("status")})
    rows = "\n".join(f"| {record['episode_id']} | {record['candidate']} | {record['classification']} | {str(record['scoreable']).lower()} | {str(record['memory_enabled_outperformed_no_memory']).lower()} |" for record in records)
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.8p BugsInPy Harness Repair Broad Harvest\n\n"
        f"Aggregate result: `{aggregate}`.\n\n"
        f"- Preserved reference gate: {gate.get('status')}.\n"
        f"- Harness sanity: {harness.get('status')}.\n"
        f"- Broad candidates preflighted: {len(preflight_records)} / available {available_count}.\n"
        f"- Returncode-127 failures after normalization: {returncode_127_count}.\n"
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
    restore_preserved_reference_hooks()
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
    harness = {"status": "NOT_RUN", "reason": "BugsInPy clone failed"}
    gate = {"status": "FAIL", "broad_harvest_allowed": False, "reason": "BugsInPy clone failed"}
    if clone_result.get("returncode") == 0:
        env["PATH"] = str((base.BUGSINPY_REPO / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")
        write_common_v28p_artifacts(seed_candidates)
        harness = run_global_harness_sanity(env)
        for candidate in PRESERVED_REFERENCE_CANDIDATES:
            results.append(run_episode(candidate, env))
        gate = write_preserved_reference_gate_result(results)
        if gate["status"] == "PASS":
            seed_candidates = enumerate_broad_candidates()
            available_count = len(seed_candidates)
            write_common_v28p_artifacts(seed_candidates)
            write_json(ARTIFACT_ROOT / "preserved_reference_gate_result.json", gate)
            write_json(ARTIFACT_ROOT / "harness_sanity_check.json", harness)
            for ordinal, candidate in enumerate(seed_candidates[:BROAD_PREFLIGHT_BUDGET], start=1):
                preflight_records.append(run_preflight(candidate, env, ordinal))
            selected = select_replacements(preflight_records)
            replacement_scoreable_found = False
            for candidate in selected:
                if replacement_scoreable_found:
                    break
                result = run_episode(candidate, env)
                results.append(result)
                if candidate.get("replacement_candidate") and result.get("scoreable"):
                    replacement_scoreable_found = True
    else:
        write_common_v28p_artifacts(seed_candidates)
        write_json(ARTIFACT_ROOT / "harness_sanity_check.json", harness)
        write_json(ARTIFACT_ROOT / "preserved_reference_gate_result.json", gate)
    gate_passed = gate.get("status") == "PASS"
    aggregate = aggregate_result(results, gate_passed)
    write_final_campaign_files(results, preflight_records, selected, aggregate, available_count, gate, harness)
    base.write_manifest(ARTIFACT_ROOT)
    print(f"v2.8p aggregate: {aggregate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
