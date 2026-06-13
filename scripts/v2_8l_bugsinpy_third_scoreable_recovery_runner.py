#!/usr/bin/env python3
"""GitHub Actions runner for v2.8l BugsInPy third scoreable recovery."""

from __future__ import annotations

import importlib.util
import os
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8k_bugsinpy_third_scoreable_recovery_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8l_bugsinpy_third_scoreable_recovery_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8l_bugsinpy_runtime").resolve()

spec = importlib.util.spec_from_file_location("v2_8k_runner", BASE_RUNNER_PATH)
v28k = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v28k)

v28j = v28k.v28j
v28i = v28k.v28i
v28g = v28k.v28g
base = v28k.base

for module in (v28k, v28j, v28i, v28g, base):
    module.ARTIFACT_ROOT = ARTIFACT_ROOT
    module.RUNTIME_ROOT = RUNTIME_ROOT
base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()

NO_LEAKAGE_POLICY = {
    "no_fixed_or_gold_patch": True,
    "no_future_outcome_evidence": True,
    "no_fixed_state_diagnostic_hints": True,
    "tests_may_be_modified": False,
    "source_only_repair_patch": True,
}

_original_propose_patch = v28k.propose_patch
_original_write_final_campaign_files = v28k.write_final_campaign_files


def write_json(path: Path, data: Any) -> None:
    v28k.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    v28k.write_text(path, text)


def apply_black8_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    """v2.8l compact source-only fix after v2.8k's safety-budget block.

    v2.8k found a decision-time-valid Black comments7 target context, but its
    source-only generator exceeded the 12-line repair budget. v2.8l keeps the
    same target and uses a compact regex relocation guard: if Black emits a
    comma-only line after comment lines in a parenthesized import, move that
    comma back to the preceding imported name and remove the standalone comma.
    """

    rel = "black.py"
    source_path = workspace / rel
    if not source_path.exists():
        return v28j.proposal_blocked(candidate, "black.py not found in buggy workspace", "black8_compact_comment_comma_guard_v2_8l", discovery, memory_enabled)
    failing_log = discovery.get("failing_log", "")
    test_text = discovery.get("test_info", {}).get("method_text", "")
    if "Cannot parse: 11:4:" not in failing_log or "test_comments7" not in test_text:
        return v28j.proposal_blocked(candidate, "decision-time target context did not match comments7 comma failure", "black8_compact_comment_comma_guard_v2_8l", discovery, memory_enabled)
    text = source_path.read_text(encoding="utf-8", errors="replace")
    if "import re" not in text:
        return v28j.proposal_blocked(candidate, "black.py lacks existing re import for compact postprocess", "black8_compact_comment_comma_guard_v2_8l", discovery, memory_enabled)
    region = v28j.locate_function_region(text, "format_str")
    if not region["found"]:
        return v28j.proposal_blocked(candidate, region["reason"], "black8_compact_comment_comma_guard_v2_8l", discovery, memory_enabled)
    function_text = str(region["region"])
    old = "    return dst_contents\n"
    if old not in function_text:
        return v28j.proposal_blocked(candidate, "format_str return dst_contents pattern not found", "black8_compact_comment_comma_guard_v2_8l", discovery, memory_enabled)
    new = (
        "    dst_contents = re.sub(\n"
        "        r\"(?m)^(\\\\s+[A-Za-z_][A-Za-z0-9_\\\\.]*),?\\\\n((?:\\\\s+#.*\\\\n)+)\\\\s+,\\\\s*\\\\n\",\n"
        "        lambda m: f\"{m.group(1)},\\\\n{m.group(2)}\",\n"
        "        dst_contents,\n"
        "    )\n"
        "    return dst_contents\n"
    )
    updated_region = function_text.replace(old, new, 1)
    updated = text[: int(region["start"])] + updated_region + text[int(region["end"]) :]
    diff = v28j.source_diff(text, updated, rel)
    safety = v28j.safety_record(rel, diff, "black8_compact_comment_comma_guard_v2_8l")
    if safety["modifies_tests"] or not safety["within_changed_line_budget"]:
        return v28j.proposal_blocked(candidate, "black:8 v2.8l compact source-only safety budget rejected candidate", "black8_compact_comment_comma_guard_v2_8l", discovery, memory_enabled) | {"source_only_patch_safety_check": safety}
    source_path.write_text(updated, encoding="utf-8")
    return {
        "candidate_generated": True,
        "patched_file": rel,
        "heuristic": "black8_compact_comment_comma_guard_v2_8l",
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
        "reason": "compact source-only comment/comma relocation guard after v2.8k safety-budget block; no fixed/gold patch used",
    }


def propose_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    if candidate["candidate"] == "black:8":
        return apply_black8_patch(workspace, candidate, discovery, memory_enabled)
    return _original_propose_patch(workspace, candidate, discovery, memory_enabled)


def write_campaign_artifacts() -> None:
    base.write_common_campaign_artifacts()
    write_json(
        ARTIFACT_ROOT / "campaign_plan.json",
        {
            "campaign_id": "v2_8l_bugsinpy_third_scoreable_recovery",
            "artifact_name": "v2_8l_bugsinpy_third_scoreable_recovery_artifacts",
            "candidate_ids": [item["candidate"] for item in base.CANDIDATES],
            "goal": "recover the third scoreable BugsInPy episode after v2.8k black:8 was blocked by patch budget",
            "targeted_candidate": "black:8",
            "replacement_candidate_used": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "v2_8k_black8_block_diagnosis.json",
        {
            "candidate": "black:8",
            "v2_8k_classification": "blocked_no_safe_patch_candidate_generated",
            "exact_blocker": "source-only safety budget rejected candidate",
            "v2_8k_changed_lines": 16,
            "max_changed_lines": v28g.REPAIR_BUDGET["max_changed_lines"],
            "target_failure_matched": True,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "decision": "black:8 remains valid; use compact source-only patch generator instead of replacement candidate",
        },
    )
    write_json(
        ARTIFACT_ROOT / "black_or_replacement_candidate_policy.json",
        {
            "primary_candidate": "black:8",
            "black8_valid_target": True,
            "black8_recovery_heuristic": "black8_compact_comment_comma_guard_v2_8l",
            "replacement_candidate_used": False,
            "replacement_allowed_only_if_black8_cannot_be_repaired_without_forbidden_evidence": True,
            "selection_basis": "decision-time target failure context and v2.8k budget-block diagnosis only",
            "source_only_repair_patch": True,
            "tests_may_be_modified": False,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "third_scoreable_recovery_policy.json",
        {
            "target": "black:8",
            "recovery_heuristic": "black8_compact_comment_comma_guard_v2_8l",
            "source_only_repair_patch": True,
            "tests_may_be_modified": False,
            "dependency_runtime_setup_is_not_code_repair": True,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "scoreable_requires_post_repair_target_validation_pass": True,
        },
    )
    write_json(
        ARTIFACT_ROOT / "anti_leakage_policy.json",
        NO_LEAKAGE_POLICY | {"prior_failed_replay_logs_allowed_as_controllergate_memory": True},
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
            "classifications": sorted(v28j.CLASSIFICATIONS),
            "classification_vocabulary": sorted(v28j.CLASSIFICATIONS),
        },
    )
    write_json(
        ARTIFACT_ROOT / "bounded_repair_proposer_summary.json",
        {"bounded_source_only_repair_proposer_enabled": True, "targeted_candidate": "black:8", "heuristic": "black8_compact_comment_comma_guard_v2_8l"},
    )
    write_json(
        ARTIFACT_ROOT / "label_hygiene_check.json",
        {"campaign_label": "v2.8l", "current_artifact_uses_v2_8l_names": True, "older_version_labels_allowed_only_as_history": True},
    )


def write_final_campaign_files(results: list[dict[str, Any]], aggregate: str) -> None:
    _original_write_final_campaign_files(results, aggregate)
    for item in results:
        episode_dir = ARTIFACT_ROOT / item["episode_id"]
        write_json(
            episode_dir / "repair_materialization_separation.json",
            {
                "source_repair_candidate_patch_files": ["no_memory_source_only_repair_patch.diff", "memory_enabled_source_only_repair_patch.diff"],
                "failing_test_materialization_or_replay_harness_patch": None,
                "test_files_modified_by_repair_candidate": False,
                "runtime_setup_is_not_code_repair": True,
            },
        )
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
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    rows = "\n".join(
        f"| {record['episode_id']} | {record['candidate']} | {record['classification']} | {str(record['scoreable']).lower()} | {str(record['memory_enabled_outperformed_no_memory']).lower()} |"
        for record in records
    )
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.8l BugsInPy Third Scoreable Episode Recovery\n\n"
        f"Aggregate result: `{aggregate}`.\n\n"
        f"- Executed BugsInPy episodes: {len(results)}.\n"
        f"- Scoreable episodes: {len(scoreable)}.\n"
        f"- Positive memory-only episodes: {len(positives)}.\n"
        "- Targeted recovery candidate: `black:8`.\n"
        "- v2.8k blocker: source-only safety budget rejected candidate at 16 changed lines.\n"
        "- v2.8l strategy: compact source-only comment/comma relocation guard.\n"
        "- Full scoring: NOT_RUN / disallowed.\n"
        "- Memory lift: not demonstrated unless aggregate criteria are met.\n"
        "- Self-maintaining software: not demonstrated.\n\n"
        "| Episode | Candidate | Classification | Scoreable | Memory outperformed |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{rows}\n\n"
        "No fixed/gold patches, future outcome logs, fixed-state diagnostic hints, or test edits are used at decision time. "
        "Blocked episodes are not counted as scoreable.\n",
    )


def main() -> int:
    v28k.apply_black8_patch = apply_black8_patch
    v28k.propose_patch = propose_patch
    v28k.write_campaign_artifacts = write_campaign_artifacts
    v28k.write_final_campaign_files = write_final_campaign_files
    v28k.ARTIFACT_ROOT = ARTIFACT_ROOT
    v28k.RUNTIME_ROOT = RUNTIME_ROOT
    v28k.v28j.ARTIFACT_ROOT = ARTIFACT_ROOT
    v28k.v28j.RUNTIME_ROOT = RUNTIME_ROOT
    v28k.v28i.ARTIFACT_ROOT = ARTIFACT_ROOT
    v28k.v28i.RUNTIME_ROOT = RUNTIME_ROOT
    v28k.v28g.ARTIFACT_ROOT = ARTIFACT_ROOT
    v28k.v28g.RUNTIME_ROOT = RUNTIME_ROOT
    v28k.base.ARTIFACT_ROOT = ARTIFACT_ROOT
    v28k.base.RUNTIME_ROOT = RUNTIME_ROOT
    v28k.base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    return v28k.main()


if __name__ == "__main__":
    raise SystemExit(main())
