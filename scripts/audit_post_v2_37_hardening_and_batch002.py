from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.core.manifests import verify_manifest
from controllergate.core.artifact_hygiene import audit_artifact_payload

POST_DIR = Path("outputs/post_v2_37_hardening_001")
BATCH_DIR = Path("outputs/clean_replication_batch_002")
BATCH003_DIR = Path("outputs/clean_replication_batch_003")
BATCH004_DIR = Path("outputs/clean_replication_batch_004")
PAYLOAD_DIR = Path("artifact_payload/post_v2_37_hardening_batch004_dual_track_challenge")

POST_REQUIRED = [
    "workspace_transport_integrity_policy.json",
    "post_v2_37_hardening_artifact_verification.json",
    "artifact_pycache_payload_audit.json",
    "batch002_mixed_mode_failure_diagnosis.json",
    "corrected_batch002_artifact_verification.json",
    "batch002_real_acquisition_gap_diagnosis.json",
    "real_leads_artifact_verification.json",
    "batch002_environment_resolution_gap_diagnosis.json",
    "batch002_environment_resolution_artifact_verification.json",
    "batch002_repair_generation_gap_diagnosis.json",
    "batch002_repair_generation_artifact_verification.json",
    "second_external_repair_ingest_summary.json",
    "repair_episode_registry_update_report.json",
    "artifact_packaging_correction_report.json",
    "artifact_payload_manifest_report.json",
    "readme_status_update_report.json",
    "public_docs_accuracy_audit.json",
    "operational_gate_matrix_status.json",
    "public_language_audit_expanded.json",
    "workspace_transport_integrity_log.json",
    "transport_boundary_audit.json",
    "homeostasis_risk_policy.json",
    "homeostasis_risk_state.json",
    "starvation_pressure_log.json",
    "version_sprawl_pressure_log.json",
    "public_claim_pressure_log.json",
    "bounded_exploration_budget_policy.json",
    "bounded_exploration_budget_trace.json",
    "context_boundary_policy.json",
    "context_boundary_map.json",
    "context_boundary_rejection_ledger.json",
    "environment_normalization_policy.json",
    "environment_normalization_log.json",
    "issue_derived_evidence_class_policy.json",
    "issue_text_temporal_guard_policy.json",
    "issue_derived_latent_knowledge_risk_disclosure.json",
    "bugsinpy_relaxation_research_status.json",
    "operational_gate_completion_status.json",
    "v3_0_readiness_scorecard_update.json",
    "matched_null_artifact_verification.json",
    "third_external_repair_ingest_summary.json",
    "equal_performance_memory_claim_boundary.json",
    "matched_null_lessons_learned.json",
    "batch003_memory_challenge_artifact_verification.json",
    "batch003_challenge_candidate_failure_diagnosis.json",
    "native_vs_issue_derived_status_after_batch003.json",
    "final_report_post_v2_37_hardening_001.json",
    "consolidated_state_post_v2_37_hardening_001.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

BATCH004_REQUIRED = [
    "consolidated_state_clean_replication_batch_004.json",
    "batch004_dual_track_acquisition_policy.json",
    "native_challenge_acquisition_policy.json",
    "issue_derived_harness_policy.json",
    "context_boundary_pinning_policy.json",
    "homeostasis_risk_policy_batch004.json",
    "bounded_exploration_budget_batch004.json",
    "native_challenge_lead_pool.json",
    "native_challenge_attempts.json",
    "native_challenge_rejection_ledger.json",
    "native_challenge_verified_candidates.json",
    "issue_derived_lead_pool.json",
    "issue_derived_attempts.json",
    "issue_derived_rejection_ledger.json",
    "issue_derived_verified_candidates.json",
    "issue_text_temporal_guard_batch004.json",
    "issue_derived_latent_knowledge_risk_disclosure_batch004.json",
    "memory_enabled_run_results.json",
    "null_ensemble_run_results.json",
    "null_ensemble_summary.json",
    "matched_null_ensemble_separation_score_result.json",
    "memory_separation_claim_evaluation.json",
    "repair_successes.json",
    "native_issue_derived_count_separation.json",
    "claim_boundary.json",
    "homeostasis_risk_state.json",
    "bounded_exploration_budget_trace.json",
    "candidate_starvation_pressure_log.json",
    "context_boundary_map.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

BATCH003_REQUIRED = [
    "consolidated_state_clean_replication_batch_003.json",
    "matched_null_ensemble_policy.json",
    "matched_null_ensemble_seed_policy.json",
    "matched_null_ensemble_score_definition.json",
    "null_generation_audit.json",
    "memory_enabled_policy.json",
    "memory_disabled_policy.json",
    "challenge_candidate_acquisition_policy.json",
    "challenge_candidate_difficulty_band.json",
    "challenge_candidate_lead_pool.json",
    "challenge_candidate_attempts.json",
    "challenge_candidate_rejection_ledger.json",
    "candidate_verification_attempts.json",
    "verified_challenge_candidates.json",
    "challenge_candidate_admission_decisions.json",
    "repairability_basin_scores_batch003.csv",
    "memory_enabled_run_results.json",
    "null_ensemble_run_results.json",
    "null_ensemble_summary.json",
    "matched_null_ensemble_separation_score_result.json",
    "memory_separation_claim_evaluation.json",
    "repair_successes.json",
    "native_issue_derived_count_separation.json",
    "claim_boundary.json",
    "failure_memory_active_routing_audit.json",
    "failure_memory_marker_usage.json",
    "failure_memory_routing_delta.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

BATCH_REQUIRED = [
    "consolidated_state_clean_replication_batch_002.json",
    "campaign_summary.md",
    "candidate_source_mode_trace.json",
    "lead_pool_intake_report.json",
    "curated_seed_intake_report.json",
    "metadata_probe_attempts.json",
    "issue_derived_attempts.json",
    "environment_resolution_attempts.json",
    "environment_resolution_policy.json",
    "environment_failure_classification.json",
    "dependency_install_logs_manifest.json",
    "candidate_verification_attempts.json",
    "candidate_rejection_ledger.json",
    "verified_candidates.json",
    "repair_attempts.json",
    "repair_successes.json",
    "clean_repair_generation_policy.json",
    "verified_candidate_repair_queue.json",
    "repair_context_capsules.json",
    "patchable_source_subsets.json",
    "source_patch_generation_attempts.json",
    "patch_safety_results.json",
    "target_validation_results.json",
    "duplicate_replay_results.json",
    "no_overreach_regression_results.json",
    "source_context_handoff_audit.json",
    "generation_validation_reconciliation_trace.json",
    "structural_repair_routing_map.json",
    "stage_interface_contract.json",
    "repairability_basin_selection.json",
    "patchable_source_ranking.csv",
    "pre_generation_context_state_lock.json",
    "patch_context_alignment_audit.json",
    "post_patch_constraint_revalidation.json",
    "no_overreach_validation.json",
    "repair_generator_capability_status.json",
    "matched_null_results.json",
    "memory_lift_evaluation.json",
    "baseline_registry_snapshot_before_matched_null.json",
    "proof_chain_lock_for_second_repair.json",
    "second_repair_claim_boundary.json",
    "darker_stdin_filename_pre_repair_replay.json",
    "darker_stdin_filename_semantic_failure_signature.json",
    "darker_stdin_filename_structural_repair_routing_map.json",
    "darker_stdin_filename_patchable_source_subset.json",
    "darker_stdin_filename_pre_generation_context_state_lock.json",
    "darker_stdin_filename_stage_interface_contract.json",
    "failure_memory_weighting_policy.json",
    "failure_memory_status_code_taxonomy.json",
    "arm_a_active_failure_memory_weighting.json",
    "arm_a_failure_memory_weight_trace.json",
    "arm_b_memory_disabled_exclusion_audit.json",
    "arm_b_memory_exclusion_audit.json",
    "failure_memory_weight_delta_report.json",
    "arm_a_pre_generation_context_state_snapshot.json",
    "arm_b_pre_generation_context_state_snapshot.json",
    "arm_a_repair_intent_lock.json",
    "arm_b_repair_intent_lock.json",
    "matched_null_arm_a_memory_enabled_plan.json",
    "matched_null_arm_b_memory_disabled_plan.json",
    "matched_null_arm_a_results.json",
    "matched_null_arm_b_results.json",
    "arm_a_patch.diff",
    "arm_b_patch.diff",
    "arm_a_patch_sha256.txt",
    "arm_b_patch_sha256.txt",
    "arm_a_target_validation.json",
    "arm_b_target_validation.json",
    "arm_a_duplicate_replay.json",
    "arm_b_duplicate_replay.json",
    "arm_a_post_patch_constraint_revalidation.json",
    "arm_b_post_patch_constraint_revalidation.json",
    "arm_a_no_overreach_validation.json",
    "arm_b_no_overreach_validation.json",
    "post_patch_constraint_revalidation_darker_stdin_filename.json",
    "no_overreach_validation_darker_stdin_filename.json",
    "interlock_invariant_revalidation.json",
    "homeostasis_risk_state_matched_null.json",
    "bounded_exploration_budget_matched_null.json",
    "active_probe_escalation_trace.json",
    "matched_null_score_inputs.json",
    "matched_null_score_formula.json",
    "matched_null_score_audit.json",
    "matched_null_separation_score_result.json",
    "memory_lift_claim_evaluation.json",
    "null_generation_audit.json",
    "native_issue_derived_count_separation.json",
    "claim_boundary.json",
    "SHA256SUMS.txt",
]


def blocked_terms() -> list[str]:
    return [
        "chromo" + "somal",
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "RNA " + "primase",
        "Meta" + "-cell",
        "Klein " + "bottle",
        "Klein " + "twist",
        "Betti" + "-number",
        "res" + "onance",
    ]


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def require_files(root: Path, files: list[str]) -> list[str]:
    return [rel for rel in files if not (root / rel).is_file()]


def command_passes(command: list[str]) -> bool:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr)
    return completed.returncode == 0


def load_lead_pool(path: Path = Path("inputs/clean_replication_batch_002_lead_pool.json")) -> dict[str, object]:
    if not path.is_file():
        return {"status": "MISSING", "leads": [], "lead_count": 0}
    data = read_json(path)
    leads = data.get("leads", [])
    return {"status": "PASS", "leads": leads if isinstance(leads, list) else [], "lead_count": len(leads) if isinstance(leads, list) else 0}


def audit_real_acquisition_records(
    lead_pool: dict[str, object],
    metadata_attempts: list[dict[str, object]],
    issue_attempts: list[dict[str, object]],
    candidate_attempts: list[dict[str, object]],
    batch: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    leads = lead_pool.get("leads", [])
    if not isinstance(leads, list):
        leads = []
    native_leads = [
        lead
        for lead in leads
        if isinstance(lead, dict)
        and lead.get("allowed_candidate_class") in {"native", "either"}
        and lead.get("lead_type") in {"repo_metadata", "commit_hint"}
    ]
    if any("py_bugger_issue_65" in json.dumps(item, sort_keys=True) for item in [*leads, *candidate_attempts]):
        errors.append("py_bugger_issue_65 reused as a new lead")
    if not leads and batch.get("exact_blocker") != "clean_replication_batch_002_lead_pool_empty":
        errors.append("lead pool empty without clean_replication_batch_002_lead_pool_empty blocker")
    if metadata_attempts and all(item.get("repo") == "offline_local_metadata_lead_pool" for item in metadata_attempts):
        errors.append("metadata_probe placeholder pool counted as acquisition")
    if issue_attempts and all(item.get("issue_lead") == "offline_local_issue_lead_pool" for item in issue_attempts):
        errors.append("issue_derived placeholder pool counted as acquisition")
    if native_leads and not any(item.get("lead_id") for item in candidate_attempts):
        errors.append("no real lead_id appears in candidate verification attempts")
    if native_leads and not metadata_attempts:
        errors.append("native lead pool present but metadata_probe_attempts empty")
    if metadata_attempts:
        if any(item.get("git_clone_status") == "PASS" for item in metadata_attempts) and not any(item.get("checkout_attempted") is True for item in metadata_attempts):
            errors.append("metadata_probe clone passed but no checkout was attempted")
        if all(item.get("checkout_attempted") is False for item in metadata_attempts) and any(not item.get("blocker") for item in metadata_attempts):
            errors.append("metadata_probe checkout false for every lead without specific blockers")
        if any(item.get("lead_id") and item.get("git_clone_attempted") is not True for item in metadata_attempts):
            errors.append("real metadata lead missing git clone attempt")
    if any(item.get("mode") == "issue_derived" and not item.get("lead_id") for item in candidate_attempts):
        errors.append("issue_derived no-lead placeholder counted as real candidate verification attempt")
    allowed_blockers = {
        "clean_replication_batch_002_lead_pool_empty",
        "metadata_probe_network_unavailable",
        "metadata_probe_no_verified_candidates",
        "metadata_probe_no_verified_candidates_after_environment_resolution",
        "clean_replication_batch_002_no_repair_successes_after_environment_resolution",
        "issue_derived_no_safe_leads",
        "clean_replication_batch_002_no_verified_candidates",
        "environment_dependency_install_failed",
        "environment_dependency_undeclared",
        "environment_editable_install_failed",
        "environment_declared_extra_missing",
        "environment_python_version_incompatible",
        "environment_collection_failed_after_resolution",
        "clean_replication_batch_002_no_repair_successes_after_environment_resolution",
        "clean_repair_no_safe_source_patch_generated",
        "clean_repair_patch_safety_failed",
        "target_validation_failed",
        "duplicate_clean_replay_failed",
        "stage_interface_contract_failed",
        "source_context_handoff_failed",
        "no_patchable_source_subset",
        "repair_generation_ignored_structural_routing",
        "patch_context_alignment_failed",
        "post_patch_constraint_revalidation_failed",
        "no_overreach_new_failure_detected",
        "no_overreach_regression_environment_limited",
    }
    if batch.get("exact_blocker") is None and batch.get("status") == "PASS":
        return errors
    if batch.get("exact_blocker") not in allowed_blockers:
        errors.append(f"unexpected batch002 blocker: {batch.get('exact_blocker')}")
    return errors


def audit_environment_resolution_records(metadata_attempts: list[dict[str, object]], batch: dict[str, object]) -> list[str]:
    errors: list[str] = []
    real_metadata = [item for item in metadata_attempts if item.get("lead_id")]
    for item in real_metadata:
        if item.get("environment_resolution_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: environment_resolution_not_attempted")
        if item.get("environment_resolution_attempted") is True and not item.get("install_strategy_attempts"):
            errors.append(f"{item.get('lead_id')}: install strategy attempts missing")
        if item.get("environment_resolution_attempted") is True and item.get("import_probe_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: import probe not recorded")
        if item.get("collection_attempted") is True and item.get("environment_resolution_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: collection occurred before environment resolution")
        text = json.dumps(item, sort_keys=True)
        if ("ModuleNotFoundError" in text or "No module named" in text) and item.get("environment_resolution_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: ModuleNotFoundError accepted without environment resolution")
        if str(item.get("blocker", "")).startswith("metadata_probe_collection_failed"):
            errors.append(f"{item.get('lead_id')}: old collection blocker used after environment resolution")
        if item.get("environment_resolution_attempted") is True and item.get("blocker") == "metadata_probe_collection_failed":
            errors.append(f"{item.get('lead_id')}: candidate/environment failure not separated")
    allowed_after_environment = {
        "metadata_probe_no_verified_candidates_after_environment_resolution",
        "environment_dependency_install_failed",
        "environment_dependency_undeclared",
        "environment_editable_install_failed",
        "environment_declared_extra_missing",
        "environment_python_version_incompatible",
        "environment_collection_failed_after_resolution",
        "metadata_probe_network_unavailable",
        "clean_replication_batch_002_no_verified_candidates",
        "clean_replication_batch_002_no_repair_successes_after_environment_resolution",
    }
    if real_metadata and all(item.get("environment_resolution_attempted") is True for item in real_metadata):
        if batch.get("exact_blocker") is None and batch.get("status") == "PASS":
            return errors
        if batch.get("exact_blocker") not in allowed_after_environment:
            errors.append(f"batch blocker does not reflect environment-aware acquisition: {batch.get('exact_blocker')}")
    return errors


def audit_repair_generation_records(batch: dict[str, object]) -> list[str]:
    errors: list[str] = []
    verified = read_json(BATCH_DIR / "verified_candidates.json")
    queue = read_json(BATCH_DIR / "verified_candidate_repair_queue.json")
    routing = read_json(BATCH_DIR / "structural_repair_routing_map.json")
    capsules = read_json(BATCH_DIR / "repair_context_capsules.json")
    subsets = read_json(BATCH_DIR / "patchable_source_subsets.json")
    generation = read_json(BATCH_DIR / "source_patch_generation_attempts.json")
    safety = read_json(BATCH_DIR / "patch_safety_results.json")
    validation = read_json(BATCH_DIR / "target_validation_results.json")
    duplicate = read_json(BATCH_DIR / "duplicate_replay_results.json")
    handoff = read_json(BATCH_DIR / "source_context_handoff_audit.json")
    trace = read_json(BATCH_DIR / "generation_validation_reconciliation_trace.json")
    stage_contract = read_json(BATCH_DIR / "stage_interface_contract.json")
    basin = read_json(BATCH_DIR / "repairability_basin_selection.json")
    locks = read_json(BATCH_DIR / "pre_generation_context_state_lock.json")
    alignment = read_json(BATCH_DIR / "patch_context_alignment_audit.json")
    revalidation = read_json(BATCH_DIR / "post_patch_constraint_revalidation.json")
    overreach = read_json(BATCH_DIR / "no_overreach_validation.json")
    capability = read_json(BATCH_DIR / "repair_generator_capability_status.json")
    policy = read_json(BATCH_DIR / "clean_repair_generation_policy.json")
    ranking_csv = BATCH_DIR / "patchable_source_ranking.csv"
    if policy.get("status") != "PASS" or policy.get("fixed_later_gold_pr_patch_content_forbidden") is not True:
        errors.append("clean repair generation policy invalid")
    verified_native = [item for item in verified if item.get("decision") == "verified_native_candidate_pending_repair"]
    if len(verified_native) != 2:
        errors.append("two verified native candidates not preserved")
    if len(queue) != len(verified_native):
        errors.append("repair queue does not contain the verified native candidates")
    queued_ids = {item.get("candidate_id") for item in queue}
    if queued_ids != {"darker_non_ascii_drop_changes", "darker_stdin_filename"}:
        errors.append(f"unexpected repair queue candidate ids: {sorted(queued_ids)}")
    if not ranking_csv.is_file() or "candidate_id,file_path" not in ranking_csv.read_text(encoding="utf-8").splitlines()[0]:
        errors.append("patchable source ranking CSV missing or malformed")
    attempted_count = max(1, len(generation), len(capability))
    for collection, name in [
        (routing, "structural repair routing map"),
        (capsules, "repair context capsules"),
        (subsets, "patchable source subsets"),
        (stage_contract, "stage interface contract"),
        (basin, "repairability basin selection"),
        (locks, "pre-generation context-state lock"),
        (capability, "repair generator capability status"),
    ]:
        if not isinstance(collection, list) or len(collection) < attempted_count:
            errors.append(f"{name} missing for attempted candidates")
    for contract in stage_contract:
        if contract.get("status") != "PASS":
            errors.append(f"{contract.get('candidate_id')}: stage_interface_contract_failed")
    for lock in locks:
        if not lock.get("pre_generation_context_state_lock_hash"):
            errors.append(f"{lock.get('candidate_id')}: context-state lock hash missing")
        if not lock.get("allowed_source_files"):
            errors.append(f"{lock.get('candidate_id')}: context-state lock allowed source files missing")
        attestation = lock.get("forbidden_evidence_attestation", {})
        if any(attestation.get(key) is not False for key in ["fixed_commits_used", "later_commits_used", "pr_patch_contents_used", "gold_patches_used", "issue_solution_comments_used"]):
            errors.append(f"{lock.get('candidate_id')}: forbidden evidence attestation failed")
    for item in routing:
        if item.get("repair_routing_decision") != "admit_patchable_subset":
            errors.append(f"{item.get('candidate_id')}: no_patchable_source_subset")
        if not item.get("patchable_source_subset"):
            errors.append(f"{item.get('candidate_id')}: patchable source subset missing in routing")
    for item in subsets:
        paths = item.get("patchable_source_files", [])
        if item.get("status") != "PASS" or not paths:
            errors.append(f"{item.get('candidate_id')}: patchable source subset failed")
        for path in paths:
            if str(path).startswith(("tests/", "test/", "src/darker/tests/", "configs/", ".github/", "outputs/", "scripts/", "docs/")):
                errors.append(f"{item.get('candidate_id')}: forbidden patchable path {path}")
    generated_ids = {item.get("candidate_id") for item in generation}
    if not generated_ids.issubset(queued_ids):
        errors.append("patch generation occurred for an unverified candidate")
    for item in capability:
        if item.get("generator_invoked") is not True:
            errors.append(f"{item.get('candidate_id')}: clean_repair_generator_not_implemented")
        if item.get("blocker") == "clean_repair_generator_not_implemented":
            errors.append(f"{item.get('candidate_id')}: generator still reported no-op implementation")
    generated = [item for item in generation if item.get("patch_candidate_generated") is True]
    for item in generated:
        if item.get("candidate_id") not in queued_ids:
            errors.append("generated patch for candidate outside repair queue")
        if item.get("patch_sha256") is None:
            errors.append(f"{item.get('candidate_id')}: generated patch missing SHA256")
        for path in item.get("patch_file_paths", []):
            if str(path) not in next((lock.get("allowed_source_files", []) for lock in locks if lock.get("candidate_id") == item.get("candidate_id")), []):
                errors.append(f"{item.get('candidate_id')}: repair_generation_ignored_structural_routing")
    if generated and not safety:
        errors.append("patch generated without patch safety result")
    for item in safety:
        if item.get("status") != "PASS":
            errors.append(f"{item.get('candidate_id')}: clean_repair_patch_safety_failed")
        if item.get("tests_modified") is not False or item.get("support_files_modified") is not False or item.get("config_workflow_registry_audit_modified") is not False:
            errors.append(f"{item.get('candidate_id')}: forbidden file mutation in patch safety")
    if generated and not alignment:
        errors.append("patch generated without patch context alignment audit")
    for item in alignment:
        if item.get("status") != "PASS":
            errors.append(f"{item.get('candidate_id')}: patch_context_alignment_failed")
    for item in validation:
        if item.get("status") == "PASS" and item.get("exit_code") != 0:
            errors.append(f"{item.get('candidate_id')}: target validation PASS without exit status 0")
    for item in duplicate:
        if item.get("status") == "PASS" and (item.get("passes") != 3 or item.get("total") != 3):
            errors.append(f"{item.get('candidate_id')}: duplicate replay PASS without 3/3")
    for item in revalidation:
        if item.get("status") == "PASS" and item.get("same_patch_bytes_across_replays") is not True:
            errors.append(f"{item.get('candidate_id')}: post-patch revalidation missing same patch bytes")
    for item in overreach:
        if item.get("stronger_robustness_claim_allowed") is not False:
            errors.append(f"{item.get('candidate_id')}: no-overreach allowed stronger claim")
        if item.get("new_failures_detected") is not False:
            errors.append(f"{item.get('candidate_id')}: no_overreach_new_failure_detected")
    if generated and not handoff:
        errors.append("source context handoff audit missing for generated patch")
    for item in handoff:
        if not item.get("context_capsule_hash") or not item.get("patchable_subset_hash"):
            errors.append(f"{item.get('verified_candidate_id')}: source_context_handoff_failed")
    for item in trace:
        if item.get("verification_stage_status") != "PASS":
            errors.append(f"{item.get('candidate_id')}: reconciliation trace missing verification PASS")
    return errors


def audit_matched_null_records(batch: dict[str, object]) -> list[str]:
    errors: list[str] = []
    official_repair_artifact = read_json(POST_DIR / "batch002_repair_generation_artifact_verification.json")
    if official_repair_artifact.get("status") != "PASS":
        errors.append("repair-generation artifact verification not PASS")
    if official_repair_artifact.get("actual_sha256") != "64e6e0ec76bf05857aa03f1b5cd0608060e9bb114f1f74981608a3a45710d9b5":
        errors.append("repair-generation artifact SHA mismatch")
    second_summary = read_json(POST_DIR / "second_external_repair_ingest_summary.json")
    if second_summary.get("confirmed_external_native_repair_episode") != "darker_non_ascii_drop_changes":
        errors.append("second external repair ingest summary does not lock darker_non_ascii_drop_changes")
    registry_report = read_json(POST_DIR / "repair_episode_registry_update_report.json")
    if registry_report.get("status") != "PASS" or registry_report.get("candidate_id") != "darker_non_ascii_drop_changes":
        errors.append("second repair registry update report invalid")

    baseline = read_json(BATCH_DIR / "baseline_registry_snapshot_before_matched_null.json")
    proof = read_json(BATCH_DIR / "proof_chain_lock_for_second_repair.json")
    second_claim = read_json(BATCH_DIR / "second_repair_claim_boundary.json")
    if baseline.get("status") != "PASS":
        errors.append("baseline registry snapshot before matched-null missing PASS")
    if proof.get("status") != "PASS" or not proof.get("proof_chain_hash"):
        errors.append("proof-chain lock for second repair invalid")
    if second_claim.get("status") != "PASS" or second_claim.get("stronger_robustness_claim_allowed") is not False:
        errors.append("second repair claim boundary invalid")

    pre_replay = read_json(BATCH_DIR / "darker_stdin_filename_pre_repair_replay.json")
    semantic = read_json(BATCH_DIR / "darker_stdin_filename_semantic_failure_signature.json")
    routing = read_json(BATCH_DIR / "darker_stdin_filename_structural_repair_routing_map.json")
    subset = read_json(BATCH_DIR / "darker_stdin_filename_patchable_source_subset.json")
    lock = read_json(BATCH_DIR / "darker_stdin_filename_pre_generation_context_state_lock.json")
    stage = read_json(BATCH_DIR / "darker_stdin_filename_stage_interface_contract.json")
    if pre_replay.get("status") != "PRE_PATCH_FAILURE_OBSERVED":
        errors.append("darker_stdin_filename pre-repair replay was not reproduced")
    if semantic.get("status") != "PASS" or not semantic.get("semantic_failure_signature_hash"):
        errors.append("darker_stdin_filename semantic failure signature missing")
    if routing.get("repair_routing_decision") != "admit_patchable_subset":
        errors.append("darker_stdin_filename structural routing did not admit source subset")
    if subset.get("status") != "PASS" or "src/darker/config.py" not in subset.get("patchable_source_files", []):
        errors.append("darker_stdin_filename patchable source subset invalid")
    if not lock.get("pre_generation_context_state_lock_hash"):
        errors.append("darker_stdin_filename context-state lock missing")
    if stage.get("status") != "PASS":
        errors.append("darker_stdin_filename stage interface contract failed")

    taxonomy = read_json(BATCH_DIR / "failure_memory_status_code_taxonomy.json")
    arm_a_weight = read_json(BATCH_DIR / "arm_a_active_failure_memory_weighting.json")
    arm_b_exclusion = read_json(BATCH_DIR / "arm_b_memory_disabled_exclusion_audit.json")
    delta = read_json(BATCH_DIR / "failure_memory_weight_delta_report.json")
    if taxonomy.get("status") != "PASS" or not taxonomy.get("codes"):
        errors.append("failure-memory status-code taxonomy invalid")
    if arm_a_weight.get("status") != "PASS":
        errors.append("Arm A active failure-memory weighting missing PASS")
    if arm_a_weight.get("failure_memory_markers_passive") is True and batch.get("preliminary_single_candidate_memory_separation_evidence") is True:
        errors.append("passive memory markers produced preliminary memory separation claim")
    if arm_a_weight.get("failure_memory_markers_passive") is False and not arm_a_weight.get("routing_decisions_affected"):
        errors.append("Arm A weighting marked active without routing effect")
    if arm_b_exclusion.get("status") != "PASS":
        errors.append("Arm B memory exclusion audit failed")
    for forbidden in ["memory_ledger_opened", "successful_patch_bytes_opened", "successful_patch_rationales_opened", "memory_weighted_routing_applied"]:
        if arm_b_exclusion.get(forbidden) is not False:
            errors.append(f"Arm B contamination detected: {forbidden}")
    if delta.get("status") != "PASS":
        errors.append("failure-memory weight delta report invalid")

    arm_a = read_json(BATCH_DIR / "matched_null_arm_a_results.json")
    arm_b = read_json(BATCH_DIR / "matched_null_arm_b_results.json")
    for arm, name in [(arm_a, "Arm A"), (arm_b, "Arm B")]:
        if arm.get("candidate_id") != "darker_stdin_filename":
            errors.append(f"{name} candidate mismatch")
        if arm.get("repo_url") != "https://github.com/akaihola/darker":
            errors.append(f"{name} repo mismatch")
        if arm.get("commit_sha") != "6ecafca023a354fe7d9539d1d20bf10391bdb24a":
            errors.append(f"{name} commit mismatch")
        if arm.get("target_test_path") != "src/darker/tests/test_main_stdin_filename.py":
            errors.append(f"{name} target test mismatch")
        if arm.get("patch_generated") is not True or arm.get("patch_authorized") is not True:
            errors.append(f"{name} patch was not generated and authorized")
        if arm.get("patch_safety", {}).get("status") != "PASS":
            errors.append(f"{name} patch safety failed")
        if arm.get("target_validation_status") != "PASS":
            errors.append(f"{name} target validation failed")
        if arm.get("duplicate_replay_status") != "PASS":
            errors.append(f"{name} duplicate replay failed")
        if arm.get("no_overreach_status") != "PASS":
            errors.append(f"{name} no-overreach failed")
    for path_name in [
        "arm_a_pre_generation_context_state_snapshot.json",
        "arm_b_pre_generation_context_state_snapshot.json",
        "arm_a_repair_intent_lock.json",
        "arm_b_repair_intent_lock.json",
    ]:
        data = read_json(BATCH_DIR / path_name)
        if data.get("status") != "PASS":
            errors.append(f"{path_name} did not PASS")
    for path_name in [
        "arm_a_post_patch_constraint_revalidation.json",
        "arm_b_post_patch_constraint_revalidation.json",
        "arm_a_no_overreach_validation.json",
        "arm_b_no_overreach_validation.json",
    ]:
        data = read_json(BATCH_DIR / path_name)
        if data.get("status") != "PASS":
            errors.append(f"{path_name} did not PASS")
    interlock = read_json(BATCH_DIR / "interlock_invariant_revalidation.json")
    if not isinstance(interlock, list) or not interlock or any(item.get("status") != "PASS" for item in interlock if item):
        errors.append("interlock invariant revalidation failed")
    homeostasis = read_json(BATCH_DIR / "homeostasis_risk_state_matched_null.json")
    budget = read_json(BATCH_DIR / "bounded_exploration_budget_matched_null.json")
    if homeostasis.get("status") != "PASS":
        errors.append("matched-null homeostasis risk state failed")
    if budget.get("status") != "PASS":
        errors.append("matched-null bounded exploration budget failed")
    score_inputs = read_json(BATCH_DIR / "matched_null_score_inputs.json")
    score_formula = read_json(BATCH_DIR / "matched_null_score_formula.json")
    score_audit = read_json(BATCH_DIR / "matched_null_score_audit.json")
    score = read_json(BATCH_DIR / "matched_null_separation_score_result.json")
    if score_inputs.get("status") != "PASS" or score_formula.get("status") != "PASS" or score_audit.get("status") != "PASS":
        errors.append("matched-null score evidence invalid")
    if score.get("matched_null_separation_score") != 0.0:
        errors.append("expected equal-performance matched-null score of 0.0")
    if score.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("preliminary memory separation overclaimed")
    memory_claim = read_json(BATCH_DIR / "memory_lift_claim_evaluation.json")
    if memory_claim.get("full_memory_lift_status") != "undemonstrated":
        errors.append("full memory lift overclaimed")
    if memory_claim.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("memory lift claim evaluation overclaimed preliminary evidence")
    registry = read_json(Path("configs/external_repair_episode_registry.json"))
    episodes = registry.get("episodes", [])
    if not any(isinstance(item, dict) and item.get("candidate_id") == "darker_stdin_filename" and item.get("scoreable") is True for item in episodes):
        errors.append("darker_stdin_filename missing from repair episode registry")
    if batch.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("full scoring boundary changed")
    if batch.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("self-maintaining software overclaim")
    if batch.get("issue_derived_repair_successes_count") != 0:
        errors.append("issue-derived repairs incremented unexpectedly")
    return errors


def audit_phase_a_ingest_records() -> list[str]:
    errors: list[str] = []
    verification = read_json(POST_DIR / "matched_null_artifact_verification.json")
    ingest = read_json(POST_DIR / "third_external_repair_ingest_summary.json")
    equal = read_json(POST_DIR / "equal_performance_memory_claim_boundary.json")
    lessons = read_json(POST_DIR / "matched_null_lessons_learned.json")
    if verification.get("status") != "PASS":
        errors.append("matched-null artifact verification not PASS")
    if verification.get("actual_sha256") != "8124be2c04533b0b22e5136c683bfdf2f457c961baefff8f19c55860df61532d":
        errors.append("matched-null artifact SHA mismatch")
    if verification.get("actual_size_bytes") not in {145764, "145764"}:
        errors.append("matched-null artifact size mismatch")
    if verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0:
        errors.append("matched-null artifact path safety failed")
    if ingest.get("confirmed_external_native_repair_episode") != "darker_stdin_filename":
        errors.append("third external repair ingest summary invalid")
    if equal.get("matched_null_separation_score") != 0.0:
        errors.append("equal-performance boundary score changed")
    if equal.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("equal-performance boundary overclaimed memory separation")
    if equal.get("memory_lift") != "undemonstrated_equal_performance":
        errors.append("equal-performance memory status mismatch")
    if lessons.get("status") != "PASS":
        errors.append("matched-null lessons record not PASS")
    batch003 = read_json(POST_DIR / "batch003_memory_challenge_artifact_verification.json")
    diagnosis = read_json(POST_DIR / "batch003_challenge_candidate_failure_diagnosis.json")
    native_issue = read_json(POST_DIR / "native_vs_issue_derived_status_after_batch003.json")
    if batch003.get("status") != "PASS":
        errors.append("batch003 memory-challenge artifact verification not PASS")
    if batch003.get("actual_sha256") != "5bbdd68ff31d4f2311d38c92d553c9aa6499e6c1ddf4bb7054aa4a6d02f6613d":
        errors.append("batch003 artifact SHA mismatch")
    if batch003.get("actual_size_bytes") not in {166649, "166649"}:
        errors.append("batch003 artifact size mismatch")
    if batch003.get("zip_entry_count") != 166:
        errors.append("batch003 artifact entry count mismatch")
    if batch003.get("challenge_candidates_attempted_count") != 3 or batch003.get("challenge_candidates_verified_count") != 0:
        errors.append("batch003 challenge counts mismatch")
    if batch003.get("exact_blocker") != "clean_replication_batch_003_no_verified_challenge_candidate":
        errors.append("batch003 blocker mismatch in official verification")
    if diagnosis.get("matched_null_ensemble_run_status") != "NOT_RUN":
        errors.append("batch003 diagnosis says ensemble ran")
    if diagnosis.get("memory_separation_claimed") is not False:
        errors.append("batch003 diagnosis overclaimed memory separation")
    if native_issue.get("confirmed_external_native_repair_episodes") != 3 or native_issue.get("confirmed_issue_derived_repair_episodes") != 0:
        errors.append("batch003 native/issue-derived carry-forward counts invalid")
    return errors


def audit_batch004_records() -> list[str]:
    errors: list[str] = []
    state = read_json(BATCH004_DIR / "consolidated_state_clean_replication_batch_004.json")
    policy = read_json(BATCH004_DIR / "batch004_dual_track_acquisition_policy.json")
    native_policy = read_json(BATCH004_DIR / "native_challenge_acquisition_policy.json")
    issue_policy = read_json(BATCH004_DIR / "issue_derived_harness_policy.json")
    native_leads = read_json(BATCH004_DIR / "native_challenge_lead_pool.json")
    native_attempts = read_json(BATCH004_DIR / "native_challenge_attempts.json")
    native_verified = read_json(BATCH004_DIR / "native_challenge_verified_candidates.json")
    issue_pool = read_json(BATCH004_DIR / "issue_derived_lead_pool.json")
    issue_attempts = read_json(BATCH004_DIR / "issue_derived_attempts.json")
    issue_verified = read_json(BATCH004_DIR / "issue_derived_verified_candidates.json")
    temporal = read_json(BATCH004_DIR / "issue_text_temporal_guard_batch004.json")
    latent = read_json(BATCH004_DIR / "issue_derived_latent_knowledge_risk_disclosure_batch004.json")
    memory_run = read_json(BATCH004_DIR / "memory_enabled_run_results.json")
    null_runs = read_json(BATCH004_DIR / "null_ensemble_run_results.json")
    null_summary = read_json(BATCH004_DIR / "null_ensemble_summary.json")
    score = read_json(BATCH004_DIR / "matched_null_ensemble_separation_score_result.json")
    claim = read_json(BATCH004_DIR / "memory_separation_claim_evaluation.json")
    repairs = read_json(BATCH004_DIR / "repair_successes.json")
    separation = read_json(BATCH004_DIR / "native_issue_derived_count_separation.json")
    boundary = read_json(BATCH004_DIR / "claim_boundary.json")
    risk = read_json(BATCH004_DIR / "homeostasis_risk_state.json")
    budget = read_json(BATCH004_DIR / "bounded_exploration_budget_trace.json")
    context = read_json(BATCH004_DIR / "context_boundary_map.json")
    if policy.get("track_order") != ["native_challenge_acquisition", "issue_derived_ephemeral_reproduction_harness_fallback"]:
        errors.append("batch004 track order invalid")
    if policy.get("issue_derived_fallback_only_after_native_failure") is not True:
        errors.append("issue-derived fallback not gated on native failure")
    if state.get("native_track_attempted_first") is not True or state.get("issue_derived_fallback_activated") is not True:
        errors.append("batch004 did not record native-first then fallback")
    if state.get("exact_blocker") != "batch004_no_native_or_issue_derived_challenge_candidate_verified":
        errors.append("batch004 exact blocker mismatch")
    if set(native_policy.get("already_repaired_candidate_ids_forbidden", [])) != {"py_bugger_issue_65", "darker_non_ascii_drop_changes", "darker_stdin_filename"}:
        errors.append("batch004 repaired-candidate exclusion invalid")
    if native_leads.get("lead_count") != 1:
        errors.append("batch004 native lead pool count invalid")
    if not isinstance(native_attempts, list) or len(native_attempts) != 1:
        errors.append("batch004 native attempts invalid")
    else:
        attempt = native_attempts[0]
        if attempt.get("candidate_id") != "darker_skip_glob_failing_test":
            errors.append("batch004 did not retry darker_skip_glob lead")
        if attempt.get("prior_blocker") != "command_cannot_collect_target":
            errors.append("batch004 native attempt prior blocker invalid")
        required_flags = [
            "environment_resolution_attempted_in_prior_evidence",
            "target_test_file_exists_in_prior_evidence",
            "file_collection_attempted",
            "project_pytest_invocation_considered",
            "safe_pythonpath_layout_considered",
            "ast_node_discovery_attempted",
            "command_cannot_collect_target_finalized_after_improved_collection",
        ]
        for flag in required_flags:
            if attempt.get(flag) is not True:
                errors.append(f"batch004 native attempt missing improved collection flag {flag}")
        if attempt.get("node_level_command_attempted_count", 0) < 1 and attempt.get("node_level_command_safely_blocked") is not True:
            errors.append("batch004 native attempt rejected without node-level attempt or safe block")
        if attempt.get("fixed_later_gold_pr_patch_content_used") is not False:
            errors.append("batch004 native attempt used forbidden patch evidence")
    if native_verified != []:
        errors.append("batch004 should not have native verified candidates")
    if issue_policy.get("increments_native_count") is not False:
        errors.append("issue-derived policy increments native count")
    if issue_policy.get("issue_text_hash_required_if_used") is not True or issue_policy.get("generated_harness_hash_required_if_used") is not True:
        errors.append("issue-derived hash requirements missing")
    if issue_pool.get("lead_count") != 0:
        errors.append("batch004 issue-derived lead pool unexpectedly non-empty")
    if not isinstance(issue_attempts, list) or not issue_attempts:
        errors.append("batch004 issue-derived fallback attempt missing")
    else:
        issue_attempt = issue_attempts[0]
        if issue_attempt.get("fallback_activated_after_native_failure") is not True:
            errors.append("issue-derived fallback not activated after native failure")
        if issue_attempt.get("candidate_class") != "issue_derived_reproduction_candidate":
            errors.append("issue-derived candidate class invalid")
        if issue_attempt.get("harness_generation_attempted") is not False:
            errors.append("issue-derived harness generated without safe lead")
        if issue_attempt.get("issue_text_hash") is not None or issue_attempt.get("generated_harness_hash") is not None:
            errors.append("issue-derived hashes recorded despite no harness")
        if issue_attempt.get("fixed_later_gold_pr_patch_content_used") is not False:
            errors.append("issue-derived attempt used forbidden patch evidence")
    if issue_verified != []:
        errors.append("batch004 should not have issue-derived verified candidates")
    if temporal.get("issue_text_hash_required_if_harness_used") is not True or temporal.get("solution_guidance_forbidden") is not True:
        errors.append("issue temporal guard invalid")
    if latent.get("cryptographic_absence_of_latent_knowledge_claimed") is not False:
        errors.append("latent knowledge disclosure overclaimed")
    if memory_run.get("status") != "NOT_RUN" or null_summary.get("status") != "NOT_RUN" or null_runs != []:
        errors.append("batch004 repair/null ensemble ran without verified candidate")
    if score.get("status") != "NOT_COMPUTED" or score.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch004 matched-null score overclaimed")
    if claim.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch004 memory claim overclaimed")
    if repairs != []:
        errors.append("batch004 repair successes should be empty")
    if separation.get("issue_derived_repairs_count_as_native") is not False:
        errors.append("batch004 issue-derived counts as native")
    if boundary.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("batch004 full scoring changed")
    if boundary.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch004 self-maintaining software overclaim")
    if boundary.get("technical_validation_release_readiness") != "not_ready":
        errors.append("batch004 release readiness overclaim")
    if risk.get("status") != "PASS" or budget.get("status") != "PASS" or context.get("status") != "PASS":
        errors.append("batch004 risk/budget/context records invalid")
    return errors


def audit_batch003_records() -> list[str]:
    errors: list[str] = []
    state = read_json(BATCH003_DIR / "consolidated_state_clean_replication_batch_003.json")
    policy = read_json(BATCH003_DIR / "matched_null_ensemble_policy.json")
    seed_policy = read_json(BATCH003_DIR / "matched_null_ensemble_seed_policy.json")
    score_definition = read_json(BATCH003_DIR / "matched_null_ensemble_score_definition.json")
    null_audit = read_json(BATCH003_DIR / "null_generation_audit.json")
    mem_enabled = read_json(BATCH003_DIR / "memory_enabled_policy.json")
    mem_disabled = read_json(BATCH003_DIR / "memory_disabled_policy.json")
    acquisition = read_json(BATCH003_DIR / "challenge_candidate_acquisition_policy.json")
    difficulty = read_json(BATCH003_DIR / "challenge_candidate_difficulty_band.json")
    lead_pool = read_json(BATCH003_DIR / "challenge_candidate_lead_pool.json")
    attempts = read_json(BATCH003_DIR / "challenge_candidate_attempts.json")
    verified = read_json(BATCH003_DIR / "verified_challenge_candidates.json")
    admissions = read_json(BATCH003_DIR / "challenge_candidate_admission_decisions.json")
    memory_run = read_json(BATCH003_DIR / "memory_enabled_run_results.json")
    null_runs = read_json(BATCH003_DIR / "null_ensemble_run_results.json")
    null_summary = read_json(BATCH003_DIR / "null_ensemble_summary.json")
    score = read_json(BATCH003_DIR / "matched_null_ensemble_separation_score_result.json")
    claim = read_json(BATCH003_DIR / "memory_separation_claim_evaluation.json")
    repair_successes = read_json(BATCH003_DIR / "repair_successes.json")
    separation = read_json(BATCH003_DIR / "native_issue_derived_count_separation.json")
    boundary = read_json(BATCH003_DIR / "claim_boundary.json")
    routing_audit = read_json(BATCH003_DIR / "failure_memory_active_routing_audit.json")
    marker_usage = read_json(BATCH003_DIR / "failure_memory_marker_usage.json")
    routing_delta = read_json(BATCH003_DIR / "failure_memory_routing_delta.json")
    if policy.get("status") != "PASS" or int(policy.get("null_ensemble_size", 0)) < 5:
        errors.append("matched-null ensemble policy invalid")
    if seed_policy.get("status") != "PASS" or len(seed_policy.get("seeds", [])) < 5:
        errors.append("matched-null seed policy invalid")
    for seed in seed_policy.get("seeds", []):
        if seed.get("memory_enabled") is not False:
            errors.append("null ensemble seed is not memory-disabled")
        if seed.get("candidate_commit_command_environment_patch_caps_changed") is not False:
            errors.append("null ensemble seed changed runtime invariants")
    if null_audit.get("status") != "PASS":
        errors.append("null generation audit failed")
    if mem_enabled.get("successful_patch_bytes_read") is not False or mem_enabled.get("prior_patches_copied") is not False:
        errors.append("memory-enabled policy allows prior patch leakage")
    if mem_disabled.get("may_read_failure_memory_weight_ledger") is not False:
        errors.append("memory-disabled policy can read memory ledger")
    if score_definition.get("full_memory_lift_claim_allowed") is not False:
        errors.append("score definition allows full memory-lift claim")
    forbidden_reuse = {"py_bugger_issue_65", "darker_non_ascii_drop_changes", "darker_stdin_filename"}
    if set(acquisition.get("candidate_ids_forbidden_as_new", [])) != forbidden_reuse:
        errors.append("batch003 forbidden candidate reuse set invalid")
    if any(item.get("candidate_id") in forbidden_reuse for item in attempts):
        errors.append("repaired candidate reused in batch003 attempts")
    if any(item.get("candidate_id") in forbidden_reuse for item in admissions):
        errors.append("repaired candidate reused in batch003 admissions")
    if lead_pool.get("lead_count") != len(attempts):
        errors.append("challenge lead pool count does not align with attempts")
    if difficulty.get("status") != "PASS" or not difficulty.get("records"):
        errors.append("challenge difficulty-band records missing")
    if len(admissions) != len(attempts):
        errors.append("admission decisions do not align with attempts")
    if verified:
        errors.append("batch003 verified a challenge candidate but repair experiment records are still NOT_RUN")
    if state.get("exact_blocker") != "clean_replication_batch_003_no_verified_challenge_candidate":
        errors.append("batch003 blocker mismatch")
    if memory_run.get("status") != "NOT_RUN" or null_summary.get("status") != "NOT_RUN":
        errors.append("batch003 experiment ran without a verified challenge candidate")
    if null_runs != []:
        errors.append("null ensemble run results should be empty when blocked before repair experiment")
    if score.get("status") != "NOT_COMPUTED" or score.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch003 score overclaimed or computed without comparable runs")
    if claim.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch003 claim evaluation overclaimed preliminary evidence")
    if claim.get("memory_lift") != "undemonstrated_equal_performance":
        errors.append("batch003 memory status mismatch")
    if repair_successes != []:
        errors.append("batch003 repair successes must be empty when no challenge candidate verifies")
    if separation.get("issue_derived_repairs_count_as_native") is not False:
        errors.append("issue-derived count separation invalid")
    if boundary.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("batch003 full scoring boundary changed")
    if boundary.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch003 self-maintaining software overclaim")
    if boundary.get("technical_validation_release_readiness") != "not_ready":
        errors.append("batch003 release readiness overclaim")
    if routing_audit.get("status") != "PASS" or marker_usage.get("memory_ledger_loaded") is not True:
        errors.append("failure-memory active routing audit invalid")
    if routing_delta.get("routing_delta_active") is not False or routing_delta.get("blocker") != "no_relevant_failure_memory_available":
        errors.append("batch003 routing delta should be passive without a verified challenge candidate")
    csv_header = (BATCH003_DIR / "repairability_basin_scores_batch003.csv").read_text(encoding="utf-8").splitlines()[0]
    if "repairability_score" not in csv_header or "admission_decision" not in csv_header:
        errors.append("batch003 repairability CSV malformed")
    return errors


def public_language_hits() -> list[str]:
    paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/claim_boundaries.md"),
        Path("docs/public_release_readiness.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/replication_protocol.md"),
        Path("docs/evidence_model.md"),
        Path("docs/operational_gate_matrix.md"),
        Path("configs/operational_gate_matrix.json"),
        Path("configs/clean_replication_batch_003.json"),
        Path("configs/clean_replication_batch_004.json"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path(".github/workflows/post_v2_37_hardening_and_batch002.yml"),
    ]
    hits: list[str] = []
    for path in paths:
        if not path.is_file():
            hits.append(f"missing:{path.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        for term in blocked_terms():
            if term in text:
                hits.append(f"{path.as_posix()}:{term}")
    return hits


def main() -> int:
    missing = (
        require_files(POST_DIR, POST_REQUIRED)
        + require_files(BATCH_DIR, BATCH_REQUIRED)
        + require_files(BATCH003_DIR, BATCH003_REQUIRED)
        + require_files(BATCH004_DIR, BATCH004_REQUIRED)
    )
    if missing:
        return fail(f"missing required files: {missing}")
    if verify_manifest(POST_DIR)["status"] != "PASS":
        return fail("post hardening manifest mismatch")
    if verify_manifest(BATCH_DIR)["status"] != "PASS":
        return fail("batch002 manifest mismatch")
    if verify_manifest(BATCH003_DIR)["status"] != "PASS":
        return fail("batch003 manifest mismatch")
    if verify_manifest(BATCH004_DIR)["status"] != "PASS":
        return fail("batch004 manifest mismatch")
    if not command_passes([sys.executable, "-m", "pytest", "tests/core", "-q"]):
        return fail("core tests failed")
    if not command_passes([sys.executable, "scripts/audit_v2_37_core_consolidation_and_clean_replication.py"]):
        return fail("v2.37 audit failed")

    records = read_json(POST_DIR / "workspace_transport_integrity_log.json").get("transfer_records")
    if not isinstance(records, list):
        return fail("transport integrity log invalid")
    for record in records:
        if not isinstance(record, dict):
            return fail("transport record malformed")
        for field in ["source_path", "destination_path", "source_sha256", "destination_sha256", "transfer_reason", "allowlist_class", "transport_decision"]:
            if not record.get(field):
                return fail(f"transport record missing {field}")
        if record.get("transport_decision") != "PASS":
            return fail("transport_integrity_breach")

    if read_json(POST_DIR / "transport_boundary_audit.json").get("forbidden_payload_count") != 0:
        return fail("forbidden payload recorded")
    if read_json(POST_DIR / "bounded_exploration_budget_trace.json").get("status") != "PASS":
        return fail("bounded exploration budget trace blocked unexpectedly")
    if read_json(POST_DIR / "environment_normalization_log.json").get("status") != "PASS":
        return fail("environment normalization unsafe")
    if read_json(POST_DIR / "issue_derived_evidence_class_policy.json").get("increments_native_count") is not False:
        return fail("issue-derived evidence class increments native count")
    if read_json(POST_DIR / "bugsinpy_relaxation_research_status.json").get("global_block_active") is not True:
        return fail("BugsInPy global block relaxed")
    official = read_json(POST_DIR / "post_v2_37_hardening_artifact_verification.json")
    if official.get("status") != "PASS":
        return fail("post-v2.37 artifact verification not PASS")
    if official.get("zip_sha256") != "6e0dcb44607dd8a23661b7bff30448e36db561477e99d2bee0689494cb505f1b":
        return fail("post-v2.37 artifact SHA mismatch")
    pycache_audit = read_json(POST_DIR / "artifact_pycache_payload_audit.json")
    if pycache_audit.get("pycache_pyc_payload_count") != 26:
        return fail("expected prior artifact cache payload audit mismatch")
    diagnosis = read_json(POST_DIR / "batch002_mixed_mode_failure_diagnosis.json")
    if diagnosis.get("metadata_probe_attempted") is not False or diagnosis.get("issue_derived_fallback_attempted") is not False:
        return fail("batch002 prior failure diagnosis invalid")
    packaging = read_json(POST_DIR / "artifact_packaging_correction_report.json")
    if packaging.get("status") != "PASS":
        return fail("artifact packaging correction report not PASS")
    manifest_report = read_json(POST_DIR / "artifact_payload_manifest_report.json")
    if manifest_report.get("status") != "PASS" or manifest_report.get("cache_payload_count") != 0:
        return fail("artifact payload manifest report invalid")
    readme_report = read_json(POST_DIR / "readme_status_update_report.json")
    docs_report = read_json(POST_DIR / "public_docs_accuracy_audit.json")
    matrix_status = read_json(POST_DIR / "operational_gate_matrix_status.json")
    language_expanded = read_json(POST_DIR / "public_language_audit_expanded.json")
    env_artifact = read_json(POST_DIR / "batch002_environment_resolution_artifact_verification.json")
    repair_gap = read_json(POST_DIR / "batch002_repair_generation_gap_diagnosis.json")
    if env_artifact.get("status") != "PASS" or env_artifact.get("sha256_match") is not True:
        return fail("environment-resolution artifact verification not PASS")
    if repair_gap.get("two_native_candidates_verified") is not True or repair_gap.get("immediate_blocker") != "clean_protocol_source_patch_generation_source_context_handoff":
        return fail("repair generation gap diagnosis invalid")
    if readme_report.get("status") != "PASS":
        return fail("README status update report failed")
    if docs_report.get("status") != "PASS":
        return fail("public docs accuracy audit failed")
    if matrix_status.get("status") != "PASS" or int(matrix_status.get("gate_count", 0)) < 26:
        return fail("operational gate matrix status failed")
    if language_expanded.get("status") != "PASS":
        return fail("expanded public language audit failed")
    phase_a_errors = audit_phase_a_ingest_records()
    if phase_a_errors:
        return fail(f"phase A ingest audit failed: {phase_a_errors}")
    payload_audit = audit_artifact_payload(PAYLOAD_DIR)
    if payload_audit["status"] != "PASS":
        return fail(f"artifact payload hygiene failed: {payload_audit}")

    batch = read_json(BATCH_DIR / "consolidated_state_clean_replication_batch_002.json")
    trace = read_json(BATCH_DIR / "candidate_source_mode_trace.json")
    trace_by_mode = {item.get("mode"): item for item in trace if isinstance(item, dict)}
    if trace_by_mode.get("curated_seed", {}).get("attempted") is not True:
        return fail("curated_seed not attempted")
    if trace_by_mode.get("metadata_probe", {}).get("attempted") is not True:
        return fail("metadata_probe not attempted")
    if trace_by_mode.get("issue_derived", {}).get("attempted") is not True:
        return fail("issue_derived fallback not attempted")
    attempts = read_json(BATCH_DIR / "candidate_verification_attempts.json")
    if not isinstance(attempts, list) or not attempts:
        return fail("candidate_verification_attempts must not be empty when modes are enabled")
    if any("py_bugger_issue_65" in json.dumps(item, sort_keys=True) for item in attempts):
        return fail("py_bugger_issue_65 reused as a new candidate")
    metadata_attempts = read_json(BATCH_DIR / "metadata_probe_attempts.json")
    issue_attempts = read_json(BATCH_DIR / "issue_derived_attempts.json")
    if not metadata_attempts and batch.get("exact_blocker") != "clean_replication_batch_002_lead_pool_empty":
        return fail("metadata probe attempt record invalid")
    if not issue_attempts and batch.get("exact_blocker") != "clean_replication_batch_002_lead_pool_empty":
        return fail("issue-derived attempt record invalid")
    real_acquisition_errors = audit_real_acquisition_records(load_lead_pool(), metadata_attempts, issue_attempts, attempts, batch)
    if real_acquisition_errors:
        return fail(f"real acquisition audit failed: {real_acquisition_errors}")
    env_attempts = read_json(BATCH_DIR / "environment_resolution_attempts.json")
    env_policy = read_json(BATCH_DIR / "environment_resolution_policy.json")
    env_classification = read_json(BATCH_DIR / "environment_failure_classification.json")
    install_manifest = read_json(BATCH_DIR / "dependency_install_logs_manifest.json")
    if env_policy.get("status") != "PASS" or env_policy.get("undeclared_arbitrary_dependency_install_allowed") is not False:
        return fail("environment resolution policy invalid")
    if not isinstance(env_attempts, list) or len(env_attempts) != len(metadata_attempts):
        return fail("environment resolution attempts do not align with metadata attempts")
    if not isinstance(env_classification, list) or not isinstance(install_manifest, list):
        return fail("environment classification or install log manifest invalid")
    environment_errors = audit_environment_resolution_records(metadata_attempts, batch)
    if environment_errors:
        return fail(f"environment resolution audit failed: {environment_errors}")
    repair_errors = audit_repair_generation_records(batch)
    if repair_errors:
        return fail(f"repair generation audit failed: {repair_errors}")
    matched_null_errors = audit_matched_null_records(batch)
    if matched_null_errors:
        return fail(f"matched-null audit failed: {matched_null_errors}")
    batch003_errors = audit_batch003_records()
    if batch003_errors:
        return fail(f"batch003 audit failed: {batch003_errors}")
    batch004_errors = audit_batch004_records()
    if batch004_errors:
        return fail(f"batch004 audit failed: {batch004_errors}")
    repair_attempts = read_json(BATCH_DIR / "repair_attempts.json")
    verified_native_count = int(batch.get("native_candidates_verified_count", 0))
    if verified_native_count and (not isinstance(repair_attempts, list) or not repair_attempts):
        return fail("verified native candidates require recorded clean repair attempts")
    if isinstance(repair_attempts, list):
        for item in repair_attempts:
            if item.get("source_only_repair_attempted") is not True:
                return fail("repair attempt missing source-only marker")
            if item.get("tests_modified") is not False or item.get("support_files_modified") is not False or item.get("config_workflow_registry_audit_modified") is not False:
                return fail("repair attempt mutated forbidden files")
            if item.get("source_mutation_performed") is True and item.get("patch_authorized") is not True:
                return fail("source mutation occurred without patch authorization")
    success_count = int(batch.get("native_repair_successes_count", 0))
    if success_count:
        duplicate_pass = read_json(BATCH_DIR / "duplicate_replay_results.json")
        validation_pass = read_json(BATCH_DIR / "target_validation_results.json")
        if not any(item.get("status") == "PASS" for item in duplicate_pass):
            return fail("native repair success without duplicate replay PASS")
        if not any(item.get("status") == "PASS" and item.get("exit_code") == 0 for item in validation_pass):
            return fail("native repair success without target validation exit 0")
    if batch.get("additional_native_external_repairs_acquired_count") != success_count:
        return fail("additional native repair count does not match repair successes")
    if success_count:
        episode_registry = read_json(Path("configs/external_repair_episode_registry.json"))
        episodes = episode_registry.get("episodes", [])
        if not any(isinstance(item, dict) and item.get("candidate_id") == "darker_non_ascii_drop_changes" and item.get("scoreable") is True for item in episodes):
            return fail("successful batch002 repair missing from external repair episode registry")
    zero_count_fields = [
        "issue_derived_candidates_verified_count",
        "additional_issue_derived_repairs_acquired_count",
        "issue_derived_repair_successes_count",
    ]
    for field in zero_count_fields:
        if batch.get(field) != 0:
            return fail(f"batch002 {field} changed unexpectedly")
    if batch.get("full_scoring") != "NOT_RUN/disallowed":
        return fail("full scoring boundary changed")
    if batch.get("memory_lift") not in {"undemonstrated", "undemonstrated_equal_performance"}:
        return fail("memory lift overclaim")
    if batch.get("self_maintaining_software") != "false/not_demonstrated":
        return fail("self-maintaining software overclaim")

    final_report = read_json(POST_DIR / "final_report_post_v2_37_hardening_001.json")
    if final_report.get("public_claim_overreach_status") != "PASS":
        return fail("public claim pressure not PASS")
    hits = public_language_hits()
    if hits:
        return fail(f"public language audit failed: {hits}")

    print("post-v2.37 hardening and batch002 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
