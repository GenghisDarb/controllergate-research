#!/usr/bin/env python3
"""Audit v2.8m BugsInPy replacement third scoreable checkpoint/artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8m_bugsinpy_replacement_third_scoreable"
V28L_OUTPUT = REPO_ROOT / "outputs" / "v2_8l_bugsinpy_third_scoreable_recovery"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8m_bugsinpy_replacement_third_scoreable.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8m_bugsinpy_replacement_third_scoreable_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8m_prepare_bugsinpy_replacement_third_scoreable.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "bounded_repair_proposer_summary.json",
    "candidate_pool.json",
    "replacement_candidate_policy_v2_8m.json",
    "candidate_source_integrity_check.json",
    "decision_time_policy.json",
    "anti_leakage_policy.json",
    "source_discovery_summary.json",
    "pre_repair_replay_gate_summary.json",
    "workspace_equivalence_summary.json",
    "source_repair_vs_harness_separation.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE = [
    "episode_metadata.json",
    "failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "source_discovery_report.json",
    "ranked_candidate_source_files.json",
    "candidate_function_extracts.json",
    "repair_heuristic_selection.json",
    "no_memory_repair_candidate_generation.json",
    "memory_enabled_repair_candidate_generation.json",
    "no_memory_source_only_repair_patch.diff",
    "memory_enabled_source_only_repair_patch.diff",
    "patch_candidate_safety_check.json",
    "no_memory_patch_application_result.json",
    "memory_enabled_patch_application_result.json",
    "no_memory_post_repair_command.txt",
    "memory_enabled_post_repair_command.txt",
    "no_memory_post_repair_log_raw.txt",
    "memory_enabled_post_repair_log_raw.txt",
    "post_repair_comparison.json",
    "limited_scoring_result.json",
    "decision_time_input_manifest.json",
    "decision_time_outcome_overlap_check.json",
    "label_blindness_check.json",
    "gold_patch_exclusion_check.json",
    "corruption_check_result.json",
    "wrapper_contamination_check.json",
    "repair_materialization_separation.json",
    "proof_obligations_ledger.json",
]

CLASSIFICATION_VOCABULARY = {
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "failed_both",
    "inconclusive_equal_performance",
    "no_memory_only",
    "positive_memory_only",
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


def text_contains(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing {snippet!r}" for snippet in snippets if snippet not in text]


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.8m implementation file: {path}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8m output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED_TOP_LEVEL:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.8m artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8m artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))

    campaign, e = load_json(OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    aggregate, e = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(e)
    decision, e = load_json(OUTPUT_DIR / "decision_report.json")
    errors.extend(e)
    pool, e = load_json(OUTPUT_DIR / "candidate_pool.json")
    errors.extend(e)
    policy, e = load_json(OUTPUT_DIR / "replacement_candidate_policy_v2_8m.json")
    errors.extend(e)
    audit, e = load_json(OUTPUT_DIR / "audit.json")
    errors.extend(e)
    leakage, e = load_json(OUTPUT_DIR / "anti_leakage_policy.json")
    errors.extend(e)
    v28l_package, e = load_json(V28L_OUTPUT / "artifact_sha256_verification.json")
    errors.extend(e)
    v28l_results, e = load_json(V28L_OUTPUT / "campaign_results.json")
    errors.extend(e)

    candidates = [item.get("candidate") for item in pool.get("records", [])]
    expected_candidates = ["youtube-dl:1", "black:8", "black:4", "black:6"]
    if candidates != expected_candidates:
        errors.append(f"v2.8m candidate pool mismatch: {candidates}")
    if policy.get("selected_replacement_candidate") != "black:6":
        errors.append("v2.8m replacement candidate must be black:6")
    if policy.get("replacement_candidate_selected_before_repair_outcome") is not True:
        errors.append("v2.8m replacement candidate must be selected before repair outcome")
    if policy.get("gold_fixed_or_future_evidence_used") is not False:
        errors.append("v2.8m replacement policy must not use gold/fixed/future evidence")
    pool_items = policy.get("selection_pool_considered", [])
    black5 = [item for item in pool_items if item.get("candidate") == "black:5"]
    if not black5 or black5[0].get("status") != "excluded_fixed_patch_exposure":
        errors.append("v2.8m must exclude black:5 after fixed patch exposure")
    if leakage.get("black5_excluded_due_fixed_patch_exposure") is not True:
        errors.append("v2.8m anti-leakage policy must record black:5 fixed-patch exclusion")

    if v28l_package.get("zip_sha256") != "d1a7792daf2b65dc589fa32dcd0854401bd775c67d2e5eaa7493c39e5d3eeafe":
        errors.append("v2.8m must preserve official v2.8l artifact SHA256")
    if v28l_package.get("internal_sha256_missing") != 0 or v28l_package.get("internal_sha256_failures") != 0:
        errors.append("v2.8l ingested artifact SHA256SUMS must verify with 0 missing/failures")
    if v28l_results.get("executed_episode_count") != 3 or v28l_results.get("scoreable_episode_count") != 2:
        errors.append("v2.8m must preserve official v2.8l 3-executed, 2-scoreable result")
    if v28l_results.get("positive_memory_episode_count") != 0:
        errors.append("v2.8m must preserve official v2.8l zero-positive-memory result")

    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8m must keep full scoring NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8m must not claim self-maintaining software")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True and aggregate.get("positive_memory_episode_count", 0) < 2:
        errors.append("v2.8m cannot claim memory lift without at least two positive memory episodes")
    if aggregate.get("full_scoring_allowed") is not False or aggregate.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8m aggregate must keep full scoring disallowed")

    workflow_executed = campaign.get("workflow_executed") is True
    if not workflow_executed:
        if campaign.get("aggregate_result") != "blocked_pending_v2_8m_replacement_artifact":
            errors.append("local v2.8m checkpoint must be blocked pending Linux artifact")
        if campaign.get("scoreable_episode_count") != 0:
            errors.append("local v2.8m checkpoint must not claim scoreable episodes")
    else:
        records = decision.get("records", [])
        if len(records) < 4:
            errors.append("executed v2.8m must include at least four episode records")
        by_candidate = {record.get("candidate"): record for record in records}
        for candidate in ["youtube-dl:1", "black:4"]:
            if by_candidate.get(candidate, {}).get("scoreable") is not True:
                errors.append(f"executed v2.8m must preserve {candidate} as scoreable")
        if by_candidate.get("black:8", {}).get("classification") != "failed_both":
            errors.append("executed v2.8m must freeze black:8 as failed_both")
        if by_candidate.get("black:6", {}).get("candidate") != "black:6":
            errors.append("executed v2.8m must include black:6 replacement episode")
        for record in records:
            classification = record.get("classification")
            if classification not in CLASSIFICATION_VOCABULARY:
                errors.append(f"unexpected v2.8m classification: {classification}")
        for episode in ["episode_001", "episode_002", "episode_003", "episode_004"]:
            directory = OUTPUT_DIR / episode
            if not directory.exists():
                errors.append(f"executed v2.8m missing {episode}")
                continue
            for name in REQUIRED_EPISODE:
                if not (directory / name).exists():
                    errors.append(f"executed v2.8m {episode} missing {name}")
            errors.extend(verify_manifest(directory))

    if audit.get("artifact_provenance") not in {"prepared by v2.8m local checkpoint", "generated by v2.8m Linux runner"}:
        errors.append("v2.8m audit provenance must be v2.8m-accurate")
    runner_text = RUNNER.read_text(encoding="utf-8", errors="replace") if RUNNER.exists() else ""
    for snippet in [
        "replacement_candidate_policy_v2_8m",
        "black:6",
        "black:5",
        "excluded_fixed_patch_exposure",
        "artifact_provenance",
        "generated by v2.8m Linux runner",
    ]:
        if snippet not in runner_text:
            errors.append(f"v2.8m runner missing required snippet: {snippet}")
    errors.extend(text_contains(SUMMARY, ["v2.8m BugsInPy Replacement Third Scoreable Episode", "Memory lift: not demonstrated", "Self-maintaining software: not demonstrated"]))

    if errors:
        print("v2.8m BugsInPy replacement third scoreable audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8m BugsInPy replacement third scoreable audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
