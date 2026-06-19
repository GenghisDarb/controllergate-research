#!/usr/bin/env python3
"""Audit v2.8w non-Ansible materialization/readiness checkpoint or artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8w_non_ansible_materialization_repairability"
V28V_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8v_cross_family_positive_memory_generalization"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8w_non_ansible_materialization_repairability.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8w_non_ansible_materialization_repairability_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8w_prepare_non_ansible_materialization_repairability.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BASELINE = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
POSITIVE_BASELINE = ["ansible:2", "ansible:5"]
REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "preserved_v2_8v_baseline_gate_result.json",
    "isomorphism_requirements_matrix_v2_8w.json",
    "non_ansible_materialization_readiness_v2_8w.json",
    "repair_path_taxonomy_v2_8w.json",
    "environmental_stress_state_v2_8w.json",
    "candidate_senescence_policy_v2_8w.json",
    "checkpoint_cycle_manifest_v2_8w.json",
    "duplicate_clean_replay_readiness_v2_8w.json",
    "repair_template_transfer_readiness_v2_8w.json",
    "non_ansible_repairability_candidate_pool_v2_8w.json",
    "memory_arm_separation_check_v2_8w.json",
    "memory_evidence_eligibility_check_v2_8w.json",
    "non_ansible_materialization_integrity_check_v2_8w.json",
    "observer_state_separation_check_v2_8w.json",
    "positive_memory_family_generalization_v2_8w.json",
    "harness_sanity_check.json",
    "command_normalization_policy.json",
    "candidate_chromatin_state_v2_8w.json",
    "local_tension_relief_v2_8w.json",
    "minimal_probe_selection_v2_8w.json",
    "candidate_triage_stability_audit_v2_8w.json",
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
    "environmental_stress_state_result.json",
    "chromatin_state_result.json",
    "repair_path_taxonomy_result.json",
    "checkpoint_cycle_result.json",
    "candidate_senescence_result.json",
    "local_tension_relief_result.json",
    "minimal_probe_selection_result.json",
    "memory_arm_role.json",
    "transfer_template_readiness_result.json",
    "duplicate_clean_replay_readiness_result.json",
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

ALLOWED_MEMORY_LABELS = {
    "replicated_positive_memory_signal_preserved",
    "cross_family_positive_memory_signal_suggestive",
    "replicated_positive_memory_signal_family_limited",
    "suggestive",
    "demonstrated",
    "insufficient_evidence",
    "not_demonstrated",
}


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    return (data if isinstance(data, dict) else {}), ([] if isinstance(data, dict) else [f"{path}: expected JSON object"])


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
            errors.append(f"missing v2.8w implementation file: {path}")
    v28v_campaign, e = load_json(V28V_OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    if v28v_campaign:
        if v28v_campaign.get("preserved_v2_8v_baseline_gate_status") != "PASS" and v28v_campaign.get("preserved_v2_8u_baseline_gate_status") != "PASS":
            errors.append("v2.8w requires verified v2.8v preserved baseline gate")
        if int(v28v_campaign.get("scoreable_episode_count", 0) or 0) < 5:
            errors.append("v2.8w requires v2.8v five-scoreable baseline")
        if int(v28v_campaign.get("positive_memory_episode_count", 0) or 0) < 2:
            errors.append("v2.8w requires v2.8v two-positive-memory baseline")
        if v28v_campaign.get("controllergate_full_scoring") != "NOT_RUN":
            errors.append("v2.8v prerequisite must keep full scoring NOT_RUN")

    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8w output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED_TOP_LEVEL:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.8w artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8w artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))
        tar_files = [path for path in OUTPUT_DIR.rglob("*") if path.is_file() and (path.suffix in {".tar", ".tgz"} or path.name.endswith(".tar.gz") or path.name.endswith(".tar.zst"))]
        if tar_files:
            errors.append(f"v2.8w output directory must not commit tar snapshots: {tar_files[:3]}")

    campaign, e = load_json(OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    aggregate, e = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(e)
    decision, e = load_json(OUTPUT_DIR / "decision_report.json")
    errors.extend(e)
    baseline_gate, e = load_json(OUTPUT_DIR / "preserved_v2_8v_baseline_gate_result.json")
    errors.extend(e)
    isomorphism, e = load_json(OUTPUT_DIR / "isomorphism_requirements_matrix_v2_8w.json")
    errors.extend(e)
    materialization, e = load_json(OUTPUT_DIR / "non_ansible_materialization_readiness_v2_8w.json")
    errors.extend(e)
    taxonomy, e = load_json(OUTPUT_DIR / "repair_path_taxonomy_v2_8w.json")
    errors.extend(e)
    stress, e = load_json(OUTPUT_DIR / "environmental_stress_state_v2_8w.json")
    errors.extend(e)
    senescence, e = load_json(OUTPUT_DIR / "candidate_senescence_policy_v2_8w.json")
    errors.extend(e)
    checkpoint, e = load_json(OUTPUT_DIR / "checkpoint_cycle_manifest_v2_8w.json")
    errors.extend(e)
    duplicate, e = load_json(OUTPUT_DIR / "duplicate_clean_replay_readiness_v2_8w.json")
    errors.extend(e)
    transfer, e = load_json(OUTPUT_DIR / "repair_template_transfer_readiness_v2_8w.json")
    errors.extend(e)
    pool, e = load_json(OUTPUT_DIR / "non_ansible_repairability_candidate_pool_v2_8w.json")
    errors.extend(e)
    separation, e = load_json(OUTPUT_DIR / "memory_arm_separation_check_v2_8w.json")
    errors.extend(e)
    eligibility, e = load_json(OUTPUT_DIR / "memory_evidence_eligibility_check_v2_8w.json")
    errors.extend(e)
    materialization_integrity, e = load_json(OUTPUT_DIR / "non_ansible_materialization_integrity_check_v2_8w.json")
    errors.extend(e)
    observer, e = load_json(OUTPUT_DIR / "observer_state_separation_check_v2_8w.json")
    errors.extend(e)
    family, e = load_json(OUTPUT_DIR / "positive_memory_family_generalization_v2_8w.json")
    errors.extend(e)
    memory, e = load_json(OUTPUT_DIR / "memory_lift_decomposition.json")
    errors.extend(e)
    source_separation, e = load_json(OUTPUT_DIR / "source_repair_vs_harness_separation.json")
    errors.extend(e)
    command_policy, e = load_json(OUTPUT_DIR / "command_normalization_policy.json")
    errors.extend(e)

    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8w must keep full scoring NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8w must not claim self-maintaining software")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True:
        errors.append("v2.8w must not claim broad benchmark memory lift")
    if source_separation.get("tests_may_be_modified_as_repair") is not False:
        errors.append("v2.8w must forbid test edits as repair candidates")
    if "python -m pytest" not in json.dumps(command_policy):
        errors.append("v2.8w must document pytest normalization")
    if "returncode 127" not in json.dumps(command_policy):
        errors.append("v2.8w must document returncode 127 as harness/normalization failure")

    if len(isomorphism.get("layers", [])) != 4:
        errors.append("isomorphism requirements matrix must contain four layers")
    for layer in isomorphism.get("layers", []):
        for key in ["required_mechanisms", "implemented_mechanisms", "partially_implemented_mechanisms", "missing_mechanisms", "tested_this_run", "passed_requirements", "failed_requirements", "next_required_layer", "evidence_files"]:
            if key not in layer:
                errors.append(f"isomorphism layer missing {key}: {layer.get('layer')}")
    if int(materialization.get("non_ansible_candidate_count", 0) or 0) < 2:
        errors.append("v2.8w must diagnose at least two non-Ansible candidates")
    if not taxonomy.get("taxonomy_assigned_before_heuristic_selection"):
        errors.append("repair-path taxonomy must be assigned before heuristic selection")
    if stress.get("blocking_candidates_attempted_without_relief") not in {False, None}:
        errors.append("blocking-stress candidates must not be attempted without relief")
    retired = {item.get("candidate"): item.get("retirement_status") for item in senescence.get("records", [])}
    for candidate in ["ansible:4", "ansible:12", "ansible:13"]:
        if retired.get(candidate) not in {"watchlist", "temporarily_retired", "retired_until_new_evidence"}:
            errors.append(f"{candidate} must be reviewed for senescence/retirement")
    if senescence.get("permanent_retirement_without_reopen_condition") is True:
        errors.append("senescence policy must not permanently retire without reopen condition")
    if len(checkpoint.get("phase_order", [])) < 19:
        errors.append("checkpoint cycle manifest must record the full phase order")
    if duplicate.get("duplicate_replay_supported") is not True:
        errors.append("duplicate clean replay readiness must be supported")
    if transfer.get("transfer_success_claimed") is True:
        errors.append("v2.8w must not claim repair-template transfer success")
    if not pool.get("non_ansible_candidates"):
        errors.append("v2.8w candidate pool must include non-Ansible candidates")
    for artifact_name, data in [
        ("materialization readiness", materialization),
        ("repair taxonomy", taxonomy),
        ("environmental stress", stress),
        ("candidate pool", pool),
    ]:
        candidates: list[Any] = []
        candidates.extend(item.get("candidate") for item in data.get("records", []) if isinstance(item, dict))
        for key in ["selected_candidates", "non_ansible_candidates", "full_candidate_pool"]:
            value = data.get(key)
            if isinstance(value, list):
                candidates.extend(value)
        malformed = [candidate for candidate in candidates if isinstance(candidate, str) and candidate.strip().startswith("{")]
        if malformed:
            errors.append(f"v2.8w {artifact_name} contains malformed stringified candidate metadata: {malformed[:3]}")
    if separation.get("no_memory_accessed_repair_memory_only_data") is not False:
        errors.append("no-memory arm must not access RepairMemory-only data")
    if separation.get("no_memory_accessed_positive_memory_transfer_readiness_data") is not False:
        errors.append("no-memory arm must not access transfer-template memory")
    if eligibility.get("future_outcome_evidence_used_at_decision_time") is not False:
        errors.append("memory eligibility must forbid future outcome evidence")
    if observer.get("observer_state_contamination_count") not in {0, None}:
        errors.append("observer-state contamination count must be zero")
    for section in ["repair_outcome_memory_lift", "selection_memory_lift", "stability_memory_lift", "global_closure_memory_lift"]:
        label = memory.get(section, {}).get("label")
        if label not in ALLOWED_MEMORY_LABELS:
            errors.append(f"invalid memory-lift label for {section}: {label}")

    workflow_executed = campaign.get("workflow_executed") is True
    if not workflow_executed:
        if campaign.get("aggregate_result") != "blocked_pending_v2_8w_non_ansible_materialization_repairability_artifact":
            errors.append("local v2.8w checkpoint must remain pending until official workflow artifact")
        for name, data in [
            ("baseline gate", baseline_gate),
            ("isomorphism matrix", isomorphism),
            ("materialization readiness", materialization),
            ("repair taxonomy", taxonomy),
            ("stress state", stress),
            ("senescence", senescence),
            ("memory separation", separation),
            ("memory eligibility", eligibility),
            ("materialization integrity", materialization_integrity),
            ("observer separation", observer),
        ]:
            if data.get("status") not in {"PENDING_GITHUB_ACTIONS", "PASS"}:
                errors.append(f"local v2.8w {name} must be pending or pass")
    else:
        records = decision.get("records", [])
        by_candidate: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            by_candidate.setdefault(str(record.get("candidate")), []).append(record)

        def has_scoreable(candidate: str) -> bool:
            return any(record.get("scoreable") is True for record in by_candidate.get(candidate, []))

        def has_positive(candidate: str) -> bool:
            return any(record.get("scoreable") is True and record.get("classification") == "positive_memory_only" for record in by_candidate.get(candidate, []))

        if baseline_gate.get("status") != "PASS":
            errors.append("official v2.8w preserved v2.8v baseline gate must pass")
        for candidate in BASELINE:
            if not has_scoreable(candidate):
                errors.append(f"official v2.8w must preserve {candidate} as scoreable")
        for candidate in POSITIVE_BASELINE:
            if not has_positive(candidate):
                errors.append(f"official v2.8w must preserve {candidate} positive_memory_only status")
        if int(campaign.get("scoreable_episode_count", 0) or 0) < 5:
            errors.append("official v2.8w must preserve at least five scoreable episodes")
        if int(campaign.get("positive_memory_episode_count", 0) or 0) < 2:
            errors.append("official v2.8w must preserve at least two positive-memory episodes")
        attempted_candidates = campaign.get("attempted_candidates") or campaign.get("attempted_cross_family_candidates") or []
        baseline_attempts = [candidate for candidate in attempted_candidates if candidate in BASELINE]
        if baseline_attempts:
            errors.append(f"official v2.8w new repairability attempts must not include preserved baseline anchors: {baseline_attempts}")
        for key in ["label_leakage_count", "decision_time_outcome_overlap_count", "corruption_count"]:
            if campaign.get(key) != 0:
                errors.append(f"official v2.8w must have zero {key}")
        for check_name, data in [
            ("memory arm separation", separation),
            ("memory eligibility", eligibility),
            ("non-Ansible materialization integrity", materialization_integrity),
            ("observer state separation", observer),
            ("isomorphism matrix", isomorphism),
            ("materialization readiness", materialization),
            ("repair taxonomy", taxonomy),
            ("stress state", stress),
            ("senescence", senescence),
            ("checkpoint cycle", checkpoint),
            ("duplicate replay readiness", duplicate),
            ("transfer readiness", transfer),
        ]:
            if data.get("status") != "PASS":
                errors.append(f"official v2.8w {check_name} must PASS")
        taxonomy_records = taxonomy.get("records", [])
        non_ansible_clear = [item for item in taxonomy_records if item.get("project_family") != "ansible" and item.get("likely_repair_path") not in {None, "unknown_no_safe_path"}]
        if not non_ansible_clear:
            errors.append("official v2.8w must assign a clear repair path to at least one non-Ansible candidate or explain safely")
        for record in records:
            directory = OUTPUT_DIR / str(record.get("episode_id"))
            if not directory.exists():
                errors.append(f"official v2.8w missing episode directory: {directory}")
                continue
            for name in REQUIRED_EPISODE_ARTIFACTS:
                if not (directory / name).exists():
                    errors.append(f"official v2.8w {record.get('episode_id')} missing {name}")
            role, role_errors = load_json(directory / "memory_arm_role.json")
            errors.extend(role_errors)
            if role.get("fixed_or_gold_patch_allowed") is not False or role.get("future_outcome_evidence_allowed") is not False:
                errors.append(f"official v2.8w {record.get('episode_id')} memory role has forbidden evidence allowed")
            errors.extend(verify_manifest(directory))

    errors.extend(
        text_contains(
            RUNNER,
            [
                "preserved_v2_8v_baseline_gate_result",
                "runner_regression_v2_8v_baseline_failure",
                "isomorphism_requirements_matrix_v2_8w",
                "non_ansible_materialization_readiness_v2_8w",
                "repair_path_taxonomy_v2_8w",
                "environmental_stress_state_v2_8w",
                "candidate_senescence_policy_v2_8w",
                "checkpoint_cycle_manifest_v2_8w",
                "duplicate_clean_replay_readiness_v2_8w",
                "repair_template_transfer_readiness_v2_8w",
                "non_ansible_repairability_candidate_pool_v2_8w",
                "observer_state_separation_check_v2_8w",
                "no_memory_accessed_positive_memory_transfer_readiness_data",
            ],
        )
    )
    errors.extend(
        text_contains(
            WORKFLOW,
            [
                "workflow_dispatch",
                "v2_8w_non_ansible_materialization_repairability_artifacts",
                "isomorphism_requirements_matrix_v2_8w",
                "non_ansible_materialization_readiness_v2_8w",
                "repair_path_taxonomy_v2_8w",
                "observer_state_separation_check_v2_8w",
                "actions/upload-artifact@v4",
            ],
        )
    )
    errors.extend(
        text_contains(
            SUMMARY,
            [
                "v2.8w Non-Ansible Materialization Repairability",
                "Full scoring remains",
                "Self-maintaining software is not demonstrated",
            ],
        )
    )
    if errors:
        print("v2.8w non-Ansible materialization repairability audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8w non-Ansible materialization repairability audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
