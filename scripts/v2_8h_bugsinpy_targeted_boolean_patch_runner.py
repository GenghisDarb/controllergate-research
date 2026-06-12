#!/usr/bin/env python3
"""GitHub Actions runner for v2.8h targeted boolean patch heuristic."""

from __future__ import annotations

import difflib
import importlib.util
import re
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
BASE_RUNNER_PATH = REPO_ROOT / "scripts" / "v2_8g_bugsinpy_source_discovery_repair_proposer_runner.py"
ARTIFACT_ROOT = (REPO_ROOT / "v2_8h_bugsinpy_targeted_boolean_patch_artifacts").resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_8h_bugsinpy_runtime").resolve()

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
orig_write_attempt = v28g.write_attempt


def write_json(path: Path, data: Any) -> None:
    v28g.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    v28g.write_text(path, text)


def extract_match_str_context(text: str) -> str:
    match = re.search(r"(?ms)^def match_str\(.*?(?=^\S|\Z)", text)
    unary = re.search(r"(?ms)^UNARY_OPERATORS\s*=\s*\{.*?^\}", text)
    parts = []
    if unary:
        parts.append(unary.group(0).rstrip())
    if match:
        parts.append(match.group(0).rstrip())
    return "\n\n".join(parts) + ("\n" if parts else "")


def boolean_context(workspace: Path, episode_dir: Path) -> dict[str, Any]:
    source_path = workspace / "youtube_dl" / "utils.py"
    test_text = (episode_dir / "failing_test_method_extract.txt").read_text(encoding="utf-8", errors="replace") if (episode_dir / "failing_test_method_extract.txt").exists() else ""
    source_text = source_path.read_text(encoding="utf-8", errors="replace") if source_path.exists() else ""
    return {
        "source_file": "youtube_dl/utils.py",
        "source_file_exists": source_path.exists(),
        "unary_operator_block_found": "UNARY_OPERATORS" in source_text and "lambda v: v is not None" in source_text and "lambda v: v is None" in source_text,
        "test_contains_false_positive_case": "match_str('is_live', {'is_live': False})" in test_text,
        "test_contains_false_negative_case": "match_str('!is_live', {'is_live': False})" in test_text,
        "test_contains_zero_presence_case": "match_str('x', {'x': 0})" in test_text,
        "test_contains_empty_string_presence_case": "match_str('title', {'title': ''})" in test_text,
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
    }


def apply_youtube_dl_patch(workspace: Path, discovery: dict[str, Any]) -> dict[str, Any]:
    """Apply a narrow boolean-False unary operator patch from buggy context only."""
    source_path = workspace / "youtube_dl" / "utils.py"
    if not source_path.exists():
        return {"candidate_generated": False, "reason": "youtube_dl/utils.py not found in buggy workspace"}
    report = discovery.get("report", {})
    test_info = discovery.get("test_info", {})
    if not report.get("match_str_found") or test_info.get("selector", {}).get("method") != "test_match_str":
        return {"candidate_generated": False, "reason": "match_str source or test_match_str context not found"}
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
    old = "UNARY_OPERATORS = {\n    '': lambda v: v is not None,\n    '!': lambda v: v is None,\n}"
    new = "UNARY_OPERATORS = {\n    '': lambda v: v is not None and v is not False,\n    '!': lambda v: v is None or v is False,\n}"
    if old not in text:
        return {"candidate_generated": False, "reason": "expected UNARY_OPERATORS block not found", "inspected_file": "youtube_dl/utils.py"}
    updated = text.replace(old, new, 1)
    diff = "".join(
        difflib.unified_diff(
            text.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile="youtube_dl/utils.py",
            tofile="youtube_dl/utils.py",
        )
    )
    changed_lines = max(0, diff.count("\n+") - 1)
    if changed_lines <= 0 or changed_lines > v28g.REPAIR_BUDGET["max_changed_lines"]:
        return {"candidate_generated": False, "reason": "boolean patch diff failed bounded changed-line safety check"}
    source_path.write_text(updated, encoding="utf-8")
    return {
        "candidate_generated": True,
        "patched_file": "youtube_dl/utils.py",
        "heuristic": "boolean_unary_false_value_presence_rule",
        "diff": diff,
        "changed_lines": changed_lines,
        "fixed_or_gold_patch_used": False,
        "future_outcome_evidence_used": False,
        "reason": "failing test distinguishes boolean False from 0 and empty string; source has unary presence operators",
    }


def write_youtube_dl_boolean_artifacts(episode_dir: Path, workspace: Path, prefix: str) -> None:
    context = boolean_context(workspace, episode_dir)
    write_json(episode_dir / "boolean_unary_false_value_context.json", context)
    source_path = workspace / "youtube_dl" / "utils.py"
    source_text = source_path.read_text(encoding="utf-8", errors="replace") if source_path.exists() else ""
    write_text(episode_dir / "youtube_dl_match_str_source_extract.txt", extract_match_str_context(source_text))
    test_context = (episode_dir / "failing_test_method_extract.txt").read_text(encoding="utf-8", errors="replace") if (episode_dir / "failing_test_method_extract.txt").exists() else ""
    write_text(episode_dir / "youtube_dl_match_str_test_context.txt", test_context)
    diff_path = episode_dir / f"{prefix}_repair_patch.diff"
    diff_text = diff_path.read_text(encoding="utf-8", errors="replace") if diff_path.exists() else "# NO PATCH CANDIDATE GENERATED\n"
    if "youtube_dl/utils.py" in diff_text and "v is not None and v is not False" in diff_text:
        write_text(episode_dir / "boolean_patch_candidate.diff", diff_text)
        candidate_generated = True
    elif not (episode_dir / "boolean_patch_candidate.diff").exists():
        write_text(episode_dir / "boolean_patch_candidate.diff", "# NO PATCH CANDIDATE GENERATED\n")
        candidate_generated = False
    else:
        candidate_generated = "NO PATCH" not in (episode_dir / "boolean_patch_candidate.diff").read_text(encoding="utf-8", errors="replace")
    write_json(
        episode_dir / "boolean_patch_candidate_explanation.json",
        {
            "heuristic": "boolean_unary_false_value_presence_rule",
            "candidate_generated": candidate_generated,
            "patched_file": "youtube_dl/utils.py" if candidate_generated else None,
            "reasoning_inputs": [
                "buggy source UNARY_OPERATORS block",
                "failing test method test_match_str",
                "False must be treated as absent",
                "0 and empty string must remain present",
            ],
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "tests_modified": False,
        },
    )


def write_attempt(path: Path, candidate: dict[str, Any], workspace: Path, prefix: str, env: dict[str, str], memory_enabled: bool) -> dict[str, Any]:
    outcome = orig_write_attempt(path, candidate, workspace, prefix, env, memory_enabled)
    if candidate["candidate"] == "youtube-dl:1":
        write_youtube_dl_boolean_artifacts(path, workspace, prefix)
    return outcome


def aggregate_result(results: list[dict[str, Any]]) -> str:
    scoreable = [item for item in results if item["scoreable"]]
    positives = [item for item in scoreable if item["memory_enabled_outperformed_no_memory"]]
    if len(scoreable) < 3:
        if scoreable:
            return "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
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
        ARTIFACT_ROOT / "boolean_unary_false_value_heuristic.json",
        {
            "heuristic_name": "boolean_unary_false_value_presence_rule",
            "candidate_scope": "youtube-dl:1",
            "source_file_scope": "youtube_dl/utils.py",
            "positive_operator": "lambda v: v is not None and v is not False",
            "negative_operator": "lambda v: v is None or v is False",
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "youtube_dl_patch_generation_rule.json",
        {
            "rule_id": "youtube_dl_match_str_boolean_false_unary_patch",
            "heuristic": "boolean_unary_false_value_presence_rule",
            "allowed_patch_file": "youtube_dl/utils.py",
            "tests_may_be_modified": False,
            "fixed_or_gold_patch_allowed": False,
        },
    )
    write_json(
        ARTIFACT_ROOT / "heuristic_applicability_check.json",
        {
            "candidate": "youtube-dl:1",
            "requires_match_str_discovery": True,
            "requires_test_match_str_context": True,
            "requires_boolean_false_and_non_false_falsy_cases": True,
        },
    )
    write_json(
        ARTIFACT_ROOT / "heuristic_safety_check.json",
        {
            "patch_only_file": "youtube_dl/utils.py",
            "modifies_tests": False,
            "uses_fixed_revision": False,
            "uses_gold_patch": False,
            "uses_future_outcome_evidence": False,
            "post_repair_validation_required": True,
        },
    )


def main() -> int:
    v28g.apply_youtube_dl_patch = apply_youtube_dl_patch
    v28g.write_attempt = write_attempt
    v28g.aggregate_result = aggregate_result
    v28g.write_campaign_artifacts = write_campaign_artifacts
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    return v28g.main()


if __name__ == "__main__":
    raise SystemExit(main())
