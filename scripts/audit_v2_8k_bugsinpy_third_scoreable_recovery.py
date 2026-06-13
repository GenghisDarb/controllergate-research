#!/usr/bin/env python3
"""Audit v2.8k BugsInPy third scoreable episode recovery."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8k_bugsinpy_third_scoreable_recovery"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8k_bugsinpy_third_scoreable_recovery.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8k_bugsinpy_third_scoreable_recovery_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8k_prepare_bugsinpy_third_scoreable_recovery.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V28J_RESULTS = REPO_ROOT / "outputs" / "v2_8j_bugsinpy_scoreable_episode_expansion" / "campaign_results.json"

REQUIRED = [
    "campaign_plan.json",
    "candidate_pool.json",
    "previous_v2_8j_official_result.json",
    "third_scoreable_recovery_policy.json",
    "anti_leakage_policy.json",
    "campaign_results.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "github_actions_usage_instructions.md",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return {}, [f"{path}: expected JSON object"]
    return data, []


def verify_manifest(directory: Path) -> list[str]:
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.exists():
        return [f"missing SHA256SUMS.txt in {directory}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"{manifest}:{line_no}: expected '<sha256>  <path>'")
            continue
        expected, rel = parts
        seen.add(rel)
        path = directory / rel
        if not path.exists():
            errors.append(f"{manifest}:{line_no}: missing artifact {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{manifest}:{line_no}: hash mismatch for {rel}")
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rel = str(path.relative_to(directory)).replace("\\", "/")
            if rel not in seen:
                errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def require_text(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing required text {snippet!r}" for snippet in snippets if snippet not in text]


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.8k implementation file: {path}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8k output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.8k artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8k artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))

    plan, plan_errors = load_json(OUTPUT_DIR / "campaign_plan.json")
    pool, pool_errors = load_json(OUTPUT_DIR / "candidate_pool.json")
    prior, prior_errors = load_json(OUTPUT_DIR / "previous_v2_8j_official_result.json")
    recovery, recovery_errors = load_json(OUTPUT_DIR / "third_scoreable_recovery_policy.json")
    leakage, leakage_errors = load_json(OUTPUT_DIR / "anti_leakage_policy.json")
    campaign, campaign_errors = load_json(OUTPUT_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    v28j, v28j_errors = load_json(V28J_RESULTS)
    errors.extend(plan_errors + pool_errors + prior_errors + recovery_errors + leakage_errors + campaign_errors + aggregate_errors + v28j_errors)

    if plan.get("campaign_id") != "v2_8k_bugsinpy_third_scoreable_recovery":
        errors.append("v2.8k campaign_plan has wrong campaign_id")
    if plan.get("targeted_candidate") != "black:8":
        errors.append("v2.8k must target black:8 as the missing scoreable recovery candidate")
    if plan.get("full_scoring_allowed") is not False or plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8k must keep full scoring NOT_RUN / disallowed")
    if plan.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8k must not claim self-maintaining software")
    candidates = [item.get("candidate") for item in pool.get("records", [])]
    if candidates != ["youtube-dl:1", "black:8", "black:4"]:
        errors.append(f"v2.8k candidate pool mismatch: {candidates}")
    if prior.get("scoreable_episode_count") != 2 or prior.get("positive_memory_episode_count") != 0:
        errors.append("v2.8k must preserve official v2.8j two-scoreable, zero-positive result")
    if v28j.get("scoreable_episode_count") != 2 or v28j.get("positive_memory_episode_count") != 0:
        errors.append("v2.8k regression must preserve ingested v2.8j official result")
    if recovery.get("recovery_heuristic") != "black8_comment_comma_relocation_guard_v2_8k":
        errors.append("v2.8k recovery policy must name the black8 comma relocation guard")
    if recovery.get("source_only_repair_patch") is not True or recovery.get("tests_may_be_modified") is not False:
        errors.append("v2.8k recovery must stay source-only and forbid test edits")
    for key in ["no_fixed_or_gold_patch", "no_future_outcome_evidence", "no_fixed_state_diagnostic_hints"]:
        if leakage.get(key) is not True:
            errors.append(f"v2.8k anti-leakage policy missing {key}")

    workflow_executed = campaign.get("workflow_executed") is True
    if not workflow_executed:
        if campaign.get("aggregate_result") != "blocked_pending_v2_8k_third_scoreable_recovery_artifact":
            errors.append("local v2.8k checkpoint must be blocked pending Linux artifact")
        if campaign.get("scoreable_episode_count") != 0:
            errors.append("local v2.8k checkpoint must not claim scoreable episodes")
    else:
        if campaign.get("executed_episode_count") != 3:
            errors.append("executed v2.8k must run exactly three promoted BugsInPy episodes")
        if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
            errors.append("executed v2.8k must keep full scoring NOT_RUN / disallowed")
        if campaign.get("self_maintaining_software_demonstrated") is not False:
            errors.append("executed v2.8k must not claim self-maintaining software")
        if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True and campaign.get("positive_memory_episode_count", 0) < 2:
            errors.append("v2.8k cannot claim memory lift without at least two positive memory episodes")

    if RUNNER.exists():
        runner_text = RUNNER.read_text(encoding="utf-8")
        for snippet in [
            "black8_comment_comma_relocation_guard_v2_8k",
            "no_fixed_or_gold_patch",
            "no_future_outcome_evidence",
            "source_only_repair_patch",
            "tests_may_be_modified",
            "previous_v2_8j_official_result",
            "third_scoreable_recovery_policy",
        ]:
            if snippet not in runner_text:
                errors.append(f"v2.8k runner missing required snippet: {snippet}")
    errors.extend(require_text(SUMMARY, ["v2.8k BugsInPy Third Scoreable Episode Recovery", "Full scoring: NOT_RUN / disallowed", "Memory lift: not demonstrated", "Self-maintaining software: not demonstrated"]))

    if errors:
        print("v2.8k BugsInPy third scoreable recovery audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8k BugsInPy third scoreable recovery audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
