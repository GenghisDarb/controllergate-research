#!/usr/bin/env python3
"""Audit v2.8o broad BugsInPy preflight-harvest checkpoint/artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8o_bugsinpy_broad_preflight_harvest"
V28N_OUTPUT = REPO_ROOT / "outputs" / "v2_8n_bugsinpy_replacement_preflight_third_scoreable"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8o_bugsinpy_broad_preflight_harvest.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8o_bugsinpy_broad_preflight_harvest_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8o_prepare_bugsinpy_broad_preflight_harvest.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED_V28N_ZIP_SHA256 = "31ef78b0f9ea422ac56338dd4369966874b89d9f5fe85d7ad63ea922d9280ca6"

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

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "bounded_repair_proposer_summary.json",
    "candidate_pool.json",
    "broad_candidate_preflight_registry_v2_8o.json",
    "replacement_candidate_policy_v2_8o.json",
    "replacement_candidate_preflight_summary.json",
    "fixture_dependency_preflight_summary.json",
    "candidate_ranking_policy_v2_8o.json",
    "candidate_source_integrity_check.json",
    "decision_time_policy.json",
    "anti_leakage_policy.json",
    "source_discovery_summary.json",
    "pre_repair_replay_gate_summary.json",
    "workspace_equivalence_summary.json",
    "source_repair_vs_harness_separation.json",
    "classification_vocabulary_check.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

REPAIR_ATTEMPT_ARTIFACTS = [
    "episode_metadata.json",
    "candidate_preflight_result.json",
    "fixture_dependency_preflight_result.json",
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


def text_contains(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing {snippet!r}" for snippet in snippets if snippet not in text]


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.8o implementation file: {path}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8o output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED_TOP_LEVEL:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.8o artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8o artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))

    campaign, e = load_json(OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    aggregate, e = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(e)
    decision, e = load_json(OUTPUT_DIR / "decision_report.json")
    errors.extend(e)
    pool, e = load_json(OUTPUT_DIR / "candidate_pool.json")
    errors.extend(e)
    registry, e = load_json(OUTPUT_DIR / "broad_candidate_preflight_registry_v2_8o.json")
    errors.extend(e)
    replacement_policy, e = load_json(OUTPUT_DIR / "replacement_candidate_policy_v2_8o.json")
    errors.extend(e)
    ranking_policy, e = load_json(OUTPUT_DIR / "candidate_ranking_policy_v2_8o.json")
    errors.extend(e)
    fixture_summary, e = load_json(OUTPUT_DIR / "fixture_dependency_preflight_summary.json")
    errors.extend(e)
    vocab, e = load_json(OUTPUT_DIR / "classification_vocabulary_check.json")
    errors.extend(e)
    v28n_package, e = load_json(V28N_OUTPUT / "artifact_sha256_verification.json")
    errors.extend(e)
    v28n_results, e = load_json(V28N_OUTPUT / "campaign_results.json")
    errors.extend(e)
    v28n_decision, e = load_json(V28N_OUTPUT / "decision_report.json")
    errors.extend(e)

    if v28n_package.get("zip_sha256") != EXPECTED_V28N_ZIP_SHA256:
        errors.append("v2.8o must preserve official v2.8n artifact SHA256")
    if v28n_package.get("internal_sha256_checked") != 392:
        errors.append("v2.8n internal SHA256SUMS checked count must be 392")
    if v28n_package.get("internal_sha256_missing") != 0 or v28n_package.get("internal_sha256_failures") != 0:
        errors.append("v2.8n internal SHA256SUMS must verify with 0 missing/failures")
    if v28n_results.get("executed_episode_count") != 5 or v28n_results.get("scoreable_episode_count") != 2:
        errors.append("v2.8o must preserve official v2.8n 5-executed, 2-scoreable result")
    if v28n_results.get("positive_memory_episode_count") != 0:
        errors.append("v2.8o must preserve official v2.8n zero-positive-memory result")
    v28n_records = {record.get("candidate"): record for record in v28n_decision.get("records", [])}
    for candidate in ["youtube-dl:1", "black:4"]:
        if v28n_records.get(candidate, {}).get("scoreable") is not True:
            errors.append(f"v2.8o must preserve v2.8n {candidate} scoreable reference")
    if v28n_records.get("black:6", {}).get("classification") != "blocked_replay_or_materialization_failure":
        errors.append("v2.8o must preserve black:6 as replay/materialization blocked")
    if v28n_records.get("black:7", {}).get("classification") != "blocked_no_safe_patch_candidate_generated":
        errors.append("v2.8o must preserve black:7 as non-scoreable no-safe-patch")

    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8o must keep full scoring NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8o must not claim self-maintaining software")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True and campaign.get("positive_memory_episode_count", 0) < 2:
        errors.append("v2.8o cannot claim memory lift without at least two positive memory episodes")

    if replacement_policy.get("broad_preflight_before_repair") is not True:
        errors.append("v2.8o must require broad preflight before repair")
    if replacement_policy.get("fixed_or_gold_patch_used") is not False or replacement_policy.get("future_outcome_evidence_used") is not False:
        errors.append("v2.8o replacement policy must not use fixed/gold/future evidence")
    if "black_formatter_penalty" not in ranking_policy.get("signals", []) and "black_formatter_penalty" not in ranking_policy.get("decision_time_safe_signals", []):
        errors.append("v2.8o ranking policy must avoid Black formatter bugs as first-choice replacements")
    if fixture_summary.get("fixed_revision_fixture_copying_used") is not False and fixture_summary.get("status") != "pending_linux_workflow_execution":
        errors.append("v2.8o fixture preflight must not copy fixed-revision fixtures")

    workflow_executed = campaign.get("workflow_executed") is True
    if not workflow_executed:
        if campaign.get("aggregate_result") != "blocked_pending_v2_8o_broad_preflight_harvest_artifact":
            errors.append("local v2.8o checkpoint must be pending Linux artifact")
        if campaign.get("scoreable_episode_count") != 0:
            errors.append("local v2.8o checkpoint must not claim scoreable episodes")
    else:
        records = decision.get("records", [])
        by_candidate = {record.get("candidate"): record for record in records}
        for candidate in ["youtube-dl:1", "black:4"]:
            if by_candidate.get(candidate, {}).get("scoreable") is not True:
                errors.append(f"executed v2.8o must preserve {candidate} as scoreable")
        if campaign.get("broad_preflight_candidate_count", 0) < 20 and registry.get("available_candidate_count", 0) >= 20:
            errors.append("executed v2.8o must preflight at least 20 broad candidates when available")
        if campaign.get("scoreable_episode_count", 0) >= 3:
            replacement_scoreable = any(
                record.get("scoreable") is True and record.get("candidate") not in {"youtube-dl:1", "black:4"}
                for record in records
            )
            if not replacement_scoreable:
                errors.append("v2.8o reaching three scoreable episodes requires a replacement episode to be scoreable")
        for record in records:
            classification = record.get("classification")
            if classification not in CLASSIFICATION_VOCABULARY:
                errors.append(f"unexpected v2.8o classification: {classification}")
            directory = OUTPUT_DIR / str(record.get("episode_id"))
            if not directory.exists():
                errors.append(f"executed v2.8o missing {directory}")
                continue
            if record.get("pre_repair_replay_gate_passed") is True:
                for name in REPAIR_ATTEMPT_ARTIFACTS:
                    if not (directory / name).exists():
                        errors.append(f"executed v2.8o repair-attempted {record.get('episode_id')} missing {name}")
            errors.extend(verify_manifest(directory))
        if vocab.get("status") != "PASS":
            errors.append("executed v2.8o classification vocabulary check must pass")

    runner_text = RUNNER.read_text(encoding="utf-8", errors="replace") if RUNNER.exists() else ""
    for snippet in [
        "BROAD_PREFLIGHT_TARGET = 20",
        "enumerate_broad_candidates",
        "candidate_ranking_policy_v2_8o",
        "fixture_dependency_preflight_result",
        "KNOWN_EXCLUDED_FOR_BROAD_HARVEST",
        "fixed_or_gold_patch_used",
    ]:
        if snippet not in runner_text:
            errors.append(f"v2.8o runner missing required snippet: {snippet}")
    workflow_text = WORKFLOW.read_text(encoding="utf-8", errors="replace") if WORKFLOW.exists() else ""
    for snippet in ["workflow_dispatch", "v2_8o_bugsinpy_broad_preflight_harvest_artifacts"]:
        if snippet not in workflow_text:
            errors.append(f"v2.8o workflow missing required snippet: {snippet}")
    baseline_records = pool.get("baseline_records", [])
    if not any(item.get("candidate") == "youtube-dl:1" for item in baseline_records):
        errors.append("v2.8o candidate pool must preserve youtube-dl:1")
    if not any(item.get("candidate") == "black:4" for item in baseline_records):
        errors.append("v2.8o candidate pool must preserve black:4")
    errors.extend(text_contains(SUMMARY, ["v2.8o BugsInPy Broad Preflight Harvest", "Memory lift is not demonstrated", "Self-maintaining software is not demonstrated"]))

    if errors:
        print("v2.8o BugsInPy broad preflight harvest audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8o BugsInPy broad preflight harvest audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
