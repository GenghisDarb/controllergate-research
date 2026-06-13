#!/usr/bin/env python3
"""GitHub Actions runner for v2.8m BugsInPy replacement third scoreable episode.

v2.8m preserves the official v2.8l result, freezes black:8 as failed_both, and
adds a fourth outcome-blind replacement BugsInPy candidate. The replacement is
selected before repair outcome, using only BugsInPy metadata and baseline
target-failure materialization.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8l_bugsinpy_third_scoreable_recovery_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8m_bugsinpy_replacement_third_scoreable_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8m_bugsinpy_runtime").resolve()

spec = importlib.util.spec_from_file_location("v2_8l_runner", BASE_RUNNER_PATH)
v28l = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v28l)

v28k = v28l.v28k
v28j = v28l.v28j
v28i = v28l.v28i
v28g = v28l.v28g
base = v28l.base

for module in (v28l, v28k, v28j, v28i, v28g, base):
    module.ARTIFACT_ROOT = ARTIFACT_ROOT
    module.RUNTIME_ROOT = RUNTIME_ROOT
base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()

ORIGINAL_RUN_EPISODE = v28g.run_episode
ORIGINAL_PROPOSE_PATCH = v28l.propose_patch
ORIGINAL_WRITE_FINAL_CAMPAIGN_FILES = v28l.write_final_campaign_files

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
        "reason": "next untouched pure-Python Black BugsInPy candidate after black:4 and black:8",
        "status": "selected_outcome_blind_replacement",
    },
    {
        "candidate": "black:5",
        "project": "black",
        "bug_id": "5",
        "reason": "excluded from v2.8m because fixed-patch contents were exposed during local investigation; not decision-time clean",
        "status": "excluded_fixed_patch_exposure",
    },
    {
        "candidate": "black:1",
        "project": "black",
        "bug_id": "1",
        "reason": "previous direct-runner attempts were runtime/environment blocked",
        "status": "excluded_prior_runtime_blocked",
    },
    {
        "candidate": "black:3",
        "project": "black",
        "bug_id": "3",
        "reason": "previous direct-runner attempts were runtime/environment blocked",
        "status": "excluded_prior_runtime_blocked",
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
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: youtube-dl:1",
        "required_markers": ["FAIL:", "TestUtil.test_match_str", "AssertionError"],
        "dependency_hints": [],
    },
    {
        "episode_id": "episode_002",
        "candidate": "black:8",
        "project": "black",
        "bug_id": "8",
        "direct_command": "python -m unittest -q tests.test_black.BlackTestCase.test_comments7",
        "target_test_file": "tests/test_black.py",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:8",
        "required_markers": ["FAIL: test_comments7", "BlackTestCase.test_comments7", "Cannot parse: 11:4:"],
        "dependency_hints": ["click"],
        "v2_8m_status": "frozen_failed_both_from_v2_8l",
    },
    {
        "episode_id": "episode_003",
        "candidate": "black:4",
        "project": "black",
        "bug_id": "4",
        "direct_command": "python -m unittest -q tests.test_black.BlackTestCase.test_beginning_backslash",
        "target_test_file": "tests/test_black.py",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:4",
        "required_markers": ["FAIL: test_beginning_backslash", "BlackTestCase.test_beginning_backslash", "AssertionError"],
        "dependency_hints": ["click"],
    },
    {
        "episode_id": "episode_004",
        "candidate": "black:6",
        "project": "black",
        "bug_id": "6",
        "direct_command": "DISCOVER_FROM_BUGSINPY_RUN_TEST",
        "target_test_file": "tests/test_black.py",
        "failure_signature": "BUGSINPY_DIRECT_TARGET_REPLAY: black:6",
        "required_markers": ["FAIL:", "BlackTestCase", "AssertionError"],
        "dependency_hints": ["click"],
        "replacement_candidate": True,
    },
]


def write_json(path: Path, data: Any) -> None:
    v28k.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    v28k.write_text(path, text)


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
    lines: list[str] = []
    for raw in run_test.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("set "):
            continue
        line = line.replace("python3 ", "python ")
        if line.startswith("pytest ") or line.startswith("python ") or line.startswith("python -m "):
            lines.append(line)
    if not lines:
        return None
    return " && ".join(lines)


def discover_candidate_command(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("direct_command") != "DISCOVER_FROM_BUGSINPY_RUN_TEST":
        return candidate
    discovered = dict(candidate)
    command = read_run_test_command(candidate["project"], candidate["bug_id"])
    bug_info = read_kv_file(base.BUGSINPY_REPO / "projects" / candidate["project"] / "bugs" / candidate["bug_id"] / "bug.info")
    if command:
        discovered["direct_command"] = command
        discovered["direct_command_source"] = "BugsInPy run_test.sh"
    else:
        discovered["direct_command"] = "python -m unittest -q tests.test_black.BlackTestCase"
        discovered["direct_command_source"] = "fallback project-local unittest class command; promotion still requires target failure match"
    if bug_info.get("test_file"):
        discovered["target_test_file"] = bug_info["test_file"]
    method_match = re.search(r"(test_[A-Za-z0-9_]+)", discovered["direct_command"])
    markers = ["FAIL:", "AssertionError"]
    if method_match:
        markers.append(method_match.group(1))
    if "BlackTestCase" in discovered["direct_command"]:
        markers.append("BlackTestCase")
    discovered["required_markers"] = sorted(set(markers))
    write_json(
        ARTIFACT_ROOT / "episode_004_command_discovery.json",
        {
            "candidate": discovered["candidate"],
            "project": discovered["project"],
            "bug_id": discovered["bug_id"],
            "direct_command": discovered["direct_command"],
            "direct_command_source": discovered["direct_command_source"],
            "target_test_file": discovered.get("target_test_file"),
            "required_markers": discovered["required_markers"],
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
        },
    )
    return discovered


def run_episode(candidate: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    return ORIGINAL_RUN_EPISODE(discover_candidate_command(candidate), env)


def proposal_blocked(candidate: dict[str, Any], reason: str, heuristic: str, discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    return v28j.proposal_blocked(candidate, reason, heuristic, discovery, memory_enabled)


def apply_black6_replacement_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    """Outcome-blind replacement patch registry for black:6.

    The rule may only fire when the baseline failure matches one of the
    pre-existing source-only Black heuristics. Otherwise it blocks cleanly
    instead of inventing a post-outcome patch.
    """

    failing_log = discovery.get("failing_log", "")
    test_text = discovery.get("test_info", {}).get("method_text", "")
    if "test_beginning_backslash" in test_text or "'\\n\\nprint(\"hello, world\")\\n'" in failing_log:
        proposal = v28j.apply_black4_patch(workspace, candidate, discovery, memory_enabled)
        proposal["reason"] = "black:6 replacement used pre-registered leading-newline Black heuristic from baseline context"
        proposal["heuristic"] = "black6_outcome_blind_leading_newline_registry_match"
        return proposal
    if "Cannot parse: 11:4:" in failing_log and "test_comments" in test_text:
        proposal = v28l.apply_black8_patch(workspace, candidate, discovery, memory_enabled)
        proposal["reason"] = "black:6 replacement used pre-registered comment/comma Black heuristic from baseline context"
        proposal["heuristic"] = "black6_outcome_blind_comment_comma_registry_match"
        return proposal
    return proposal_blocked(
        candidate,
        "black:6 replacement baseline context did not match a pre-registered source-only repair heuristic",
        "outcome_blind_replacement_no_registry_match",
        discovery,
        memory_enabled,
    )


def propose_patch(workspace: Path, candidate: dict[str, Any], discovery: dict[str, Any], memory_enabled: bool) -> dict[str, Any]:
    if candidate["candidate"] == "black:6":
        return apply_black6_replacement_patch(workspace, candidate, discovery, memory_enabled)
    return ORIGINAL_PROPOSE_PATCH(workspace, candidate, discovery, memory_enabled)


def write_campaign_artifacts() -> None:
    base.write_common_campaign_artifacts()
    pool_hash_source = json.dumps(REPLACEMENT_POOL, sort_keys=True).encode("utf-8")
    import hashlib

    write_json(
        ARTIFACT_ROOT / "campaign_plan.json",
        {
            "campaign_id": "v2_8m_bugsinpy_replacement_third_scoreable",
            "artifact_name": "v2_8m_bugsinpy_replacement_third_scoreable_artifacts",
            "candidate_ids": [item["candidate"] for item in CANDIDATES],
            "preserved_scoreable_candidates": ["youtube-dl:1", "black:4"],
            "frozen_candidate": "black:8",
            "replacement_candidate": "black:6",
            "outcome_blind_replacement_selection": True,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(ARTIFACT_ROOT / "candidate_pool.json", {"count": len(CANDIDATES), "records": CANDIDATES})
    write_json(
        ARTIFACT_ROOT / "replacement_candidate_policy_v2_8m.json",
        {
            "why_black8_frozen": "v2.8l generated and applied black8_compact_comment_comma_guard_v2_8l, but post-repair target validation still failed; black:8 is frozen as failed_both for v2.8m aggregate expansion.",
            "selection_pool_considered": REPLACEMENT_POOL,
            "selection_filters": [
                "pure-Python BugsInPy project",
                "Linux target replay materialization expected from BugsInPy metadata",
                "no prior dependency/runtime blockade where available",
                "no fixed/gold patch exposure for selected candidate",
                "source-only patch possible only through pre-registered heuristic registry",
            ],
            "selected_replacement_candidate": "black:6",
            "evidence_available_at_decision_time": [
                "BugsInPy project and bug id",
                "BugsInPy run_test.sh command if present",
                "buggy checkout",
                "failing log from buggy baseline",
                "traceback and source discovery from buggy source",
            ],
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "replacement_selected_before_repair_outcome": True,
            "preregistered_candidate_pool_sha256": hashlib.sha256(pool_hash_source).hexdigest(),
        },
    )
    write_json(
        ARTIFACT_ROOT / "decision_time_policy.json",
        {
            "allowed_inputs": [
                "BugsInPy bug identifier",
                "buggy checkout",
                "failing command",
                "raw failing log",
                "traceback into buggy source",
                "source discovery from buggy source",
                "pre-registered bounded heuristic family",
            ],
            "forbidden_inputs": [
                "fixed revision",
                "gold patch",
                "future outcome evidence",
                "post-repair success or failure from candidate trials",
                "hidden labels",
                "manual target picking after seeing repair pass",
            ],
        },
    )
    write_json(
        ARTIFACT_ROOT / "anti_leakage_policy.json",
        {
            "no_fixed_or_gold_patch": True,
            "no_future_outcome_evidence": True,
            "no_fixed_state_diagnostic_hints": True,
            "tests_may_be_modified": False,
            "source_only_repair_patch": True,
            "black5_excluded_due_fixed_patch_exposure": True,
        },
    )
    write_json(
        ARTIFACT_ROOT / "source_repair_vs_harness_separation.json",
        {
            "source_repair_candidate_patch_files": ["*_source_only_repair_patch.diff", "*_repair_patch.diff"],
            "tests_may_be_modified_as_repair": False,
            "dependency_runtime_setup_is_not_code_repair": True,
        },
    )
    write_json(
        ARTIFACT_ROOT / "scoreable_episode_expansion_policy.json",
        {
            "scoreable_requires_pre_repair_target_failure_reproduced": True,
            "scoreable_requires_repair_candidate_generated": True,
            "scoreable_requires_source_only_patch": True,
            "scoreable_requires_patch_applies": True,
            "scoreable_requires_target_post_repair_validation_executes": True,
            "scoreable_requires_target_passes_in_at_least_one_arm": True,
            "classification_vocabulary": CLASSIFICATION_VOCABULARY,
        },
    )
    write_json(
        ARTIFACT_ROOT / "bounded_repair_proposer_summary.json",
        {
            "bounded_source_only_repair_proposer_enabled": True,
            "black8_frozen_as_failed_both": True,
            "replacement_candidate": "black:6",
            "replacement_patch_policy": "pre-registered source-only Black heuristic registry, otherwise block",
        },
    )
    write_json(
        ARTIFACT_ROOT / "package_verification.json",
        {
            "artifact_package": "v2_8m_bugsinpy_replacement_third_scoreable_artifacts",
            "generated_by": "v2.8m Linux runner",
            "large_tar_snapshots_expected": True,
            "full_scoring_allowed": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "artifact_sha256_verification.json",
        {
            "status": "generated_inside_workflow_not_yet_zipped",
            "zip_sha256_available_after_download": False,
            "internal_sha256_manifest_written_at_end": True,
        },
    )


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


def write_final_campaign_files(results: list[dict[str, Any]], aggregate: str) -> None:
    ORIGINAL_WRITE_FINAL_CAMPAIGN_FILES(results, aggregate)
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
    write_json(ARTIFACT_ROOT / "decision_report.json", {"records": records, "classification_vocabulary": CLASSIFICATION_VOCABULARY})
    write_json(
        ARTIFACT_ROOT / "audit.json",
        {
            "artifact_provenance": "generated by v2.8m Linux runner",
            "fixed_or_gold_patch_used_at_decision_time": False,
            "future_outcome_evidence_used_at_decision_time": False,
            "tests_modified_as_repair": False,
            "source_only_patch_separation_enforced": True,
            "black8_frozen_as_failed_both": True,
            "replacement_candidate": "black:6",
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
    rows = "\n".join(
        f"| {item['episode_id']} | {item['candidate']} | {item['classification']} | {str(item['scoreable']).lower()} | {str(item['memory_enabled_outperformed_no_memory']).lower()} |"
        for item in records
    )
    write_text(
        ARTIFACT_ROOT / "campaign_summary.md",
        "# v2.8m BugsInPy Replacement Third Scoreable Episode\n\n"
        f"Aggregate result: `{aggregate}`.\n\n"
        f"- Executed BugsInPy episodes: {len(results)}.\n"
        f"- Scoreable episodes: {len(scoreable)}.\n"
        f"- Positive memory-only episodes: {len(positives)}.\n"
        "- black:8 status: frozen as `failed_both` from v2.8l.\n"
        "- Replacement candidate: `black:6`.\n"
        "- Full scoring: NOT_RUN / disallowed.\n"
        "- Memory lift: not demonstrated unless aggregate criteria are met.\n"
        "- Self-maintaining software: not demonstrated.\n\n"
        "| Episode | Candidate | Classification | Scoreable | Memory outperformed |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{rows}\n",
    )


def main() -> int:
    for module in (v28l, v28k, v28j, v28i, v28g, base):
        module.ARTIFACT_ROOT = ARTIFACT_ROOT
        module.RUNTIME_ROOT = RUNTIME_ROOT
    base.BUGSINPY_REPO = (RUNTIME_ROOT / "BugsInPy").resolve()
    base.CANDIDATES = CANDIDATES
    v28g.run_episode = run_episode
    v28g.aggregate_result = aggregate_result
    v28j.aggregate_result = aggregate_result
    v28k.aggregate_result = aggregate_result
    v28l.aggregate_result = aggregate_result
    v28k.propose_patch = propose_patch
    v28l.propose_patch = propose_patch
    v28l.write_campaign_artifacts = write_campaign_artifacts
    v28l.write_final_campaign_files = write_final_campaign_files
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    return v28l.main()


if __name__ == "__main__":
    raise SystemExit(main())
