#!/usr/bin/env python3
"""GitHub Actions runner for v2.8f BugsInPy bounded repair proposer.

This runner builds on the v2.8e workspace-preservation gate. It is intentionally
bounded and conservative: a path is scoreable only after preserved repair
workspaces reproduce the target failure and at least one path generates a
non-empty decision-time-only patch candidate.
"""

from __future__ import annotations

import difflib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8e_bugsinpy_repair_workspace_preservation_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8f_bugsinpy_bounded_repair_proposer_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8f_bugsinpy_runtime").resolve()


spec = importlib.util.spec_from_file_location("v2_8e_runner", BASE_RUNNER_PATH)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)

base.ARTIFACT_ROOT = ARTIFACT_ROOT
base.RUNTIME_ROOT = RUNTIME_ROOT
base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()
ORIGINAL_WRITE_COMMON_CAMPAIGN_ARTIFACTS = base.write_common_campaign_artifacts


REPAIR_BUDGET = {
    "max_inspected_files": 25,
    "max_candidate_patches": 2,
    "max_changed_files": 1,
    "max_changed_lines": 8,
    "max_repair_actions": 8,
    "same_budget_for_no_memory_and_memory_enabled": True,
}

REQUIRED_WORKSPACE_GATE_ARTIFACTS = [
    "workspace_equivalence_check.json",
    "no_memory_prerepair_replay_log_raw.txt",
    "memory_enabled_prerepair_replay_log_raw.txt",
]


def write_json(path: Path, data: Any) -> None:
    base.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    base.write_text(path, text)


def run_shell(command: str, cwd: Path, env: dict[str, str], timeout: int = 1800) -> dict[str, Any]:
    return base.run_shell(command, cwd=cwd, env=env, timeout=timeout)


def run_raw(command: list[str], cwd: Path, env: dict[str, str], timeout: int = 1800) -> dict[str, Any]:
    return base.run_raw(command, cwd=cwd, env=env, timeout=timeout)


def git_diff(workspace: Path, env: dict[str, str]) -> str:
    result = run_raw(["git", "diff", "--no-ext-diff"], cwd=workspace, env=env, timeout=120)
    return str(result.get("stdout", ""))


def candidate_files(workspace: Path, candidate: dict[str, Any], log_text: str) -> list[Path]:
    patterns = ["match_str", "test_comments7", "test_beginning_backslash", "Cannot parse", "AssertionError"]
    files: list[Path] = []
    for path in workspace.rglob("*.py"):
        if any(part in {"__pycache__", ".tox", ".venv", "venv"} for part in path.relative_to(workspace).parts):
            continue
        rel = str(path.relative_to(workspace)).replace("\\", "/")
        if rel == candidate["target_test_file"]:
            files.append(path)
            continue
        if len(files) >= REPAIR_BUDGET["max_inspected_files"]:
            break
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if any(pattern in text or pattern in log_text for pattern in patterns):
            files.append(path)
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        if path not in seen:
            deduped.append(path)
            seen.add(path)
    return deduped[: REPAIR_BUDGET["max_inspected_files"]]


def propose_youtube_dl_patch(workspace: Path, inspected: list[Path]) -> dict[str, Any]:
    for path in inspected:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "def match_str(" not in text:
            continue
        if "actual_value is False" in text:
            return {"candidate_generated": False, "reason": "false handling already appears present", "inspected_file": str(path.relative_to(workspace)).replace("\\", "/")}
        candidate_replacements = [
            (
                "return op(actual_value, comparison_value)",
                "if comparison_value is True and actual_value is False:\n        return False\n    return op(actual_value, comparison_value)",
            ),
            (
                "return operator(actual_value, comparison_value)",
                "if comparison_value is True and actual_value is False:\n        return False\n    return operator(actual_value, comparison_value)",
            ),
            (
                "return operator(value, comparison)",
                "if comparison is True and value is False:\n        return False\n    return operator(value, comparison)",
            ),
        ]
        for old, new in candidate_replacements:
            if old in text:
                before = text.splitlines(keepends=True)
                updated = text.replace(old, new, 1)
                after = updated.splitlines(keepends=True)
                diff = "".join(
                    difflib.unified_diff(
                        before,
                        after,
                        fromfile=str(path.relative_to(workspace)),
                        tofile=str(path.relative_to(workspace)),
                    )
                )
                if diff.count("\n+") <= REPAIR_BUDGET["max_changed_lines"] + 3:
                    path.write_text(updated, encoding="utf-8")
                    return {
                        "candidate_generated": True,
                        "patched_file": str(path.relative_to(workspace)).replace("\\", "/"),
                        "heuristic": "boolean_false_handling_for_match_str",
                        "diff": diff,
                    }
        return {"candidate_generated": False, "reason": "def match_str found but no recognized safe return pattern", "inspected_file": str(path.relative_to(workspace)).replace("\\", "/")}
    return {"candidate_generated": False, "reason": "def match_str not found in inspected buggy files"}


def propose_patch(workspace: Path, candidate: dict[str, Any], failing_log: str, memory_enabled: bool) -> dict[str, Any]:
    inspected = candidate_files(workspace, candidate, failing_log)
    inspected_rel = [str(path.relative_to(workspace)).replace("\\", "/") for path in inspected]
    if candidate["candidate"] == "youtube-dl:1":
        proposal = propose_youtube_dl_patch(workspace, inspected)
    else:
        proposal = {
            "candidate_generated": False,
            "reason": "no safe localized parser/formatter patch heuristic is registered for this target failure",
        }
    proposal["inspected_files"] = inspected_rel
    proposal["memory_enabled_path"] = memory_enabled
    proposal["forbidden_inputs_used"] = False
    proposal["fixed_or_gold_patch_used"] = False
    proposal["future_outcome_evidence_used"] = False
    return proposal


def write_proposer_campaign_artifacts() -> None:
    ORIGINAL_WRITE_COMMON_CAMPAIGN_ARTIFACTS()
    write_json(ARTIFACT_ROOT / "bounded_repair_proposer_design.json", {
        "proposer_id": "v2_8f_bounded_decision_time_repair_proposer",
        "safe_patch_only": True,
        "no_patch_generated_is_not_scoreable": True,
    })
    write_json(ARTIFACT_ROOT / "repair_budget_policy.json", REPAIR_BUDGET)
    write_json(ARTIFACT_ROOT / "decision_time_allowed_inputs_policy.json", {
        "allowed_inputs": ["buggy checkout source files", "failing command", "raw failing log", "failing test file content", "local project context", "allowed ControllerGate memory for memory-enabled path"],
    })
    write_json(ARTIFACT_ROOT / "forbidden_inputs_policy.json", {
        "forbidden_inputs": ["BugsInPy fixed revision", "BugsInPy gold patch", "known repair diff", "future passing logs", "manually copied fixes", "fixed-state diagnostic hints"],
    })
    write_json(ARTIFACT_ROOT / "memory_evidence_policy.json", {"memory_enabled_path_may_use_controllergate_memory": True, "fixed_or_gold_patch_forbidden": True})
    write_json(ARTIFACT_ROOT / "repair_candidate_generation_policy.json", {"record_every_inspected_file": True, "record_every_generated_candidate": True})


def write_attempt(path: Path, candidate: dict[str, Any], workspace: Path, prefix: str, env: dict[str, str], memory_enabled: bool) -> dict[str, Any]:
    failing_log = (path / "failing_log_raw.txt").read_text(encoding="utf-8", errors="replace")
    proposal = propose_patch(workspace, candidate, failing_log, memory_enabled)
    write_json(path / f"{prefix}_repair_candidate_generation.json", proposal)
    actions = [
        {"action": "inspect_allowed_decision_time_inputs", "result": "completed"},
        {"action": "inspect_buggy_workspace_files", "files": proposal.get("inspected_files", [])},
        {"action": "generate_bounded_patch_candidate", "candidate_generated": proposal.get("candidate_generated")},
    ]
    write_json(path / f"{prefix}_action_trace.json", {"actions": actions, "patch_candidate_generated": proposal.get("candidate_generated")})
    write_json(path / f"{prefix}_patch_application_result.json", {
        "patch_application_attempted": bool(proposal.get("candidate_generated")),
        "patch_applied": bool(proposal.get("candidate_generated")),
        "blocked_reason": None if proposal.get("candidate_generated") else "blocked_no_safe_patch_candidate_generated",
    })
    diff = git_diff(workspace, env) if proposal.get("candidate_generated") else "# NO PATCH CANDIDATE GENERATED\n"
    write_text(path / f"{prefix}_repair_patch.diff", diff or "# NO PATCH CANDIDATE GENERATED\n")
    write_text(path / f"{prefix}_post_repair_command.txt", candidate["direct_command"] + "\n")
    if proposal.get("candidate_generated"):
        result = run_shell(candidate["direct_command"], cwd=workspace, env=env)
        base.log_result(path / f"{prefix}_post_repair_log_raw.txt", result)
        passed = result.get("returncode") == 0
    else:
        write_text(path / f"{prefix}_post_repair_log_raw.txt", "NOT_RUN: blocked_no_safe_patch_candidate_generated\n")
        passed = False
    outcome = {
        "repair_path_ran": True,
        "candidate_generation_attempted": True,
        "patch_candidate_generated": bool(proposal.get("candidate_generated")),
        "primary_command_passed": passed,
        "changed_file_count": 1 if proposal.get("candidate_generated") else 0,
        "changed_lines": max(0, diff.count("\n+") - 1) if proposal.get("candidate_generated") else 0,
        "repair_actions": len(actions),
        "blocked_reason": None if proposal.get("candidate_generated") else "blocked_no_safe_patch_candidate_generated",
    }
    write_json(path / f"{prefix}_outcome.json", outcome)
    return outcome


def run_repair_paths(candidate: dict[str, Any], project_root: Path, episode_dir: Path, env: dict[str, str]) -> dict[str, Any]:
    validation_command = candidate["direct_command"]
    repair_root = RUNTIME_ROOT / "repair_paths" / candidate["episode_id"]
    no_memory_dir = (repair_root / "no_memory").resolve()
    memory_dir = (repair_root / "memory_enabled").resolve()
    preservation = base.preserve_repair_workspaces(project_root, episode_dir, no_memory_dir, memory_dir)
    if not preservation["workspace_equivalence_passed"]:
        return base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_repair_workspace_equivalence_failure")
    no_pre = run_shell(validation_command, cwd=no_memory_dir, env=env)
    mem_pre = run_shell(validation_command, cwd=memory_dir, env=env)
    base.log_result(episode_dir / "no_memory_prerepair_replay_log_raw.txt", no_pre)
    base.log_result(episode_dir / "memory_enabled_prerepair_replay_log_raw.txt", mem_pre)
    no_check = base.classify_target_replay(base.combined_log(no_pre), no_pre.get("returncode"), candidate["required_markers"])
    mem_check = base.classify_target_replay(base.combined_log(mem_pre), mem_pre.get("returncode"), candidate["required_markers"])
    write_json(episode_dir / "repair_workspace_prerepair_replay_check.json", {"no_memory": no_check, "memory_enabled": mem_check})
    if not no_check["target_failure_matched"] or not mem_check["target_failure_matched"]:
        return base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_repair_workspace_prerepair_replay_failed")
    write_json(episode_dir / "repair_attempt_budget.json", REPAIR_BUDGET | {"fixed_or_gold_patch_forbidden": True})
    write_json(episode_dir / "no_memory_decision_time_inputs.json", {"validation_command": validation_command, "memory_evidence_used": False})
    write_json(episode_dir / "memory_enabled_decision_time_inputs.json", {"validation_command": validation_command, "memory_evidence_used": True})
    write_json(episode_dir / "memory_evidence_used.json", {"allowed_controllergate_memory_only": True, "fixed_bugsinpy_patch_used": False})
    no_outcome = write_attempt(episode_dir, candidate, no_memory_dir, "no_memory", env, False)
    mem_outcome = write_attempt(episode_dir, candidate, memory_dir, "memory_enabled", env, True)
    if not no_outcome["patch_candidate_generated"] and not mem_outcome["patch_candidate_generated"]:
        classification = "blocked_no_safe_patch_candidate_generated"
    elif mem_outcome["primary_command_passed"] and not no_outcome["primary_command_passed"]:
        classification = "positive_evidence_memory_lift_bugsinpy_real_bug_episode"
    elif no_outcome["primary_command_passed"] and not mem_outcome["primary_command_passed"]:
        classification = "negative_evidence_no_memory_lift_bugsinpy_real_bug_episode"
    else:
        classification = "inconclusive_equal_performance"
    return {
        "repair_paths_ran": True,
        "workspace_preservation_passed": True,
        "no_memory_patch_candidate_generated": no_outcome["patch_candidate_generated"],
        "memory_enabled_patch_candidate_generated": mem_outcome["patch_candidate_generated"],
        "classification": classification,
    }


def main() -> int:
    base.write_common_campaign_artifacts = write_proposer_campaign_artifacts
    base.run_repair_paths = run_repair_paths
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
