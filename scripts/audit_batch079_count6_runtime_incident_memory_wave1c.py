from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from controllergate.runtime.unified_diff_contract import parse_unified_diff


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch079_count6_runtime_incident_memory_wave1c"
EXPECTED_ARTIFACT_SHA = "6469b4bf8e317b842bcbfc8a2b6cca0df67f9cabeb6a5abf1bc5250d56fc01f6"
EXPECTED_PATCH_SHA = "8e350fcf880f31975f21fd6f493d634b4b9aebe18e7441eefc1990a689e5d6a0"


def load(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def jsonl(name: str):
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    failures: list[str] = []
    required = [
        "batch078_artifact_ingest.json", "batch078_state_preservation.json", "batch078_claim_boundary_preservation.json",
        "batch078_count6_quarantine_preservation.json", "batch078_wave1b_blocker_preservation.json", "batch078_metrology_preservation.json",
        "cognicore_count6_semantic_diff_witness.json", "cognicore_count6_semantic_diff_negative_controls.json",
        "cognicore_count6_revalidation.json", "cognicore_count6_existing_count_hardening_gate.json", "cognicore_count6_terminal_proof_event_v2.json",
        "batch078_memory_calibration_depth_reconciliation.json", "batch078_same_repository_exclusion_audit.json", "batch078_no_memory_baseline_audit.json", "batch078_null_execution_reconciliation.json",
        "batch078_frame_recovery_registry.jsonl", "batch078_collection_failure_diagnostics.json", "batch078_provider_failure_diagnostics.json", "batch078_runtime_compatibility_matrix.json", "batch078_frame_recovery_decision.json",
        "hordeforge_native_working_directory_adapter.json", "hordeforge_adapter_closure_decision.json",
        "pathway_memory_calibration_v2_preregistration.json", "pathway_memory_leave_one_group_out_results.jsonl", "pathway_memory_baseline_results.json", "pathway_memory_macro_micro_metrics.json", "pathway_memory_calibration_v2_decision.json",
        "batch079_incident_lead_registry.jsonl", "batch079_incident_static_preflight.json", "batch079_incident_frame_freeze.json", "batch079_admitted_cohort_freeze.json",
        "batch079_executed_null_preregistration.json", "batch079_executed_null_registry.jsonl", "batch079_executed_null_results.json", "batch079_cg_nsi_v2_shadow_results.json",
        "batch079_comparative_arm_execution_summary.json", "batch079_blinded_ground_truth.json", "batch079_authoritative_repair_decision.json",
        "controllergate_control_taxonomy_v1.json", "batch079_control_condition_registry.jsonl", "batch079_null_vs_baseline_nonconflation.json",
        "controllergate_empirical_tail_contract_v2.json", "batch079_empirical_tail_results.jsonl", "batch079_null_resolution_preregistration.json", "batch079_null_resolution_audit.json",
        "batch079_exact_null_space_registry.json", "batch079_null_sequence_uniqueness_audit.json", "batch079_domain_relative_effects.jsonl", "batch079_null_distribution_diagnostics.json",
        "batch079_nss_alpha_nonconflation.json", "batch079_localized_defect_signal_compression.json", "batch079_power_and_sample_size_audit.json", "batch079_domain_relative_threshold_study.json",
        "batch079_claim_boundary.json", "batch079_completion_decisions.json", "batch079_final_decision.json", "batch079_summary.md", "SHA256SUMS.txt",
    ]
    for name in required:
        if not (OUT / name).is_file():
            failures.append("missing:" + name)
    if failures:
        print("Batch079 audit: FAIL\n" + "\n".join(failures)); return 1
    ingest = load("batch078_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("observed_sha256") != EXPECTED_ARTIFACT_SHA or ingest.get("file_count") != 320 or ingest.get("outer_manifest", {}).get("checked") != 319:
        failures.append("batch078_artifact_identity")
    manifest_expected: dict[str, str] = {}
    for line in (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1); manifest_expected[name] = digest
    actual_files = [path for path in OUT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"]
    if len(manifest_expected) != len(actual_files): failures.append("manifest_coverage")
    for path in actual_files:
        relative = path.relative_to(OUT).as_posix()
        if manifest_expected.get(relative) != hashlib.sha256(path.read_bytes()).hexdigest(): failures.append("manifest_hash:" + relative)
    patch = ROOT / "outputs" / "post_v2_37_hardening_batch077_typed_event_pathway_memory_v2" / "cognicore_no_memory_source_only_patch.diff"
    parsed = parse_unified_diff(patch.read_text(encoding="utf-8"))
    if hashlib.sha256(patch.read_bytes()).hexdigest() != EXPECTED_PATCH_SHA or parsed["status"] != "PASS" or parsed["hunk_count"] != 1 or parsed["changed_files"] != ["cognicore/studio.py"]:
        failures.append("unified_diff_independent_recomputation")
    witness = load("cognicore_count6_semantic_diff_witness.json")
    negative = load("cognicore_count6_semantic_diff_negative_controls.json")
    revalidation = load("cognicore_count6_revalidation.json")
    if witness.get("status") != "PASS" or witness.get("independent_recomputation_result") != "PASS": failures.append("semantic_witness")
    if negative.get("status") != "PASS" or not all(negative.get("cases", {}).values()): failures.append("semantic_negative_controls")
    if revalidation.get("COUNT_6_HARDENING") != "COUNT_6_HARDENING_PASS" or revalidation.get("count_increment") != 0 or revalidation.get("recounted") is not False: failures.append("count6_hardening_or_recount")
    timeout_case = classify_for_audit({"stage": "test_execution", "return_code": 124, "timeout_state": True, "target_nodes": ["x"], "bounded_output_tail": "AssertionError"})
    collection_case = classify_for_audit({"stage": "collection", "return_code": 4, "target_nodes": [], "bounded_output_tail": "not found"})
    if timeout_case != "RESOURCE_TIMEOUT_REPRODUCED" or collection_case not in {"TARGET_NOT_FOUND", "COLLECTION_FAILURE_REPRODUCED"}: failures.append("failure_contract_v2")
    recovery = jsonl("batch078_frame_recovery_registry.jsonl")
    allowed = {"ADMISSION_HARNESS_FIXED", "RUNTIME_COMPATIBILITY_FIXED", "PROVIDER_RESOLUTION_FIXED", "TARGET_IDENTITY_FIXED", "EXPECTED_TARGET_PASS", "DOCUMENTED_CANDIDATE_FAILURE", "UNRESOLVED_EXACT_BLOCKER"}
    if len(recovery) != 4 or any(row.get("recovery_classification") not in allowed or row.get("prospective_evidence") for row in recovery): failures.append("batch078_recovery_classification")
    runtime = load("batch078_runtime_compatibility_matrix.json")
    if any(row.get("selection", {}).get("outcome_used_for_selection") is not False or row.get("audit", {}).get("status") != "PASS" for row in runtime.get("records", [])): failures.append("runtime_selection")
    horde = load("hordeforge_native_working_directory_adapter.json")
    if horde.get("candidate_source_mutated") or horde.get("candidate_tests_mutated") or horde.get("issue_derived_count_increment") != 0: failures.append("hordeforge_adapter_boundary")
    prereg = load("pathway_memory_calibration_v2_preregistration.json")
    rows = jsonl("pathway_memory_leave_one_group_out_results.jsonl")
    if prereg.get("evaluation") != "leave_one_independence_group_out" or not rows or any(row.get("same_proof_group_excluded_count", 0) < 1 or row.get("same_repository_excluded_count", 0) < 1 for row in rows): failures.append("memory_independence")
    if load("pathway_memory_baseline_results.json").get("actual_no_memory_baseline_is_zero") is not False: failures.append("no_memory_baseline")
    frame = load("batch079_incident_frame_freeze.json")
    preflight = load("batch079_incident_static_preflight.json")
    if frame.get("frozen_before_target_execution") is not True or frame.get("adaptive_replenishment") is not False or preflight.get("target_execution_count") != 0: failures.append("incident_freeze_order")
    nulls = load("batch079_executed_null_results.json")
    if nulls.get("synthetic_replicates") != 0 or (frame.get("candidate_count") == 0 and nulls.get("executed_replicates") != 0): failures.append("executed_null_truthfulness")
    taxonomy = load("controllergate_control_taxonomy_v1.json").get("roles", {})
    if taxonomy.get("random_legal_probe_ranking") != "RANDOMIZATION_NULL" or taxonomy.get("fixed_legal_order_no_memory") != "STRONG_BASELINE_COMPARATOR" or taxonomy.get("amds_no_memory") != "MEMORY_ABLATION": failures.append("control_taxonomy")
    if load("batch079_null_vs_baseline_nonconflation.json").get("pooled") is not False: failures.append("null_baseline_conflation")
    contract = load("controllergate_empirical_tail_contract_v2.json")
    if "1+count" not in contract.get("formula", "") or contract.get("uncorrected_count_over_B_forbidden") is not True: failures.append("finite_sample_estimator")
    resolution = load("batch079_null_resolution_audit.json")
    if resolution.get("eight_or_sixteen_threshold_eligible") is not False or resolution.get("nineteen_minimum_enforced") is not True: failures.append("null_resolution")
    if load("batch079_null_sequence_uniqueness_audit.json").get("duplicate_sequences_counted_independently") is not False: failures.append("null_sequence_uniqueness")
    alpha = load("batch079_nss_alpha_nonconflation.json")
    if alpha.get("CG_NSI_0_95_corresponds_to") != "p_empirical<=0.05" or alpha.get("CG_NSI_0_99_corresponds_to") != "p_empirical<=0.01": failures.append("alpha_nonconflation")
    power = load("batch079_power_and_sample_size_audit.json")
    if power.get("low_power_interpreted_as_no_effect") is not False: failures.append("power_nonconflation")
    threshold = load("batch079_domain_relative_threshold_study.json")
    if threshold.get("production_influence") is not False or threshold.get("NSS_095_TRANSFER_STATUS") != "NOT_ESTABLISHED_FOR_PRODUCTION": failures.append("shadow_promotion_boundary")
    final = load("batch079_final_decision.json")
    if final.get("validated_protocol", "").split()[0] != "v2.19" or final.get("issue_derived_repair_count") != 6 or final.get("native_external_repair_count") != 4 or final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not demonstrated" or final.get("self_maintaining_software") != "false/not demonstrated": failures.append("claim_boundary")
    print("Batch079 audit:", "PASS" if not failures else "FAIL")
    if failures: print("\n".join(failures))
    return 1 if failures else 0


def classify_for_audit(record: dict) -> str:
    from controllergate.runtime.admission_failure_classifier import classify_capsule_failure
    return classify_capsule_failure(record)["classification"]


if __name__ == "__main__":
    raise SystemExit(main())
