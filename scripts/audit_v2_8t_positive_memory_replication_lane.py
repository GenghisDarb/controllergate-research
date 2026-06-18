#!/usr/bin/env python3
"""Audit v2.8t positive-memory replication checkpoint/artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8t_positive_memory_replication_lane"
V28S_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8s_positive_memory_evidence_lane"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8t_positive_memory_replication_lane.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8t_positive_memory_replication_lane_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8t_prepare_positive_memory_replication_lane.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

CLASSIFICATION_VOCABULARY = {
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "failed_both",
    "inconclusive_equal_performance",
    "no_memory_only",
    "positive_memory_only",
    "runner_regression_preserved_reference_failure",
    "runner_regression_v2_8s_baseline_failure",
}

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "preserved_v2_8s_baseline_gate_result.json",
    "harness_sanity_check.json",
    "command_normalization_policy.json",
    "memory_replication_candidate_selection_policy_v2_8t.json",
    "memory_arm_separation_check_v2_8t.json",
    "memory_evidence_eligibility_check_v2_8t.json",
    "memory_replication_integrity_check_v2_8t.json",
    "candidate_chromatin_state_v2_8t.json",
    "local_tension_relief_v2_8t.json",
    "minimal_probe_selection_v2_8t.json",
    "candidate_triage_stability_audit_v2_8t.json",
    "closure_scaling_audit.json",
    "memory_lift_decomposition.json",
    "broad_candidate_preflight_registry.json",
    "replacement_candidate_policy.json",
    "replacement_candidate_preflight_summary.json",
    "fixture_dependency_preflight_summary.json",
    "candidate_ranking_policy.json",
    "bounded_repair_proposer_summary.json",
    "candidate_pool.json",
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

REQUIRED_EPISODE_ARTIFACTS = [
    "episode_metadata.json",
    "candidate_preflight_result.json",
    "fixture_dependency_preflight_result.json",
    "command_normalization_result.json",
    "chromatin_state_result.json",
    "local_tension_relief_result.json",
    "minimal_probe_selection_result.json",
    "memory_arm_role.json",
    "failing_command.txt",
    "normalized_failing_command.txt",
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

ALLOWED_MEMORY_LABELS = {"replicated_positive_signal", "single_positive_signal_not_replicated_yet", "demonstrated", "suggestive", "not_demonstrated", "insufficient_evidence"}


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


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        if sha_file(path) != expected:
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
            errors.append(f"missing v2.8t implementation file: {path}")
    if not V28S_OUTPUT_DIR.exists():
        errors.append(f"missing v2.8s official baseline output directory: {V28S_OUTPUT_DIR}")
    else:
        v28s_campaign, e = load_json(V28S_OUTPUT_DIR / "campaign_results.json")
        errors.extend(e)
        if v28s_campaign.get("preserved_v2_8r_baseline_gate_status") != "PASS":
            errors.append("v2.8t requires verified v2.8s preserved baseline artifacts")
        if v28s_campaign.get("scoreable_episode_count", 0) < 4:
            errors.append("v2.8t requires v2.8s four-scoreable baseline")
        if v28s_campaign.get("positive_memory_episode_count", 0) < 1:
            errors.append("v2.8t requires v2.8s positive-memory baseline")

    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8t output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED_TOP_LEVEL:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.8t artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8t artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))
        tar_files = [path for path in OUTPUT_DIR.rglob("*") if path.is_file() and (path.suffix in {".tar", ".tgz"} or path.name.endswith(".tar.gz"))]
        if tar_files:
            errors.append(f"v2.8t output directory must not commit large tar snapshots: {tar_files[:3]}")

    campaign, e = load_json(OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    aggregate, e = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(e)
    decision, e = load_json(OUTPUT_DIR / "decision_report.json")
    errors.extend(e)
    baseline_gate, e = load_json(OUTPUT_DIR / "preserved_v2_8s_baseline_gate_result.json")
    errors.extend(e)
    harness, e = load_json(OUTPUT_DIR / "harness_sanity_check.json")
    errors.extend(e)
    selection, e = load_json(OUTPUT_DIR / "memory_replication_candidate_selection_policy_v2_8t.json")
    errors.extend(e)
    separation, e = load_json(OUTPUT_DIR / "memory_arm_separation_check_v2_8t.json")
    errors.extend(e)
    eligibility, e = load_json(OUTPUT_DIR / "memory_evidence_eligibility_check_v2_8t.json")
    errors.extend(e)
    integrity, e = load_json(OUTPUT_DIR / "memory_replication_integrity_check_v2_8t.json")
    errors.extend(e)
    memory, e = load_json(OUTPUT_DIR / "memory_lift_decomposition.json")
    errors.extend(e)
    stability, e = load_json(OUTPUT_DIR / "candidate_triage_stability_audit_v2_8t.json")
    errors.extend(e)
    source_separation, e = load_json(OUTPUT_DIR / "source_repair_vs_harness_separation.json")
    errors.extend(e)
    vocab, e = load_json(OUTPUT_DIR / "classification_vocabulary_check.json")
    errors.extend(e)

    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8t must keep full scoring NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8t must not claim self-maintaining software")
    if source_separation.get("tests_may_be_modified_as_repair") is not False:
        errors.append("v2.8t must forbid test edits as repair candidates")
    if "python -m pytest" not in json.dumps(load_json(OUTPUT_DIR / "command_normalization_policy.json")[0]):
        errors.append("v2.8t must document pytest normalization to python -m pytest")
    if "returncode 127" not in json.dumps(load_json(OUTPUT_DIR / "command_normalization_policy.json")[0]):
        errors.append("v2.8t must document returncode 127 as harness/normalization failure")
    if selection.get("selection_used_only_decision_time_safe_evidence") is not True:
        errors.append("v2.8t memory candidate selection must use only decision-time-safe evidence")
    if not selection.get("selected_memory_replication_candidates"):
        errors.append("v2.8t must record selected memory-replication candidates")
    if selection.get("ansible2_prior_positive_used_as_future_outcome_evidence") is not False:
        errors.append("v2.8t selection must not use ansible:2 prior positive as future outcome evidence")
    if stability.get("queue_bias_detected") is not False:
        errors.append("v2.8t stability audit must not detect queue bias")
    if stability.get("gate_topology_dependence_confirmed") is not True:
        errors.append("v2.8t stability audit must confirm gate topology dependence")

    workflow_executed = campaign.get("workflow_executed") is True
    positives = int(campaign.get("positive_memory_episode_count", 0) or 0)
    repair_label = memory.get("repair_outcome_memory_lift", {}).get("label")
    for section in ["repair_outcome_memory_lift", "selection_memory_lift", "stability_memory_lift", "global_closure_memory_lift"]:
        label = memory.get(section, {}).get("label")
        if label not in ALLOWED_MEMORY_LABELS:
            errors.append(f"invalid memory lift label for {section}: {label}")
    if workflow_executed:
        if positives >= 2 and repair_label != "replicated_positive_signal":
            errors.append("two total positive memory episodes require repair_outcome_memory_lift replicated_positive_signal")
        if positives == 1 and repair_label != "single_positive_signal_not_replicated_yet":
            errors.append("one total positive memory episode requires repair_outcome_memory_lift single_positive_signal_not_replicated_yet")
        if positives == 0 and repair_label != "not_demonstrated":
            errors.append("zero positive memory episodes require repair_outcome_memory_lift not_demonstrated")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True:
        errors.append("v2.8t must not claim existing benchmark memory lift")

    if not workflow_executed:
        if campaign.get("aggregate_result") != "blocked_pending_v2_8t_positive_memory_replication_artifact":
            errors.append("local v2.8t checkpoint must remain pending until Linux artifact ingestion")
        for item_name, data in [("baseline gate", baseline_gate), ("harness sanity", harness), ("memory separation", separation), ("memory eligibility", eligibility), ("memory replication integrity", integrity)]:
            if data.get("status") != "PENDING_GITHUB_ACTIONS":
                errors.append(f"local v2.8t {item_name} must be pending")
    else:
        records = decision.get("records", [])
        by_candidate = {record.get("candidate"): record for record in records}
        if baseline_gate.get("status") != "PASS":
            errors.append("executed v2.8t preserved v2.8s baseline gate must pass")
        for candidate in ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2"]:
            if by_candidate.get(candidate, {}).get("scoreable") is not True:
                errors.append(f"executed v2.8t must preserve {candidate} as scoreable")
        if by_candidate.get("ansible:2", {}).get("classification") != "positive_memory_only" or baseline_gate.get("ansible2_positive_memory_only_status_preserved") is not True:
            errors.append("executed v2.8t must preserve ansible:2 positive_memory_only status")
        if harness.get("status") != "PASS":
            errors.append("executed v2.8t harness sanity must pass")
        if separation.get("status") != "PASS":
            errors.append("executed v2.8t memory arm separation check must pass")
        if eligibility.get("status") != "PASS":
            errors.append("executed v2.8t memory replication eligibility check must pass")
        if integrity.get("status") != "PASS":
            errors.append("executed v2.8t memory replication integrity check must pass")
        if separation.get("no_memory_accessed_repair_memory_only_data") is not False:
            errors.append("no-memory arm must not access RepairMemory-only data")
        if eligibility.get("future_outcome_evidence_used_at_decision_time") is not False:
            errors.append("memory replication eligibility must forbid future outcome evidence")
        if eligibility.get("ansible2_prior_positive_used_as_future_outcome_evidence") is not False:
            errors.append("ansible:2 prior positive must not be used as future outcome evidence")
        if int(campaign.get("scoreable_episode_count", 0) or 0) < 4:
            errors.append("executed v2.8t must have at least four scoreable episodes")
        if int(campaign.get("positive_memory_episode_count", 0) or 0) < 1:
            errors.append("executed v2.8t must preserve at least one positive memory episode")
        for key in ["label_leakage_count", "decision_time_outcome_overlap_count", "corruption_count"]:
            if campaign.get(key) != 0:
                errors.append(f"executed v2.8t must have zero {key}")
        attempted = campaign.get("attempted_memory_replication_candidates", [])
        new_positive_count = int(campaign.get("new_positive_memory_episode_count", 0) or 0)
        if new_positive_count == 0 and len(attempted) < 3:
            errors.append("executed v2.8t must attempt at least three memory-replication candidates unless a positive memory episode appears")
        if positives > 0 and not any(record.get("classification") == "positive_memory_only" for record in records):
            errors.append("positive memory count requires at least one positive_memory_only episode")
        if campaign.get("replicated_positive_memory_signal") is True and positives < 2:
            errors.append("replicated positive memory signal requires at least two total positive episodes")
        if vocab.get("status") != "PASS":
            errors.append("executed v2.8t classification vocabulary check must pass")
        for record in records:
            if record.get("classification") not in CLASSIFICATION_VOCABULARY:
                errors.append(f"unexpected v2.8t classification: {record.get('classification')}")
            directory = OUTPUT_DIR / str(record.get("episode_id"))
            if not directory.exists():
                errors.append(f"executed v2.8t missing episode directory: {directory}")
                continue
            for name in REQUIRED_EPISODE_ARTIFACTS:
                if not (directory / name).exists():
                    errors.append(f"executed v2.8t {record.get('episode_id')} missing {name}")
            role, role_errors = load_json(directory / "memory_arm_role.json")
            errors.extend(role_errors)
            if role.get("fixed_or_gold_patch_allowed") is not False or role.get("future_outcome_evidence_allowed") is not False:
                errors.append(f"executed v2.8t {record.get('episode_id')} memory arm role has forbidden evidence allowed")
            errors.extend(verify_manifest(directory))

    errors.extend(
        text_contains(
            RUNNER,
            [
                "preserved_v2_8s_baseline_gate_result",
                "runner_regression_v2_8s_baseline_failure",
                "memory_replication_candidate_selection_policy_v2_8t",
                "memory_arm_separation_check_v2_8t",
                "memory_evidence_eligibility_check_v2_8t",
                "memory_replication_integrity_check_v2_8t",
                "repair_workspace_pythonpath_isolation",
                "no_memory_accessed_repair_memory_only_data",
                "future_outcome_evidence_used_at_decision_time",
            ],
        )
    )
    errors.extend(
        text_contains(
            WORKFLOW,
            [
                "workflow_dispatch",
                "v2_8t_positive_memory_replication_lane_artifacts",
                "memory_arm_separation_check_v2_8t",
                "memory_evidence_eligibility_check_v2_8t",
                "memory_replication_integrity_check_v2_8t",
                "actions/upload-artifact@v4",
            ],
        )
    )
    errors.extend(
        text_contains(
            SUMMARY,
            [
                "v2.8t Positive Memory Replication Lane",
                "Full scoring remains",
                "Self-maintaining software is not demonstrated",
            ],
        )
    )

    if errors:
        print("v2.8t positive memory replication lane audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8t positive memory replication lane audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
