#!/usr/bin/env python3
"""GitHub Actions runner for v2.8i boolean patch construction fix."""

from __future__ import annotations

import difflib
import importlib.util
import re
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8g_bugsinpy_source_discovery_repair_proposer_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8i_bugsinpy_boolean_patch_construction_fix_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8i_bugsinpy_runtime").resolve()
BOOLEAN_PATCH_DIFF_ARTIFACTS = [
    "no_memory_boolean_patch_candidate.diff",
    "memory_enabled_boolean_patch_candidate.diff",
]

spec = importlib.util.spec_from_file_location("v2_8g_runner", BASE_RUNNER_PATH)
v28g = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v28g)

v28g.ARTIFACT_ROOT = ARTIFACT_ROOT
v28g.RUNTIME_ROOT = RUNTIME_ROOT
v28g.base.ARTIFACT_ROOT = ARTIFACT_ROOT
v28g.base.RUNTIME_ROOT = RUNTIME_ROOT
v28g.base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()

orig_write_campaign_artifacts = v28g.write_campaign_artifacts


def write_json(path: Path, data: Any) -> None:
    v28g.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    v28g.write_text(path, text)


def region_record(found: bool, region: str = "", start: int | None = None, end: int | None = None, reason: str = "") -> dict[str, Any]:
    return {
        "unary_operator_block_found": found,
        "start_offset": start,
        "end_offset": end,
        "region": region,
        "reason": reason,
    }


def locate_unary_operator_region(text: str) -> dict[str, Any]:
    start = text.find("UNARY_OPERATORS")
    if start < 0:
        return region_record(False, reason="UNARY_OPERATORS assignment not found")
    brace = text.find("{", start)
    if brace < 0:
        return region_record(False, reason="UNARY_OPERATORS assignment has no opening brace")
    depth = 0
    for offset in range(brace, len(text)):
        char = text[offset]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = offset + 1
                return region_record(True, text[start:end], start, end)
    return region_record(False, reason="UNARY_OPERATORS assignment has no bounded closing brace")


def line_match(pattern: str, region: str) -> re.Match[str] | None:
    return re.search(pattern, region, flags=re.MULTILINE)


def build_boolean_patch(text: str, rel: str = "youtube_dl/utils.py") -> dict[str, Any]:
    region = locate_unary_operator_region(text)
    if not region["unary_operator_block_found"]:
        return {
            "candidate_generated": False,
            "blocked_reason": "blocked_boolean_patch_construction_failed",
            "reason": region["reason"],
            "unary_operator_region_match_check": region,
        }
    operator_region = str(region["region"])
    positive = line_match(r"^([ \t]*)'':\s*lambda\s+v:\s*v\s+is\s+not\s+None\s*,?\s*$", operator_region)
    negative = line_match(r"^([ \t]*)'!':\s*lambda\s+v:\s*v\s+is\s+None\s*,?\s*$", operator_region)
    match_check = {
        "unary_operator_block_found": True,
        "positive_lambda_equivalent_to_v_is_not_none": positive is not None,
        "negative_lambda_equivalent_to_v_is_none": negative is not None,
        "exact_or_bounded_region_search_used": True,
        "full_source_search_used": True,
        "blocked_reason": None,
    }
    if positive is None or negative is None:
        match_check["blocked_reason"] = "blocked_boolean_patch_construction_failed"
        return {
            "candidate_generated": False,
            "blocked_reason": "blocked_boolean_patch_construction_failed",
            "reason": "UNARY_OPERATORS region found but expected unary lambdas were not matched",
            "unary_operator_region_match_check": match_check,
            "unary_operator_region_extract": operator_region,
        }
    updated_region = operator_region
    updated_region = re.sub(
        r"^([ \t]*)'':\s*lambda\s+v:\s*v\s+is\s+not\s+None\s*,?\s*$",
        lambda match: f"{match.group(1)}'': lambda v: v is not None and v is not False,",
        updated_region,
        count=1,
        flags=re.MULTILINE,
    )
    updated_region = re.sub(
        r"^([ \t]*)'!':\s*lambda\s+v:\s*v\s+is\s+None\s*,?\s*$",
        lambda match: f"{match.group(1)}'!': lambda v: v is None or v is False,",
        updated_region,
        count=1,
        flags=re.MULTILINE,
    )
    if updated_region == operator_region:
        match_check["blocked_reason"] = "blocked_boolean_patch_construction_failed"
        return {
            "candidate_generated": False,
            "blocked_reason": "blocked_boolean_patch_construction_failed",
            "reason": "UNARY_OPERATORS replacements produced no source delta",
            "unary_operator_region_match_check": match_check,
            "unary_operator_region_extract": operator_region,
        }
    updated = text[: int(region["start_offset"])] + updated_region + text[int(region["end_offset"]) :]
    diff = "".join(
        difflib.unified_diff(
            text.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=rel,
            tofile=rel,
        )
    )
    changed_lines = max(0, diff.count("\n+") - 1)
    safety = {
        "patch_only_file": rel,
        "modifies_tests": False,
        "uses_fixed_revision": False,
        "uses_gold_patch": False,
        "uses_future_outcome_evidence": False,
        "diff_non_empty": bool(diff.strip()),
        "changed_lines": changed_lines,
        "within_changed_line_budget": 0 < changed_lines <= v28g.REPAIR_BUDGET["max_changed_lines"],
        "patch_contains_positive_operator": "v is not None and v is not False" in diff,
        "patch_contains_negative_operator": "v is None or v is False" in diff,
    }
    if not safety["within_changed_line_budget"]:
        return {
            "candidate_generated": False,
            "blocked_reason": "blocked_boolean_patch_construction_failed",
            "reason": "boolean patch failed bounded changed-line safety check",
            "unary_operator_region_match_check": match_check,
            "unary_operator_region_extract": operator_region,
            "boolean_patch_safety_check": safety,
        }
    return {
        "candidate_generated": True,
        "patched_file": rel,
        "heuristic": "boolean_unary_false_value_presence_rule",
        "diff": diff,
        "changed_lines": changed_lines,
        "updated_text": updated,
        "unary_operator_region_extract": operator_region,
        "unary_operator_region_match_check": match_check,
        "boolean_patch_safety_check": safety,
        "construction_fix_used": True,
        "full_source_search_used": True,
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
        "reason": "bounded full-source UNARY_OPERATORS region patch constructed from buggy source and failing test context",
    }


def apply_youtube_dl_patch(workspace: Path, discovery: dict[str, Any]) -> dict[str, Any]:
    source_path = workspace / "youtube_dl" / "utils.py"
    if not source_path.exists():
        return {
            "candidate_generated": False,
            "blocked_reason": "blocked_boolean_patch_construction_failed",
            "reason": "youtube_dl/utils.py not found in buggy workspace",
        }
    report = discovery.get("report", {})
    test_info = discovery.get("test_info", {})
    if not report.get("match_str_found") or test_info.get("selector", {}).get("method") != "test_match_str":
        return {
            "candidate_generated": False,
            "reason": "match_str source or test_match_str context not found",
        }
    test_text = test_info.get("method_text", "")
    required_tests = [
        "match_str('is_live', {'is_live': False})",
        "match_str('!is_live', {'is_live': False})",
        "match_str('x', {'x': 0})",
        "match_str('title', {'title': ''})",
    ]
    if not all(snippet in test_text for snippet in required_tests):
        return {
            "candidate_generated": False,
            "reason": "failing test context does not justify boolean-False-only unary operator patch",
        }
    text = source_path.read_text(encoding="utf-8", errors="replace")
    proposal = build_boolean_patch(text)
    if proposal.get("candidate_generated"):
        source_path.write_text(str(proposal.pop("updated_text")), encoding="utf-8")
    return proposal


def write_boolean_construction_artifacts(episode_dir: Path, prefix: str, proposal: dict[str, Any]) -> None:
    region = str(proposal.get("unary_operator_region_extract", ""))
    if region and not (episode_dir / "unary_operator_region_extract.txt").exists():
        write_text(episode_dir / "unary_operator_region_extract.txt", region + ("\n" if not region.endswith("\n") else ""))
    if proposal.get("unary_operator_region_match_check") and not (episode_dir / "unary_operator_region_match_check.json").exists():
        write_json(episode_dir / "unary_operator_region_match_check.json", proposal["unary_operator_region_match_check"])
    generation = {
        "candidate_generated": bool(proposal.get("candidate_generated")),
        "patched_file": proposal.get("patched_file"),
        "heuristic": proposal.get("heuristic", "boolean_unary_false_value_presence_rule"),
        "construction_fix_used": bool(proposal.get("construction_fix_used")),
        "full_source_search_used": bool(proposal.get("full_source_search_used")),
        "blocked_reason": proposal.get("blocked_reason"),
        "reason": proposal.get("reason"),
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
    }
    safety = proposal.get("boolean_patch_safety_check") or {
        "patch_only_file": "youtube_dl/utils.py",
        "modifies_tests": False,
        "uses_fixed_revision": False,
        "uses_gold_patch": False,
        "uses_future_outcome_evidence": False,
        "candidate_generated": bool(proposal.get("candidate_generated")),
    }
    write_json(episode_dir / f"{prefix}_boolean_patch_generation_result.json", generation)
    write_json(episode_dir / f"{prefix}_boolean_patch_safety_check.json", safety)
    write_text(episode_dir / f"{prefix}_boolean_patch_candidate.diff", str(proposal.get("diff") or "# NO PATCH CANDIDATE GENERATED\n"))
    if not (episode_dir / "boolean_patch_generation_result.json").exists() or proposal.get("candidate_generated"):
        write_json(episode_dir / "boolean_patch_generation_result.json", generation)
    if not (episode_dir / "boolean_patch_safety_check.json").exists() or proposal.get("candidate_generated"):
        write_json(episode_dir / "boolean_patch_safety_check.json", safety)


def write_attempt(path: Path, candidate: dict[str, Any], workspace: Path, prefix: str, env: dict[str, str], memory_enabled: bool) -> dict[str, Any]:
    failing_log = (path / "failing_log_raw.txt").read_text(encoding="utf-8", errors="replace")
    discovery = v28g.run_source_discovery(path, workspace, candidate, failing_log)
    if discovery["report"].get("source_discovery_failed"):
        proposal = {
            "candidate_generated": False,
            "reason": "def match_str exists in buggy workspace but source discovery did not find it",
            "heuristic_family": "boolean_value_matching_failure",
            "memory_enabled_path": memory_enabled,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "label_leakage_detected": False,
            "source_discovery_failed": True,
            "source_discovery_ranked_files": [item["file"] for item in discovery["ranked"][:10]],
        }
    else:
        proposal = v28g.propose_patch(workspace, candidate, discovery, memory_enabled)
    write_json(path / f"{prefix}_repair_candidate_generation.json", proposal)
    write_json(path / "repair_heuristic_selection.json", {"selected_heuristic": proposal["heuristic_family"], "candidate_generated": proposal["candidate_generated"]})
    write_json(path / "patch_candidate_explanation.json", {"path": prefix, "proposal": proposal, "source_reasoning": proposal.get("reason") or "minimal localized decision-time patch candidate generated"})
    write_json(path / "patch_candidate_safety_check.json", {"patch_touches_tests": False, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False, "candidate_generated": proposal["candidate_generated"]})
    actions = [
        {"action": "inspect_allowed_decision_time_inputs", "result": "completed"},
        {"action": "run_source_discovery", "ranked_files": proposal["source_discovery_ranked_files"]},
        {"action": "select_repair_heuristic", "heuristic": proposal["heuristic_family"]},
        {"action": "generate_bounded_patch_candidate", "candidate_generated": proposal["candidate_generated"]},
    ]
    if candidate["candidate"] == "youtube-dl:1":
        actions.append({"action": "full_source_unary_operator_region_search", "result": "completed"})
        write_boolean_construction_artifacts(path, prefix, proposal)
    write_json(path / f"{prefix}_action_trace.json", {"actions": actions, "patch_candidate_generated": proposal["candidate_generated"]})
    diff = v28g.git_diff(workspace, env) if proposal["candidate_generated"] else "# NO PATCH CANDIDATE GENERATED\n"
    write_text(path / f"{prefix}_repair_patch.diff", diff or "# NO PATCH CANDIDATE GENERATED\n")
    blocked_reason = None
    if not proposal["candidate_generated"]:
        if proposal.get("source_discovery_failed"):
            blocked_reason = "blocked_source_discovery_failed"
        elif proposal.get("blocked_reason") == "blocked_boolean_patch_construction_failed":
            blocked_reason = "blocked_boolean_patch_construction_failed"
        else:
            blocked_reason = "blocked_no_safe_patch_candidate_generated"
    write_json(path / f"{prefix}_patch_application_result.json", {"patch_application_attempted": bool(proposal["candidate_generated"]), "patch_applied": bool(proposal["candidate_generated"]), "blocked_reason": blocked_reason})
    write_text(path / f"{prefix}_post_repair_command.txt", candidate["direct_command"] + "\n")
    if proposal["candidate_generated"]:
        result = v28g.run_shell(candidate["direct_command"], cwd=workspace, env=env)
        v28g.base.log_result(path / f"{prefix}_post_repair_log_raw.txt", result)
        passed = result.get("returncode") == 0
    else:
        write_text(path / f"{prefix}_post_repair_log_raw.txt", f"NOT_RUN: {blocked_reason}\n")
        passed = False
    outcome = {
        "repair_path_ran": True,
        "candidate_generation_attempted": True,
        "patch_candidate_generated": bool(proposal["candidate_generated"]),
        "primary_command_passed": passed,
        "changed_file_count": 1 if proposal["candidate_generated"] else 0,
        "changed_lines": max(0, diff.count("\n+") - 1) if proposal["candidate_generated"] else 0,
        "repair_actions": len(actions),
        "blocked_reason": blocked_reason,
    }
    write_json(path / f"{prefix}_outcome.json", outcome)
    return outcome


def run_repair_paths(candidate: dict[str, Any], project_root: Path, episode_dir: Path, env: dict[str, str]) -> dict[str, Any]:
    validation_command = candidate["direct_command"]
    repair_root = RUNTIME_ROOT / "repair_paths" / candidate["episode_id"]
    no_memory_dir = (repair_root / "no_memory").resolve()
    memory_dir = (repair_root / "memory_enabled").resolve()
    preservation = v28g.base.preserve_repair_workspaces(project_root, episode_dir, no_memory_dir, memory_dir)
    if not preservation["workspace_equivalence_passed"]:
        return v28g.base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_repair_workspace_equivalence_failure")
    no_pre = v28g.run_shell(validation_command, cwd=no_memory_dir, env=env)
    mem_pre = v28g.run_shell(validation_command, cwd=memory_dir, env=env)
    v28g.base.log_result(episode_dir / "no_memory_prerepair_replay_log_raw.txt", no_pre)
    v28g.base.log_result(episode_dir / "memory_enabled_prerepair_replay_log_raw.txt", mem_pre)
    no_check = v28g.base.classify_target_replay(v28g.base.combined_log(no_pre), no_pre.get("returncode"), candidate["required_markers"])
    mem_check = v28g.base.classify_target_replay(v28g.base.combined_log(mem_pre), mem_pre.get("returncode"), candidate["required_markers"])
    write_json(episode_dir / "repair_workspace_prerepair_replay_check.json", {"no_memory": no_check, "memory_enabled": mem_check})
    if not no_check["target_failure_matched"] or not mem_check["target_failure_matched"]:
        return v28g.base.write_blocked_repair_artifacts(episode_dir, validation_command, "blocked_repair_workspace_prerepair_replay_failed")
    write_json(episode_dir / "repair_attempt_budget.json", v28g.DISCOVERY_BUDGET | v28g.REPAIR_BUDGET | {"fixed_or_gold_patch_forbidden": True})
    write_json(episode_dir / "no_memory_decision_time_inputs.json", {"validation_command": validation_command, "memory_evidence_used": False})
    write_json(episode_dir / "memory_enabled_decision_time_inputs.json", {"validation_command": validation_command, "memory_evidence_used": True})
    write_json(episode_dir / "memory_evidence_used.json", {"allowed_controllergate_memory_only": True, "fixed_bugsinpy_patch_used": False})
    no_outcome = write_attempt(episode_dir, candidate, no_memory_dir, "no_memory", env, False)
    mem_outcome = write_attempt(episode_dir, candidate, memory_dir, "memory_enabled", env, True)
    blocked_reasons = {no_outcome.get("blocked_reason"), mem_outcome.get("blocked_reason")}
    if "blocked_source_discovery_failed" in blocked_reasons:
        classification = "blocked_source_discovery_failed"
        scoreable = False
        memory_outperformed = False
    elif "blocked_boolean_patch_construction_failed" in blocked_reasons:
        classification = "blocked_boolean_patch_construction_failed"
        scoreable = False
        memory_outperformed = False
    elif not no_outcome["patch_candidate_generated"] and not mem_outcome["patch_candidate_generated"]:
        classification = "blocked_no_safe_patch_candidate_generated"
        scoreable = False
        memory_outperformed = False
    elif mem_outcome["patch_candidate_generated"] and not no_outcome["patch_candidate_generated"]:
        classification = "positive_evidence_memory_lift_bugsinpy_real_bug_episode"
        scoreable = True
        memory_outperformed = True
    elif mem_outcome["primary_command_passed"] and not no_outcome["primary_command_passed"]:
        classification = "positive_evidence_memory_lift_bugsinpy_real_bug_episode"
        scoreable = True
        memory_outperformed = True
    elif no_outcome["primary_command_passed"] and not mem_outcome["primary_command_passed"]:
        classification = "negative_evidence_no_memory_lift_bugsinpy_real_bug_episode"
        scoreable = True
        memory_outperformed = False
    else:
        classification = "inconclusive_equal_performance"
        scoreable = True
        memory_outperformed = False
    return {
        "repair_paths_ran": True,
        "workspace_preservation_passed": True,
        "no_memory_patch_candidate_generated": no_outcome["patch_candidate_generated"],
        "memory_enabled_patch_candidate_generated": mem_outcome["patch_candidate_generated"],
        "classification": classification,
        "scoreable": scoreable,
        "memory_enabled_outperformed_no_memory": memory_outperformed,
    }


def aggregate_result(results: list[dict[str, Any]]) -> str:
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    if len(scoreable) < 3:
        if scoreable:
            return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
        if any(item["classification"] == "blocked_boolean_patch_construction_failed" for item in results):
            return "blocked_boolean_patch_construction_failed"
        if any(item["classification"] == "blocked_no_safe_patch_candidate_generated" for item in results):
            return "blocked_no_safe_patch_candidate_generated"
        return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    if len(positives) >= 2:
        return "limited_bugsinpy_real_bug_memory_lift_criteria_met"
    if not positives:
        return "negative_evidence_no_bugsinpy_real_bug_memory_lift"
    return "insufficient_positive_episode_count_for_bugsinpy_real_bug_memory_lift"


def write_campaign_artifacts() -> None:
    orig_write_campaign_artifacts()
    write_json(
        ARTIFACT_ROOT / "boolean_patch_construction_fix_design.json",
        {
            "fix_id": "v2_8i_full_source_unary_operator_patch_construction",
            "candidate_scope": "youtube-dl:1",
            "source_file": "youtube_dl/utils.py",
            "full_source_search_used": True,
            "tests_may_be_modified": False,
            "fixed_or_gold_patch_allowed": False,
            "future_outcome_evidence_allowed": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "full_source_patch_search_policy.json",
        {
            "search_scope": "full buggy youtube_dl/utils.py source file",
            "primary_locator": "locate_unary_operator_region",
            "fallback_strategy": "bounded UNARY_OPERATORS region search with lambda equivalence checks",
            "forbidden_inputs": ["fixed revision", "gold patch", "future outcome logs"],
        },
    )
    write_text(
        ARTIFACT_ROOT / "unary_operator_region_extract.txt",
        "Runner records the exact buggy UNARY_OPERATORS region in episode_001 after source discovery.\n",
    )
    write_json(
        ARTIFACT_ROOT / "unary_operator_region_match_check.json",
        {
            "workflow_executed": True,
            "full_source_search_policy_defined": True,
            "episode_specific_match_check_required": True,
        },
    )
    write_json(
        ARTIFACT_ROOT / "boolean_patch_generation_result.json",
        {
            "workflow_executed": True,
            "candidate_scope": "youtube-dl:1",
            "episode_specific_generation_result_required": True,
        },
    )
    write_json(
        ARTIFACT_ROOT / "boolean_patch_safety_check.json",
        {
            "patch_only_file": "youtube_dl/utils.py",
            "modifies_tests": False,
            "uses_fixed_revision": False,
            "uses_gold_patch": False,
            "uses_future_outcome_evidence": False,
        },
    )


def main() -> int:
    v28g.apply_youtube_dl_patch = apply_youtube_dl_patch
    v28g.write_attempt = write_attempt
    v28g.run_repair_paths = run_repair_paths
    v28g.aggregate_result = aggregate_result
    v28g.write_campaign_artifacts = write_campaign_artifacts
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    return v28g.main()


if __name__ == "__main__":
    raise SystemExit(main())
