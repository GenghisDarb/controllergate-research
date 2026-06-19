#!/usr/bin/env python3
"""Audit v2.12 dependency-cofactor recovery artifacts or pending checkpoint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_12_dependency_cofactor_recovery"
V211_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_11_topology_aware_source_repair"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_12_dependency_cofactor_recovery.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_12_dependency_cofactor_recovery_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_12_prepare_dependency_cofactor_recovery.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BASELINE = {"youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"}
POSITIVE_BASELINE = {"ansible:2", "ansible:5"}

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md", "campaign_results.json", "decision_report.json", "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", "preserved_v2_11_baseline_gate_result.json",
    "dependency_cofactor_recovery_plan_v2_12.json", "python_toolbox_recovery_audit_v2_12.json",
    "declared_dependency_evidence_v2_12.json", "cofactor_recovery_decision_log_v2_12.json",
    "v2_11_patch_revalidation_v2_12.json", "pysnooper_patch_validation_v2_12.json",
    "v2_12_candidate_recovery_queue.json", "bounded_topology_aware_repair_proposer_v2_12.json",
    "topology_to_patch_proof_ledger_v2_12.json", "recovered_surface_repair_plan_v2_12.json",
    "duplicate_clean_replay_verification_v2_12.json", "phase_inversion_seed_constraint_check_v2_12.json",
    "memory_arm_separation_check_v2_12.json", "memory_evidence_eligibility_check_v2_12.json",
    "observer_state_separation_check_v2_12.json", "dependency_cofactor_anti_leakage_check_v2_12.json",
    "source_patch_anti_leakage_check_v2_12.json", "heterochromatin_monitor_v2_12.json",
    "silent_scaffolding_risk_audit_v2_12.json", "isomorphism_requirements_matrix_v2_12.json",
    "positive_memory_family_generalization_v2_12.json", "harness_sanity_check.json",
    "command_normalization_policy.json", "candidate_chromatin_state_v2_12.json",
    "local_tension_relief_v2_12.json", "minimal_probe_selection_v2_12.json",
    "candidate_triage_stability_audit_v2_12.json", "closure_scaling_audit.json",
    "memory_lift_decomposition.json", "broad_candidate_preflight_registry.json", "replacement_candidate_policy.json",
    "replacement_candidate_preflight_summary.json", "fixture_dependency_preflight_summary.json",
    "candidate_ranking_policy.json", "bounded_repair_proposer_summary.json", "candidate_pool.json",
    "candidate_source_integrity_check.json", "decision_time_policy.json", "anti_leakage_policy.json",
    "source_discovery_summary.json", "pre_repair_replay_gate_summary.json", "workspace_equivalence_summary.json",
    "source_repair_vs_harness_separation.json", "classification_vocabulary_check.json", "audit.json",
    "package_verification.json", "artifact_sha256_verification.json", "SHA256SUMS.txt",
]

REQUIRED_EPISODE = [
    "episode_metadata.json", "candidate_preflight_result.json", "fixture_dependency_preflight_result.json",
    "command_normalization_result.json", "dependency_cofactor_recovery_result.json",
    "declared_dependency_evidence_result.json", "cofactor_recovery_decision_result.json",
    "candidate_recovery_queue_result.json", "context_bundle_reuse_result.json",
    "recovered_surface_repair_plan_result.json", "environmental_stress_state_result.json",
    "chromatin_state_result.json", "heterochromatin_monitor_result.json", "silent_scaffolding_risk_result.json",
    "repair_path_taxonomy_result.json", "topology_aware_repair_proposer_result.json",
    "topology_to_patch_proof_ledger_result.json", "checkpoint_cycle_result.json",
    "candidate_senescence_result.json", "local_tension_relief_result.json", "minimal_probe_selection_result.json",
    "memory_arm_role.json", "duplicate_clean_replay_result.json", "phase_inversion_seed_constraint_result.json",
    "failing_command.txt", "normalized_failing_command.txt", "failing_log_raw.txt", "failure_signature.txt",
    "source_discovery_report.json", "ranked_candidate_source_files.json", "candidate_function_extracts.json",
    "repair_heuristic_selection.json", "no_memory_repair_candidate_generation.json",
    "memory_enabled_repair_candidate_generation.json", "no_memory_source_only_repair_patch.diff",
    "memory_enabled_source_only_repair_patch.diff", "patch_candidate_safety_check.json",
    "no_memory_patch_application_result.json", "memory_enabled_patch_application_result.json",
    "no_memory_post_repair_command.txt", "memory_enabled_post_repair_command.txt",
    "no_memory_post_repair_log_raw.txt", "memory_enabled_post_repair_log_raw.txt",
    "post_repair_comparison.json", "limited_scoring_result.json", "decision_time_input_manifest.json",
    "decision_time_outcome_overlap_check.json", "label_blindness_check.json", "gold_patch_exclusion_check.json",
    "corruption_check_result.json", "wrapper_contamination_check.json", "repair_materialization_separation.json",
    "proof_obligations_ledger.json", "SHA256SUMS.txt",
]


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    if not isinstance(value, dict):
        return {}, [f"{path}: expected JSON object"]
    return value, []


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
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            errors.append(f"{manifest}:{line_no}: malformed manifest entry")
            continue
        expected, rel = parts
        seen.add(rel)
        path = directory / rel
        if not path.exists():
            errors.append(f"{manifest}:{line_no}: missing artifact {rel}")
        elif sha_file(path) != expected:
            errors.append(f"{manifest}:{line_no}: hash mismatch for {rel}")
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rel = str(path.relative_to(directory)).replace("\\", "/")
            if rel not in seen:
                errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def record_by_candidate(data: dict[str, Any], candidate: str) -> dict[str, Any]:
    return next((record for record in data.get("records", []) if isinstance(record, dict) and record.get("candidate") == candidate), {})


def status_pass(data: dict[str, Any]) -> bool:
    return data.get("status") == "PASS"


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.12 implementation file: {path}")

    campaign211, e = load_json(V211_OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    if campaign211:
        if int(campaign211.get("scoreable_episode_count", 0) or 0) < 5:
            errors.append("v2.12 requires the verified v2.11 five-scoreable baseline")
        if int(campaign211.get("positive_memory_episode_count", 0) or 0) < 2:
            errors.append("v2.12 requires the verified v2.11 two-positive baseline")
        if campaign211.get("controllergate_full_scoring") != "NOT_RUN":
            errors.append("v2.11 prerequisite must keep full scoring NOT_RUN")

    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.12 output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED_TOP_LEVEL:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.12 artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.12 artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))
        tar_files = [path for path in OUTPUT_DIR.rglob("*") if path.is_file() and (path.suffix in {".tar", ".tgz"} or path.name.endswith((".tar.gz", ".tar.zst")))]
        if tar_files:
            errors.append(f"v2.12 output directory must not commit tar snapshots: {tar_files[:3]}")

    campaign, e = load_json(OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    pending = campaign.get("workflow_executed") is False or str(campaign.get("aggregate_result", "")).startswith("blocked_pending_")
    if pending:
        if campaign.get("controllergate_full_scoring") != "NOT_RUN" or campaign.get("full_scoring_allowed") is not False:
            errors.append("pending v2.12 checkpoint must keep full scoring NOT_RUN/disallowed")
        if campaign.get("self_maintaining_software_demonstrated") is not False:
            errors.append("pending v2.12 checkpoint must not claim self-maintaining software")
        summary_text = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
        if "## v2.12 Dependency Cofactor Recovery and Locked Non-Ansible Repair Validation Lane" not in summary_text:
            errors.append("shareable summary missing v2.12 block")
        if errors:
            print("v2.12 dependency cofactor recovery audit FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        print("v2.12 dependency cofactor recovery audit PASS")
        return 0

    names = [
        "preserved_v2_11_baseline_gate_result.json", "dependency_cofactor_recovery_plan_v2_12.json",
        "python_toolbox_recovery_audit_v2_12.json", "declared_dependency_evidence_v2_12.json",
        "cofactor_recovery_decision_log_v2_12.json", "v2_11_patch_revalidation_v2_12.json",
        "pysnooper_patch_validation_v2_12.json", "v2_12_candidate_recovery_queue.json",
        "bounded_topology_aware_repair_proposer_v2_12.json", "topology_to_patch_proof_ledger_v2_12.json",
        "duplicate_clean_replay_verification_v2_12.json", "phase_inversion_seed_constraint_check_v2_12.json",
        "memory_arm_separation_check_v2_12.json", "memory_evidence_eligibility_check_v2_12.json",
        "observer_state_separation_check_v2_12.json", "dependency_cofactor_anti_leakage_check_v2_12.json",
        "source_patch_anti_leakage_check_v2_12.json", "heterochromatin_monitor_v2_12.json",
        "silent_scaffolding_risk_audit_v2_12.json", "isomorphism_requirements_matrix_v2_12.json",
        "positive_memory_family_generalization_v2_12.json", "classification_vocabulary_check.json", "audit.json",
    ]
    loaded: dict[str, dict[str, Any]] = {}
    for name in names:
        loaded[name], e = load_json(OUTPUT_DIR / name)
        errors.extend(e)
    for name, data in loaded.items():
        if not status_pass(data):
            errors.append(f"{name}.status must be PASS")

    baseline = loaded["preserved_v2_11_baseline_gate_result.json"]
    if baseline.get("preserved_v2_11_baseline_gate_status") != "PASS":
        errors.append("preserved v2.11 baseline gate must PASS")
    scoreable_status = baseline.get("scoreable_status_by_episode") or {}
    if len([value for value in scoreable_status.values() if value is True]) < 5:
        errors.append("v2.12 baseline gate must preserve five scoreable episodes")
    positive_status = baseline.get("positive_memory_only_preservation_status") or {}
    for candidate in POSITIVE_BASELINE:
        if positive_status.get(candidate) is not True:
            errors.append(f"{candidate} positive_memory_only preservation must be true")

    if int(campaign.get("scoreable_episode_count", 0) or 0) < 5:
        errors.append("scoreable_episode_count must be >= 5")
    if int(campaign.get("positive_memory_episode_count", 0) or 0) < 2:
        errors.append("positive_memory_episode_count must be >= 2")
    if campaign.get("controllergate_full_scoring") != "NOT_RUN" or campaign.get("full_scoring_allowed") is not False:
        errors.append("full scoring must remain NOT_RUN/disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain false")
    for field in ["label_leakage_count", "decision_time_outcome_overlap_count", "corruption_count"]:
        if int(campaign.get(field, 0) or 0) != 0:
            errors.append(f"{field} must be zero")

    plan = loaded["dependency_cofactor_recovery_plan_v2_12.json"]
    if plan.get("complete") is not True:
        errors.append("dependency cofactor recovery plan must be complete")
    if int(plan.get("arbitrary_undeclared_package_install_count", 0) or 0) != 0:
        errors.append("arbitrary undeclared package install count must be zero")
    py1 = record_by_candidate(plan, "PySnooper:1")
    py2 = record_by_candidate(plan, "PySnooper:2")
    if py1.get("blocker_name") != "python_toolbox" or py1.get("declared_in_project_metadata") is not False:
        errors.append("PySnooper:1 must record python_toolbox as undeclared")
    if py1.get("recovery_allowed_by_policy") is not False or py1.get("recovery_performed") is not False:
        errors.append("PySnooper:1 undeclared cofactor recovery must be forbidden and not performed")
    if py1.get("recovery_action") != "forbidden_by_policy":
        errors.append("PySnooper:1 recovery action must be forbidden_by_policy")
    if py2.get("declared_in_project_metadata") is not True:
        errors.append("PySnooper:2 must have declared python_toolbox evidence")
    if not py2.get("metadata_source_files"):
        errors.append("PySnooper:2 declared dependency evidence must name metadata sources")

    dependency_anti = loaded["dependency_cofactor_anti_leakage_check_v2_12.json"]
    if int(dependency_anti.get("arbitrary_undeclared_dependency_install_count", 0) or 0) != 0:
        errors.append("dependency anti-leakage must report zero undeclared installs")
    if dependency_anti.get("project_source_modified_during_dependency_recovery") is not False:
        errors.append("dependency recovery must not modify project source")
    source_anti = loaded["source_patch_anti_leakage_check_v2_12.json"]
    if source_anti.get("fixed_gold_future_patch_source_used") is not False or source_anti.get("test_files_modified_count") not in {0, "0"}:
        errors.append("source patch anti-leakage boundary failed")

    revalidation = loaded["v2_11_patch_revalidation_v2_12.json"]
    if revalidation.get("patch_exists") is not True or revalidation.get("patch_hash_matches") is not True:
        errors.append("v2.11 PySnooper patch evidence must exist and match the recorded hash")
    if revalidation.get("patch_altered_after_outcome_observation") is not False:
        errors.append("v2.11 patch must not be altered after outcome observation")
    if revalidation.get("classification") != "dependency_recovery_forbidden_by_policy":
        errors.append("PySnooper:1 no-lock proof must classify dependency recovery forbidden by policy")

    queue = loaded["v2_12_candidate_recovery_queue.json"]
    if queue.get("broad_candidate_search_restarted") is not False:
        errors.append("v2.12 must not restart broad candidate search")
    queue_py1 = record_by_candidate(queue, "PySnooper:1")
    queue_py2 = record_by_candidate(queue, "PySnooper:2")
    if queue_py1.get("selected_for_attempt") is not True or queue_py2.get("selected_for_attempt") is not True:
        errors.append("locked PySnooper:1 and declared fallback PySnooper:2 must both be evaluated")

    validation = loaded["pysnooper_patch_validation_v2_12.json"]
    validation_py2 = record_by_candidate(validation, "PySnooper:2")
    if not validation_py2:
        errors.append("PySnooper:2 validation record is required")
    duplicate = loaded["duplicate_clean_replay_verification_v2_12.json"]
    phase = loaded["phase_inversion_seed_constraint_check_v2_12.json"]
    duplicate_py2 = record_by_candidate(duplicate, "PySnooper:2")
    phase_py2 = record_by_candidate(phase, "PySnooper:2")
    if validation_py2.get("scoreable") is True:
        if duplicate_py2.get("duplicate_clean_replay_status") != "pass":
            errors.append("new PySnooper:2 scoreable result requires duplicate replay pass")
        if phase_py2.get("phase_inversion_status") != "pass":
            errors.append("new PySnooper:2 scoreable result requires phase inversion pass")

    family = loaded["positive_memory_family_generalization_v2_12.json"]
    non_ansible_positive = int(family.get("non_ansible_positive_memory_count", 0) or 0)
    if non_ansible_positive == 0:
        if family.get("family_generalization") != "not_expanded":
            errors.append("family generalization must remain not_expanded without a non-Ansible positive")
        if family.get("cross_family_positive_memory_signal_suggestive") is not False:
            errors.append("cross-family signal must remain false without a non-Ansible positive")
        if campaign.get("repair_outcome_memory_lift") != "replicated_positive_memory_signal_preserved":
            errors.append("repair-outcome memory lift must remain replicated_positive_memory_signal_preserved")

    matrix = loaded["isomorphism_requirements_matrix_v2_12.json"]
    layers = matrix.get("layers") or []
    expected_layers = {"chromosome_chromatin_isomorphism", "tld_isomorphism", "tot_brot_isomorphism", "torus_brot_isomorphism"}
    if {layer.get("layer") for layer in layers if isinstance(layer, dict)} != expected_layers:
        errors.append("v2.12 isomorphism matrix must contain all four layers")
    required_tokens = {"Cofactor-gated validation", "cofactor-before-validation ordering"}
    matrix_tokens = {item for layer in layers if isinstance(layer, dict) for item in layer.get("required_mechanisms", [])}
    if not required_tokens <= matrix_tokens:
        errors.append("v2.12 isomorphism matrix is missing cofactor-gated ordering requirements")

    episode_dirs = sorted(path for path in OUTPUT_DIR.glob("episode_*") if path.is_dir())
    if len(episode_dirs) < int(campaign.get("executed_episode_count", 0) or 0):
        errors.append("episode directories must cover all executed episodes")
    for episode_dir in episode_dirs:
        meta, e = load_json(episode_dir / "episode_metadata.json")
        errors.extend(e)
        candidate = str(meta.get("candidate") or "")
        for name in REQUIRED_EPISODE:
            path = episode_dir / name
            if not path.exists():
                errors.append(f"missing v2.12 episode artifact: {path}")
        if candidate.startswith("PySnooper"):
            for name in ["python_toolbox_recovery_result.json", "v2_11_patch_revalidation_result.json", "pysnooper_patch_validation_result.json"]:
                if not (episode_dir / name).exists():
                    errors.append(f"missing PySnooper-specific v2.12 artifact: {episode_dir / name}")
        errors.extend(verify_manifest(episode_dir))

    decision, e = load_json(OUTPUT_DIR / "decision_report.json")
    errors.extend(e)
    vocabulary, e = load_json(OUTPUT_DIR / "classification_vocabulary_check.json")
    errors.extend(e)
    classifications = {record.get("classification") for record in decision.get("records", []) if isinstance(record, dict)}
    allowed = set(vocabulary.get("allowed_vocabulary") or [])
    if classifications and allowed and not classifications <= allowed:
        errors.append(f"decision classifications outside vocabulary: {sorted(classifications - allowed)}")

    summary_text = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    if "## v2.12 Dependency Cofactor Recovery and Locked Non-Ansible Repair Validation Lane" not in summary_text:
        errors.append("shareable summary missing v2.12 block")

    if errors:
        print("v2.12 dependency cofactor recovery audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.12 dependency cofactor recovery audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
