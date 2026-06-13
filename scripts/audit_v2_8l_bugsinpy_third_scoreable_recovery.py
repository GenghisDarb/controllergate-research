#!/usr/bin/env python3
"""Audit v2.8l BugsInPy third scoreable recovery."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8l_bugsinpy_third_scoreable_recovery"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8l_bugsinpy_third_scoreable_recovery.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8l_bugsinpy_third_scoreable_recovery_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8l_prepare_bugsinpy_third_scoreable_recovery.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V28K_RESULTS = REPO_ROOT / "outputs" / "v2_8k_bugsinpy_third_scoreable_recovery" / "campaign_results.json"

REQUIRED = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "bounded_repair_proposer_summary.json",
    "candidate_pool.json",
    "candidate_source_integrity_check.json",
    "decision_time_policy.json",
    "anti_leakage_policy.json",
    "black_or_replacement_candidate_policy.json",
    "source_discovery_summary.json",
    "pre_repair_replay_gate_summary.json",
    "workspace_equivalence_summary.json",
    "audit.json",
    "SHA256SUMS.txt",
]

EPISODES = {
    "episode_001": "youtube-dl:1",
    "episode_002": "black:8",
    "episode_003": "black:4",
}


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
            errors.append(f"missing v2.8l implementation file: {path}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8l output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.8l artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8l artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))

    plan, plan_errors = load_json(OUTPUT_DIR / "campaign_plan.json")
    pool, pool_errors = load_json(OUTPUT_DIR / "candidate_pool.json")
    diagnosis, diagnosis_errors = load_json(OUTPUT_DIR / "v2_8k_black8_block_diagnosis.json")
    replacement_policy, replacement_errors = load_json(OUTPUT_DIR / "black_or_replacement_candidate_policy.json")
    leakage, leakage_errors = load_json(OUTPUT_DIR / "anti_leakage_policy.json")
    decision_policy, decision_policy_errors = load_json(OUTPUT_DIR / "decision_time_policy.json")
    campaign, campaign_errors = load_json(OUTPUT_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    decision, decision_errors = load_json(OUTPUT_DIR / "decision_report.json")
    v28k, v28k_errors = load_json(V28K_RESULTS)
    errors.extend(
        plan_errors
        + pool_errors
        + diagnosis_errors
        + replacement_errors
        + leakage_errors
        + decision_policy_errors
        + campaign_errors
        + aggregate_errors
        + decision_errors
        + v28k_errors
    )

    if plan.get("campaign_id") != "v2_8l_bugsinpy_third_scoreable_recovery":
        errors.append("v2.8l campaign_plan has wrong campaign_id")
    if plan.get("targeted_candidate") != "black:8":
        errors.append("v2.8l must target black:8 unless replacement policy is explicitly activated")
    if plan.get("full_scoring_allowed") is not False or plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8l must keep full scoring NOT_RUN / disallowed")
    if plan.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8l must not claim self-maintaining software")
    candidates = [item.get("candidate") for item in pool.get("records", [])]
    if candidates != ["youtube-dl:1", "black:8", "black:4"]:
        errors.append(f"v2.8l candidate pool mismatch: {candidates}")
    if v28k.get("scoreable_episode_count") != 2 or v28k.get("positive_memory_episode_count") != 0:
        errors.append("v2.8l must preserve official v2.8k two-scoreable, zero-positive result")
    if diagnosis.get("exact_blocker") != "source-only safety budget rejected candidate":
        errors.append("v2.8l must diagnose v2.8k black:8 as safety-budget blocked")
    if diagnosis.get("v2_8k_changed_lines") != 16 or diagnosis.get("max_changed_lines") != 12:
        errors.append("v2.8l must record exact v2.8k black:8 changed-line blocker")
    if replacement_policy.get("primary_candidate") != "black:8" or replacement_policy.get("replacement_candidate_used") is not False:
        errors.append("v2.8l must keep black:8 as primary and not silently use replacement")
    if replacement_policy.get("source_only_repair_patch") is not True or replacement_policy.get("tests_may_be_modified") is not False:
        errors.append("v2.8l replacement policy must enforce source-only/no-test-edit boundaries")
    for key in ["no_fixed_or_gold_patch", "no_future_outcome_evidence", "no_fixed_state_diagnostic_hints"]:
        if leakage.get(key) is not True:
            errors.append(f"v2.8l anti-leakage policy missing {key}")
    if decision_policy.get("test_edits_forbidden") is not True or decision_policy.get("source_only_repair_required") is not True:
        errors.append("v2.8l decision-time policy must forbid test edits and require source-only repair")

    workflow_executed = campaign.get("workflow_executed") is True
    if not workflow_executed:
        if campaign.get("aggregate_result") != "blocked_pending_v2_8l_third_scoreable_recovery_artifact":
            errors.append("local v2.8l checkpoint must be blocked pending Linux artifact")
        if campaign.get("scoreable_episode_count") != 0:
            errors.append("local v2.8l checkpoint must not claim scoreable episodes")
    else:
        if campaign.get("executed_episode_count", 0) < 3:
            errors.append("executed v2.8l must run at least three BugsInPy episodes")
        if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
            errors.append("executed v2.8l must keep full scoring NOT_RUN / disallowed")
        if campaign.get("self_maintaining_software_demonstrated") is not False:
            errors.append("executed v2.8l must not claim self-maintaining software")
        if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True and campaign.get("positive_memory_episode_count", 0) < 2:
            errors.append("v2.8l cannot claim memory lift without at least two positive memory episodes")
        records = {record.get("candidate"): record for record in decision.get("records", [])}
        for candidate in ["youtube-dl:1", "black:4"]:
            if records.get(candidate, {}).get("scoreable") is not True:
                errors.append(f"v2.8l must preserve {candidate} as scoreable reference episode")
        for episode, candidate in EPISODES.items():
            episode_dir = OUTPUT_DIR / episode
            if not episode_dir.exists():
                errors.append(f"executed v2.8l missing episode directory: {episode_dir}")
                continue
            for required in [
                "episode_metadata.json",
                "failing_log_raw.txt",
                "source_discovery_report.json",
                "repair_materialization_separation.json",
                "proof_obligations_ledger.json",
                "limited_scoring_result.json",
            ]:
                if not (episode_dir / required).exists():
                    errors.append(f"executed v2.8l {candidate} missing {required}")

    if RUNNER.exists():
        runner_text = RUNNER.read_text(encoding="utf-8")
        for snippet in [
            "black8_compact_comment_comma_guard_v2_8l",
            "v2_8k_black8_block_diagnosis",
            "black_or_replacement_candidate_policy",
            "source_only_repair_patch",
            "tests_may_be_modified",
            "no_fixed_or_gold_patch",
            "no_future_outcome_evidence",
        ]:
            if snippet not in runner_text:
                errors.append(f"v2.8l runner missing required snippet: {snippet}")
    errors.extend(require_text(SUMMARY, ["v2.8l BugsInPy Third Scoreable Episode Recovery", "Full scoring: NOT_RUN / disallowed", "Memory lift: not demonstrated", "Self-maintaining software: not demonstrated"]))

    if errors:
        print("v2.8l BugsInPy third scoreable recovery audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8l BugsInPy third scoreable recovery audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
