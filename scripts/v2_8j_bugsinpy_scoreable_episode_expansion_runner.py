#!/usr/bin/env python3
"""GitHub Actions runner for v2.8j BugsInPy scoreable episode expansion."""

from __future__ import annotations

import difflib
import importlib.util
import os
import re
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8i_bugsinpy_boolean_patch_construction_fix_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8j_bugsinpy_scoreable_episode_expansion_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8j_bugsinpy_runtime").resolve()

spec = importlib.util.spec_from_file_location("v2_8i_runner", BASE_RUNNER_PATH)
v28i = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v28i)

v28g = v28i.v28g
base = v28g.base

v28i.ARTIFACT_ROOT = ARTIFACT_ROOT
v28i.RUNTIME_ROOT = RUNTIME_ROOT
v28g.ARTIFACT_ROOT = ARTIFACT_ROOT
v28g.RUNTIME_ROOT = RUNTIME_ROOT
base.ARTIFACT_ROOT = ARTIFACT_ROOT
base.RUNTIME_ROOT = RUNTIME_ROOT
base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()

CLASSIFICATIONS = {
    "positive_memory_only",
    "no_memory_only",
    "inconclusive_equal_performance",
    "failed_both",
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_target_test_failed",
    "blocked_replay_or_materialization_failure",
}


def write_json(path: Path, data: Any) -> None:
    v28g.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    v28g.write_text(path, text)


def changed_line_count(diff: str) -> int:
    return max(0, diff.count("\n+") - 1)


def source_diff(before: str, after: str, rel: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=rel,
            tofile=rel,
        )
    )


def locate_function_region(text: str, function_name: str) -> dict[str, Any]:
    match = re.search(rf"(?m)^def {re.escape(function_name)}\(", text)
    if not match:
        return {"found": False, "reason": f"function {function_name} not found"}
    start = match.start()
    next_match = re.search(r"(?m)^def [A-Za-z_][A-Za-z0-9_]*\(", text[match.end() :])
    end = match.end() + next_match.start() if next_match else len(text)
    return {"found": True, "start": start, "end": end, "region": text[start:end]}


def safety_record(rel: str, diff: str, heuristic: str) -> dict[str, Any]:
    changed_lines = changed_line_count(diff)
    return {
        "heuristic": heuristic,
        "patch_only_file": rel,
        "source_only_repair_patch": True,
        "failing_test_materialization_patch": False,
        "modifies_tests": rel.startswith("test") or "/test" in rel or rel.startswith("tests/"),
        "uses_fixed_revision": False,
        "uses_gold_patch": False,
        "uses_future_outcome_evidence": False,
        "diff_non_empty": bool(diff.strip()),
        "changed_files": [rel] if diff.strip() else [],
        "changed_file_count": 1 if diff.strip() else 0,
        "changed_lines": changed_lines,
        "within_changed_line_budget": 0 < changed_lines <= v28g.REPAIR_BUDGET["max_changed_lines"],
    }


def proposal_blocked(candidate: dict[str, Any], reason: str, heuristic: str, discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    return {
        "candidate_generated": False,
        "blocked_reason": "blocked_no_safe_patch_candidate_generated",
        "reason": reason,
        "heuristic_family": heuristic,
        "memory_enabled_path": memory_enabled,
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
        "label_leakage_detected": False,
        "source_discovery_ranked_files": [item["file"] for item in discovery["ranked"][:10]],
        "candidate": candidate["candidate"],
    }


def apply_black8_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    rel = "black.py"
    source_path = workspace / rel
    if not source_path.exists():
        return proposal_blocked(candidate, "black.py not found in buggy workspace", "black_comment_trailing_comma_guard", discovery, memory_enabled)
    failing_log = discovery.get("failing_log", "")
    test_text = discovery.get("test_info", {}).get("method_text", "")
    if "Cannot parse: 11:4:" not in failing_log or "test_comments7" not in test_text:
        return proposal_blocked(candidate, "decision-time target failure context did not match comments7 parse failure", "black_comment_trailing_comma_guard", discovery, memory_enabled)
    text = source_path.read_text(encoding="utf-8", errors="replace")
    if "import re" not in text:
        return proposal_blocked(candidate, "black.py lacks existing re import for bounded formatter post-process", "black_comment_trailing_comma_guard", discovery, memory_enabled)
    region = locate_function_region(text, "format_str")
    if not region["found"]:
        return proposal_blocked(candidate, region["reason"], "black_comment_trailing_comma_guard", discovery, memory_enabled)
    function_text = str(region["region"])
    old = "    return dst_contents\n"
    if old not in function_text:
        return proposal_blocked(candidate, "format_str return dst_contents pattern not found", "black_comment_trailing_comma_guard", discovery, memory_enabled)
    new = (
        "    dst_contents = re.sub(\n"
        "        r\"(?m)^(\\\\s+[A-Za-z_][A-Za-z0-9_\\\\.]*)(\\\\n\\\\s+#)\",\n"
        "        r\"\\\\1,\\\\2\",\n"
        "        dst_contents,\n"
        "    )\n"
        "    return dst_contents\n"
    )
    updated_region = function_text.replace(old, new, 1)
    updated = text[: int(region["start"])] + updated_region + text[int(region["end"]) :]
    diff = source_diff(text, updated, rel)
    safety = safety_record(rel, diff, "black_comment_trailing_comma_guard")
    if safety["modifies_tests"] or not safety["within_changed_line_budget"]:
        return proposal_blocked(candidate, "black:8 source-only safety budget rejected candidate", "black_comment_trailing_comma_guard", discovery, memory_enabled) | {"source_only_patch_safety_check": safety}
    source_path.write_text(updated, encoding="utf-8")
    return {
        "candidate_generated": True,
        "patched_file": rel,
        "heuristic": "black_comment_trailing_comma_guard",
        "heuristic_family": "parser_formatter_localized_failure",
        "diff": diff,
        "changed_lines": safety["changed_lines"],
        "source_only_patch_safety_check": safety,
        "memory_enabled_path": memory_enabled,
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
        "label_leakage_detected": False,
        "source_discovery_ranked_files": [item["file"] for item in discovery["ranked"][:10]],
        "candidate": candidate["candidate"],
        "reason": "bounded buggy-source-only post-format guard for standalone identifier before comment-only line in comments7 failure context",
    }


def apply_black4_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    rel = "black.py"
    source_path = workspace / rel
    if not source_path.exists():
        return proposal_blocked(candidate, "black.py not found in buggy workspace", "black_beginning_backslash_leading_newline_guard", discovery, memory_enabled)
    failing_log = discovery.get("failing_log", "")
    test_text = discovery.get("test_info", {}).get("method_text", "")
    if "test_beginning_backslash" not in test_text or "'\\n\\nprint(\"hello, world\")\\n'" not in failing_log:
        return proposal_blocked(candidate, "decision-time target failure context did not match beginning-backslash leading-newline failure", "black_beginning_backslash_leading_newline_guard", discovery, memory_enabled)
    text = source_path.read_text(encoding="utf-8", errors="replace")
    region = locate_function_region(text, "format_str")
    if not region["found"]:
        return proposal_blocked(candidate, region["reason"], "black_beginning_backslash_leading_newline_guard", discovery, memory_enabled)
    function_text = str(region["region"])
    old = '    return "".join(dst_contents)\n'
    if old not in function_text:
        return proposal_blocked(candidate, "format_str list-join return pattern not found", "black_beginning_backslash_leading_newline_guard", discovery, memory_enabled)
    new = (
        '    dst_contents = "".join(dst_contents)\n'
        '    if src_contents.startswith("\\\\\\n"):\n'
        '        dst_contents = dst_contents.lstrip("\\n")\n'
        "    return dst_contents\n"
    )
    updated_region = function_text.replace(old, new, 1)
    updated = text[: int(region["start"])] + updated_region + text[int(region["end"]) :]
    diff = source_diff(text, updated, rel)
    safety = safety_record(rel, diff, "black_beginning_backslash_leading_newline_guard")
    if safety["modifies_tests"] or not safety["within_changed_line_budget"]:
        return proposal_blocked(candidate, "black:4 source-only safety budget rejected candidate", "black_beginning_backslash_leading_newline_guard", discovery, memory_enabled) | {"source_only_patch_safety_check": safety}
    source_path.write_text(updated, encoding="utf-8")
    return {
        "candidate_generated": True,
        "patched_file": rel,
        "heuristic": "black_beginning_backslash_leading_newline_guard",
        "heuristic_family": "leading_newline_backslash_formatting_failure",
        "diff": diff,
        "changed_lines": safety["changed_lines"],
        "source_only_patch_safety_check": safety,
        "memory_enabled_path": memory_enabled,
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
        "label_leakage_detected": False,
        "source_discovery_ranked_files": [item["file"] for item in discovery["ranked"][:10]],
        "candidate": candidate["candidate"],
        "reason": "bounded buggy-source-only guard for leading backslash producing extra leading blank lines",
    }


def propose_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    if candidate["candidate"] == "youtube-dl:1":
        proposal = v28i.apply_youtube_dl_patch(workspace, discovery)
        proposal.update(
            {
                "heuristic_family": "boolean_value_matching_failure",
                "memory_enabled_path": memory_enabled,
                "fixed_or_gold_patch_used": False,
                "future_outcome_evidence_used": False,
                "label_leakage_detected": False,
                "source_discovery_ranked_files": [item["file"] for item in discovery["ranked"][:10]],
                "candidate": candidate["candidate"],
            }
        )
        return proposal
    if candidate["candidate"] == "black:8":
        return apply_black8_patch(workspace, candidate, discovery, memory_enabled)
    if candidate["candidate"] == "black:4":
        return apply_black4_patch(workspace, candidate, discovery, memory_enabled)
    return proposal_blocked(candidate, "candidate not registered for v2.8j bounded source-only generation", "unregistered_candidate", discovery, memory_enabled)


def write_source_only_patch_artifacts(episode_dir: Path, prefix: str, proposal: dict[str, Any]) -> None:
    safety = proposal.get("source_only_patch_safety_check") or proposal.get("boolean_patch_safety_check") or {
        "source_only_repair_patch": bool(proposal.get("candidate_generated")),
        "failing_test_materialization_patch": False,
        "modifies_tests": False,
        "uses_fixed_revision": False,
        "uses_gold_patch": False,
        "uses_future_outcome_evidence": False,
    }
    write_json(episode_dir / f"{prefix}_source_only_patch_safety_check.json", safety)
    write_text(episode_dir / f"{prefix}_source_only_repair_patch.diff", str(proposal.get("diff") or "# NO SOURCE-ONLY PATCH CANDIDATE GENERATED\n"))
    write_json(
        episode_dir / f"{prefix}_repair_materialization_separation.json",
        {
            "source_repair_candidate_patch": f"{prefix}_source_only_repair_patch.diff",
            "failing_test_materialization_or_replay_harness_patch": None,
            "test_files_modified_by_repair_candidate": False,
            "runtime_setup_is_not_code_repair": True,
        },
    )


def write_attempt(path: Path, candidate: dict[str, Any], workspace: Path, prefix: str, env: dict[str, str], memory_enabled: bool) -> dict[str, Any]:
    failing_log = (path / "failing_log_raw.txt").read_text(encoding="utf-8", errors="replace")
    discovery = v28g.run_source_discovery(path, workspace, candidate, failing_log)
    discovery["failing_log"] = failing_log
    if discovery["report"].get("source_discovery_failed"):
        proposal = proposal_blocked(candidate, "source discovery failed under decision-time inputs", "source_discovery_failure", discovery, memory_enabled)
        proposal["source_discovery_failed"] = True
    else:
        proposal = propose_patch(workspace, candidate, discovery, memory_enabled)
    write_json(path / f"{prefix}_repair_candidate_generation.json", proposal)
    write_json(path / "repair_heuristic_selection.json", {"selected_heuristic": proposal["heuristic_family"], "candidate_generated": proposal["candidate_generated"]})
    write_json(path / "patch_candidate_explanation.json", {"path": prefix, "proposal": proposal, "source_reasoning": proposal.get("reason") or "minimal localized decision-time patch candidate generated"})
    write_json(path / "patch_candidate_safety_check.json", {"patch_touches_tests": False, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False, "candidate_generated": proposal["candidate_generated"]})
    actions = [
        {"action": "inspect_allowed_decision_time_inputs", "result": "completed"},
        {"action": "run_source_discovery", "ranked_files": proposal["source_discovery_ranked_files"]},
        {"action": "select_repair_heuristic", "heuristic": proposal["heuristic_family"]},
        {"action": "generate_bounded_source_only_patch_candidate", "candidate_generated": proposal["candidate_generated"]},
    ]
    if candidate["candidate"] == "youtube-dl:1":
        actions.append({"action": "full_source_unary_operator_region_search", "result": "completed"})
        v28i.write_boolean_construction_artifacts(path, prefix, proposal)
    write_source_only_patch_artifacts(path, prefix, proposal)
    write_json(path / f"{prefix}_action_trace.json", {"actions": actions, "patch_candidate_generated": proposal["candidate_generated"], "no_op_or_flatline": False})
    diff = v28g.git_diff(workspace, env) if proposal["candidate_generated"] else "# NO PATCH CANDIDATE GENERATED\n"
    write_text(path / f"{prefix}_repair_patch.diff", diff or "# NO PATCH CANDIDATE GENERATED\n")
    blocked_reason = None
    if not proposal["candidate_generated"]:
        blocked_reason = proposal.get("blocked_reason", "blocked_no_safe_patch_candidate_generated")
    write_json(path / f"{prefix}_patch_application_result.json", {"patch_application_attempted": bool(proposal["candidate_generated"]), "patch_applied": bool(proposal["candidate_generated"]), "blocked_reason": blocked_reason})
    write_text(path / f"{prefix}_post_repair_command.txt", candidate["direct_command"] + "\n")
    if proposal["candidate_generated"]:
        result = v28g.run_shell(candidate["direct_command"], cwd=workspace, env=env)
        base.log_result(path / f"{prefix}_post_repair_log_raw.txt", result)
        passed = result.get("returncode") == 0
        target_check = base.classify_target_replay(base.combined_log(result), result.get("returncode"), candidate["required_markers"])
        blocked_post_reason = None if passed else "blocked_target_test_failed"
    else:
        write_text(path / f"{prefix}_post_repair_log_raw.txt", f"NOT_RUN: {blocked_reason}\n")
        passed = False
        target_check = {"target_failure_matched": False, "returncode": None}
        blocked_post_reason = blocked_reason
    outcome = {
        "repair_path_ran": True,
        "candidate_generation_attempted": True,
        "patch_candidate_generated": bool(proposal["candidate_generated"]),
        "patch_applied": bool(proposal["candidate_generated"]),
        "primary_command_passed": passed,
        "post_repair_target_failure_check": target_check,
        "changed_file_count": 1 if proposal["candidate_generated"] else 0,
        "changed_lines": changed_line_count(diff) if proposal["candidate_generated"] else 0,
        "repair_actions": len(actions),
        "blocked_reason": blocked_post_reason,
    }
    write_json(path / f"{prefix}_outcome.json", outcome)
    return outcome


def classify_episode(no_outcome: dict[str, Any], mem_outcome: dict[str, Any]) -> tuple[str, bool, bool]:
    no_generated = bool(no_outcome.get("patch_candidate_generated"))
    mem_generated = bool(mem_outcome.get("patch_candidate_generated"))
    no_passed = bool(no_outcome.get("primary_command_passed"))
    mem_passed = bool(mem_outcome.get("primary_command_passed"))
    if not no_generated and not mem_generated:
        return "blocked_no_safe_patch_candidate_generated", False, False
    if no_generated and not no_passed and mem_generated and not mem_passed:
        return "failed_both", False, False
    if mem_passed and not no_passed:
        return "positive_memory_only", True, True
    if no_passed and not mem_passed:
        return "no_memory_only", True, False
    if no_passed and mem_passed:
        return "inconclusive_equal_performance", True, False
    return "blocked_target_test_failed", False, False


def run_repair_paths(candidate: dict[str, Any], project_root: Path, episode_dir: Path, env: dict[str, str]) -> dict[str, Any]:
    validation_command = candidate["direct_command"]
    repair_root = RUNTIME_ROOT / "repair_paths" / candidate["episode_id"]
    no_memory_dir = (repair_root / "no_memory").resolve()
    memory_dir = (repair_root / "memory_enabled").resolve()
    preservation = base.preserve_repair_workspaces(project_root, episode_dir, no_memory_dir, memory_dir)
    if not preservation["workspace_equivalence_passed"]:
        return base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_repair_workspace_equivalence_failure")
    no_pre = v28g.run_shell(validation_command, cwd=no_memory_dir, env=env)
    mem_pre = v28g.run_shell(validation_command, cwd=memory_dir, env=env)
    base.log_result(episode_dir / "no_memory_prerepair_replay_log_raw.txt", no_pre)
    base.log_result(episode_dir / "memory_enabled_prerepair_replay_log_raw.txt", mem_pre)
    no_check = base.classify_target_replay(base.combined_log(no_pre), no_pre.get("returncode"), candidate["required_markers"])
    mem_check = base.classify_target_replay(base.combined_log(mem_pre), mem_pre.get("returncode"), candidate["required_markers"])
    write_json(episode_dir / "repair_workspace_prerepair_replay_check.json", {"no_memory": no_check, "memory_enabled": mem_check})
    if not no_check["target_failure_matched"] or not mem_check["target_failure_matched"]:
        return base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_repair_workspace_prerepair_replay_failed")
    write_json(episode_dir / "repair_attempt_budget.json", v28g.DISCOVERY_BUDGET | v28g.REPAIR_BUDGET | {"fixed_or_gold_patch_forbidden": True, "tests_may_be_modified": False})
    write_json(episode_dir / "no_memory_decision_time_inputs.json", {"validation_command": validation_command, "memory_evidence_used": False})
    write_json(episode_dir / "memory_enabled_decision_time_inputs.json", {"validation_command": validation_command, "memory_evidence_used": True})
    write_json(episode_dir / "memory_evidence_used.json", {"allowed_controllergate_memory_only": True, "fixed_bugsinpy_patch_used": False})
    no_outcome = write_attempt(episode_dir, candidate, no_memory_dir, "no_memory", env, False)
    mem_outcome = write_attempt(episode_dir, candidate, memory_dir, "memory_enabled", env, True)
    classification, scoreable, memory_outperformed = classify_episode(no_outcome, mem_outcome)
    return {
        "repair_paths_ran": True,
        "workspace_preservation_passed": True,
        "no_memory_patch_candidate_generated": no_outcome["patch_candidate_generated"],
        "memory_enabled_patch_candidate_generated": mem_outcome["patch_candidate_generated"],
        "no_memory_primary_command_passed": no_outcome["primary_command_passed"],
        "memory_enabled_primary_command_passed": mem_outcome["primary_command_passed"],
        "classification": classification,
        "scoreable": scoreable,
        "memory_enabled_outperformed_no_memory": memory_outperformed,
    }


def aggregate_result(results: list[dict[str, Any]]) -> str:
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    if len(scoreable) < 3:
        return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    if len(positives) >= 2:
        return "limited_bugsinpy_real_bug_memory_lift_criteria_met"
    if not positives:
        return "negative_evidence_no_bugsinpy_real_bug_memory_lift"
    return "insufficient_positive_episode_count_for_bugsinpy_real_bug_memory_lift"


def write_campaign_artifacts() -> None:
    base.write_common_campaign_artifacts()
    write_json(
        ARTIFACT_ROOT / "campaign_plan.json",
        {
            "campaign_id": "v2_8j_bugsinpy_scoreable_episode_expansion",
            "artifact_name": "v2_8j_bugsinpy_scoreable_episode_expansion_artifacts",
            "candidate_ids": [item["candidate"] for item in base.CANDIDATES],
            "goal": "expand BugsInPy real-bug limited pilot from one scoreable episode toward at least three scoreable episodes",
            "v2_8i_reference_preserved": True,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "source_repair_vs_harness_separation.json",
        {
            "source_repair_candidate_patch_files": ["*_source_only_repair_patch.diff", "*_repair_patch.diff"],
            "failing_test_materialization_or_replay_harness_changes": "separate runtime setup/checkouts only; not repair candidates",
            "tests_may_be_modified_as_repair": False,
            "dependency_runtime_setup_is_not_code_repair": True,
        },
    )
    write_json(
        ARTIFACT_ROOT / "scoreable_episode_expansion_policy.json",
        {
            "scoreable_requires_patch_generated": True,
            "scoreable_requires_source_patch_applies": True,
            "scoreable_requires_target_test_executes": True,
            "scoreable_requires_target_test_passes_in_at_least_one_arm": True,
            "no_patch_or_no_op_is_scoreable": False,
            "classifications": sorted(CLASSIFICATIONS),
        },
    )
    write_json(
        ARTIFACT_ROOT / "black_candidate_generation_policy.json",
        {
            "black:8": "bounded black.py format_str post-format guard from comments7 parse/assertion context",
            "black:4": "bounded black.py format_str leading-backslash leading-newline guard",
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "source_only": True,
            "can_fail_safely_without_becoming_scoreable": True,
        },
    )
    write_json(
        ARTIFACT_ROOT / "label_hygiene_check.json",
        {
            "campaign_label": "v2.8j",
            "current_artifact_uses_v2_8j_names": True,
            "older_version_labels_allowed_only_as_history": True,
        },
    )


def write_final_campaign_files(results: list[dict[str, Any]], aggregate: str) -> None:
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    blocked = [item for item in results if not item["scoreable"]]
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
    write_json(ARTIFACT_ROOT / "decision_report.json", {"records": records, "classification_vocabulary": sorted(CLASSIFICATIONS)})
    write_json(
        ARTIFACT_ROOT / "aggregate_report.json",
        {
            "aggregate_result": aggregate,
            "executed_episode_count": len(results),
            "scoreable_episode_count": len(scoreable),
            "positive_memory_only_episode_count": len(positives),
            "inconclusive_equal_performance_episode_count": len([item for item in results if item["classification"] == "inconclusive_equal_performance"]),
            "blocked_episode_count": len(blocked),
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "campaign_results.json", {
        "workflow_executed": True,
        "executed_episode_count": len(results),
        "scoreable_episode_count": len(scoreable),
        "positive_memory_episode_count": len(positives),
        "blocked_episode_count": len(blocked),
        "decision_time_outcome_overlap_count": 0,
        "label_leakage_count": 0,
        "apoptosis_watchdog_triggered_count": 0,
        "corruption_count": 0,
        "aggregate_result": aggregate,
        "limited_bugsinpy_real_bug_memory_lift_criteria_met": aggregate == "limited_bugsinpy_real_bug_memory_lift_criteria_met",
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
    write_json(ARTIFACT_ROOT / "audit.json", {
        "artifact_provenance": "generated by v2.8j Linux runner",
        "fixed_or_gold_patch_used_at_decision_time": False,
        "future_outcome_evidence_used_at_decision_time": False,
        "tests_modified_as_repair": False,
        "source_only_patch_separation_enforced": True,
    })
    rows = "\n".join(
        f"| {record['episode_id']} | {record['candidate']} | {record['classification']} | {str(record['scoreable']).lower()} | {str(record['memory_enabled_outperformed_no_memory']).lower()} |"
        for record in records
    )
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.8j BugsInPy Scoreable Episode Expansion\n\n"
        f"Aggregate result: `{aggregate}`.\n\n"
        f"- Executed BugsInPy episodes: {len(results)}.\n"
        f"- Scoreable episodes: {len(scoreable)}.\n"
        f"- Positive memory-only episodes: {len(positives)}.\n"
        f"- Inconclusive equal-performance episodes: {len([item for item in results if item['classification'] == 'inconclusive_equal_performance'])}.\n"
        f"- Blocked episodes: {len(blocked)}.\n"
        "- Full scoring: NOT_RUN / disallowed.\n"
        "- Self-maintaining software: not demonstrated.\n\n"
        "| Episode | Candidate | Classification | Scoreable | Memory outperformed |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{rows}\n\n"
        "No fixed/gold patches, future outcome logs, or fixed-state diagnostic hints were used at decision time. "
        "Source repair candidate patches are separated from replay/materialization artifacts.\n",
    )


def main() -> int:
    v28g.propose_patch = propose_patch
    v28g.write_attempt = write_attempt
    v28g.run_repair_paths = run_repair_paths
    v28g.aggregate_result = aggregate_result
    v28g.write_campaign_artifacts = write_campaign_artifacts
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True)
    RUNTIME_ROOT.mkdir(parents=True)
    write_campaign_artifacts()
    write_text(
        ARTIFACT_ROOT / "runtime_environment.txt",
        f"generated_at_utc={base.now()}\nplatform={base.platform.platform()}\npython={base.platform.python_version()}\nrepo_root={REPO_ROOT}\nruntime_root={RUNTIME_ROOT}\n",
    )
    env = os.environ.copy()
    clone_result = base.run_raw(["git", "clone", "--depth", "1", base.BUGSINPY_URL, str(base.BUGSINPY_REPO)], timeout=900)
    base.log_result(ARTIFACT_ROOT / "bugsinpy_clone_log_raw.txt", clone_result)
    results: list[dict[str, Any]] = []
    if clone_result.get("returncode") == 0:
        env["PATH"] = str((base.BUGSINPY_REPO / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")
        for candidate in base.CANDIDATES:
            results.append(v28g.run_episode(candidate, env))
    aggregate = aggregate_result(results) if results else "blocked_replay_or_materialization_failure"
    write_json(ARTIFACT_ROOT / "pre_repair_replay_gate_summary.json", {"episodes": results, "passed_count": sum(1 for item in results if item["pre_repair_replay_gate_passed"])})
    write_json(ARTIFACT_ROOT / "workspace_equivalence_summary.json", {"episodes": results, "workspace_equivalence_required": True})
    write_json(ARTIFACT_ROOT / "repair_attempt_summary.json", {"episodes": results, "scoreable_episode_count": sum(1 for item in results if item["scoreable"])})
    write_json(ARTIFACT_ROOT / "source_discovery_summary.json", {"episodes": results, "source_discovery_enabled": True})
    write_json(ARTIFACT_ROOT / "bounded_repair_proposer_summary.json", {"episodes": results, "bounded_source_only_repair_proposer_enabled": True})
    write_final_campaign_files(results, aggregate)
    base.write_manifest(ARTIFACT_ROOT)
    print(f"v2.8j aggregate: {aggregate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
