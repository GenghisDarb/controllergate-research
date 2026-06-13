#!/usr/bin/env python3
"""Audit v2.8n BugsInPy replacement-preflight third-scoreable checkpoint/artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8n_bugsinpy_replacement_preflight_third_scoreable"
V28M_OUTPUT = REPO_ROOT / "outputs" / "v2_8m_bugsinpy_replacement_third_scoreable"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8n_bugsinpy_replacement_preflight_third_scoreable.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8n_bugsinpy_replacement_preflight_third_scoreable_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8n_prepare_bugsinpy_replacement_preflight_third_scoreable.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED_V28M_ZIP_SHA256 = "498b5d384638286ac7665e48f453256df3a1e0e96cc9f8602f66a9401b81d6bf"
OLD_BLOCKED = "blocked_runtime_replay_failure"
NORMALIZED_BLOCKED = "blocked_replay_or_materialization_failure"
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
    "replacement_candidate_policy_v2_8n.json",
    "replacement_candidate_preflight_summary.json",
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

CORE_EPISODE_ARTIFACTS = [
    "episode_metadata.json",
    "candidate_preflight_result.json",
    "failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "limited_scoring_result.json",
    "decision_time_input_manifest.json",
    "decision_time_outcome_overlap_check.json",
    "label_blindness_check.json",
    "gold_patch_exclusion_check.json",
    "corruption_check_result.json",
    "wrapper_contamination_check.json",
    "proof_obligations_ledger.json",
    "SHA256SUMS.txt",
]

PREFLIGHT_PASS_ARTIFACTS = [
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
    "repair_materialization_separation.json",
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
            errors.append(f"missing v2.8n implementation file: {path}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8n output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED_TOP_LEVEL:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.8n artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8n artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))

    campaign, e = load_json(OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    aggregate, e = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(e)
    decision, e = load_json(OUTPUT_DIR / "decision_report.json")
    errors.extend(e)
    pool, e = load_json(OUTPUT_DIR / "candidate_pool.json")
    errors.extend(e)
    policy, e = load_json(OUTPUT_DIR / "replacement_candidate_policy_v2_8n.json")
    errors.extend(e)
    vocab, e = load_json(OUTPUT_DIR / "classification_vocabulary_check.json")
    errors.extend(e)
    v28m_package, e = load_json(V28M_OUTPUT / "artifact_sha256_verification.json")
    errors.extend(e)
    v28m_results, e = load_json(V28M_OUTPUT / "campaign_results.json")
    errors.extend(e)
    v28m_decision, e = load_json(V28M_OUTPUT / "decision_report.json")
    errors.extend(e)
    v28m_vocab, e = load_json(V28M_OUTPUT / "classification_vocabulary_check.json")
    errors.extend(e)

    if v28m_package.get("zip_sha256") != EXPECTED_V28M_ZIP_SHA256:
        errors.append("v2.8n must preserve official v2.8m artifact SHA256")
    if v28m_package.get("internal_sha256_checked") != 312:
        errors.append("v2.8m internal SHA256SUMS checked count must be 312")
    if v28m_package.get("internal_sha256_missing") != 0 or v28m_package.get("internal_sha256_failures") != 0:
        errors.append("v2.8m internal SHA256SUMS must verify with 0 missing/failures")
    if v28m_results.get("executed_episode_count") != 4 or v28m_results.get("scoreable_episode_count") != 2:
        errors.append("v2.8n must preserve official v2.8m 4-executed, 2-scoreable result")
    if v28m_results.get("positive_memory_episode_count") != 0:
        errors.append("v2.8n must preserve official v2.8m zero-positive-memory result")
    records = v28m_decision.get("records", [])
    by_candidate = {item.get("candidate"): item for item in records}
    if by_candidate.get("black:6", {}).get("classification") != NORMALIZED_BLOCKED:
        errors.append("v2.8n must normalize v2.8m black:6 classification")
    if any(item.get("classification") == OLD_BLOCKED for item in records):
        errors.append("v2.8n must remove blocked_runtime_replay_failure from v2.8m decision records")
    if v28m_vocab.get("status") != "PASS":
        errors.append("v2.8m classification vocabulary check must pass after normalization")

    candidates = [item.get("candidate") for item in pool.get("records", [])]
    for expected in ["youtube-dl:1", "black:8", "black:4", "black:6", "black:metadata_next"]:
        if expected not in candidates:
            errors.append(f"v2.8n candidate pool missing {expected}")
    if policy.get("primary_replacement_retry") != "black:6":
        errors.append("v2.8n must retry black:6 with materialization preflight")
    if policy.get("fixed_or_gold_patch_used") is not False or policy.get("future_outcome_evidence_used") is not False:
        errors.append("v2.8n replacement policy must not use fixed/gold/future evidence")
    if "semicolon-delimited" not in policy.get("black6_materialization_fix", ""):
        errors.append("v2.8n policy must document black:6 semicolon target-file-list fix")
    if vocab.get("status") not in {"PASS", "PENDING_UNTIL_FINAL_RECORDS"}:
        errors.append("v2.8n classification vocabulary check must be pending/pass")

    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8n must keep full scoring NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8n must not claim self-maintaining software")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True and aggregate.get("positive_memory_episode_count", 0) < 2:
        errors.append("v2.8n cannot claim memory lift without at least two positive memory episodes")

    workflow_executed = campaign.get("workflow_executed") is True
    if not workflow_executed:
        if campaign.get("aggregate_result") != "blocked_pending_v2_8n_replacement_preflight_artifact":
            errors.append("local v2.8n checkpoint must be blocked pending Linux artifact")
        if campaign.get("scoreable_episode_count") != 0:
            errors.append("local v2.8n checkpoint must not claim scoreable episodes")
    else:
        records = decision.get("records", [])
        if len(records) < 4:
            errors.append("executed v2.8n must include at least four episode records")
        by_candidate = {record.get("candidate"): record for record in records}
        for candidate in ["youtube-dl:1", "black:4"]:
            if by_candidate.get(candidate, {}).get("scoreable") is not True:
                errors.append(f"executed v2.8n must preserve {candidate} as scoreable")
        if by_candidate.get("black:8", {}).get("classification") not in {"failed_both", "blocked_no_safe_patch_candidate_generated"}:
            errors.append("executed v2.8n must keep black:8 non-scoreable under the approved vocabulary")
        for record in records:
            classification = record.get("classification")
            if classification not in CLASSIFICATION_VOCABULARY:
                errors.append(f"unexpected v2.8n classification: {classification}")
            directory = OUTPUT_DIR / str(record.get("episode_id"))
            if not directory.exists():
                errors.append(f"executed v2.8n missing {directory}")
                continue
            for name in CORE_EPISODE_ARTIFACTS:
                if not (directory / name).exists():
                    errors.append(f"executed v2.8n {record.get('episode_id')} missing {name}")
            preflight, ep_errors = load_json(directory / "candidate_preflight_result.json")
            errors.extend(ep_errors)
            if preflight.get("preflight_passed") is True:
                for name in PREFLIGHT_PASS_ARTIFACTS:
                    if not (directory / name).exists():
                        errors.append(f"executed v2.8n preflight-passed {record.get('episode_id')} missing {name}")
            else:
                if record.get("scoreable") is True:
                    errors.append(f"executed v2.8n {record.get('episode_id')} cannot be scoreable if preflight failed")
            errors.extend(verify_manifest(directory))
        if campaign.get("scoreable_episode_count", 0) >= 3:
            replacement_scoreable = any(
                record.get("scoreable") is True and record.get("candidate") not in {"youtube-dl:1", "black:4"}
                for record in records
            )
            if not replacement_scoreable:
                errors.append("v2.8n reaching 3 scoreable episodes requires a replacement episode to be scoreable")

    runner_text = RUNNER.read_text(encoding="utf-8", errors="replace") if RUNNER.exists() else ""
    for snippet in [
        "candidate_preflight_result",
        "blocked_replay_or_materialization_failure",
        "split_metadata_files",
        "classification_vocabulary_check",
        "black:6",
    ]:
        if snippet not in runner_text:
            errors.append(f"v2.8n runner missing required snippet: {snippet}")
    errors.extend(text_contains(SUMMARY, ["v2.8n BugsInPy Replacement Preflight Third Scoreable", "Memory lift: not demonstrated", "Self-maintaining software: not demonstrated"]))

    if errors:
        print("v2.8n BugsInPy replacement preflight third scoreable audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8n BugsInPy replacement preflight third scoreable audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
