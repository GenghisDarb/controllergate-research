from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.batch078_count6_minimal_closure_memory_wave1b import (
    ARM_CONDITIONS,
    BATCH,
    EXPECTED_PATCH_SHA,
    EXPECTED_SHA,
    EXPECTED_SIZE,
)

OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line]


def expect(errors: list[str], condition: bool, label: str) -> None:
    if not condition:
        errors.append(label)


def manifest_valid() -> tuple[bool, int]:
    manifest = OUT / "SHA256SUMS.txt"
    if not manifest.is_file():
        return False, 0
    checked = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        target = OUT / relative
        if not separator or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            return False, checked
        checked += 1
    return checked > 0, checked


def main() -> int:
    errors: list[str] = []
    required = {
        "batch077_artifact_ingest.json", "batch077_state_preservation.json",
        "batch077_claim_boundary_preservation.json", "batch077_count6_identity_preservation.json",
        "batch077_pathway_memory_preservation.json", "cognicore_count6_provider_lock.json",
        "cognicore_count6_prepatch_replay.json", "cognicore_count6_patch_validation.json",
        "cognicore_count6_semantic_invariants.json", "cognicore_count6_duplicate_replay.json",
        "cognicore_count6_existing_count_gate.json", "cognicore_count6_terminal_proof_event.json",
        "cognicore_count6_hardening_decision.json", "batch077_complete_traversal_reconciliation.json",
        "batch077_memory_effect_identifiability_audit.json", "hordeforge_transition_trace.json",
        "hordeforge_blocked_state_origin.json", "hordeforge_test_expectation_consistency.json",
        "hordeforge_direct_pipeline_comparison.json", "hordeforge_causal_ownership_decision.json",
        "pathway_memory_calibration_preregistration.json", "pathway_memory_leave_one_out_results.jsonl",
        "pathway_memory_calibration_metrics.json", "pathway_memory_weight_freeze.json",
        "pathway_memory_activation_decision.json", "routing_event_pathway_corpus_v2_1.jsonl",
        "routing_event_pathway_manifest_v2_1.json", "routing_event_pathway_independence_groups.json",
        "routing_event_pathway_balance_audit.json", "minimal_causal_closure_contract.json",
        "probe_cost_model_freeze.json", "transition_closure_audit.json",
        "batch078_candidate_frame_policy.json", "batch078_candidate_frame.json",
        "batch078_candidate_frame_freeze.json", "batch078_candidate_admission_registry.jsonl",
        "batch078_admitted_cohort_freeze.json", "batch078_wave1b_arm_execution_summary.json",
        "batch078_wave1b_arm_records.jsonl", "batch078_blinded_ground_truth.json",
        "batch078_wave1b_metrics.json", "batch078_authoritative_repair_decision.json",
        "tld_metric_lineage_registry_batch078.jsonl", "tld_nss_source_audit_batch078.json",
        "tld_elbow_source_audit_batch078.json", "tld_threshold_transferability_batch078.json",
        "controllergate_matched_null_contract_v1.json", "controllergate_null_registry_batch078.jsonl",
        "controllergate_null_generation_audit.json", "controllergate_null_separation_metric_v1.json",
        "controllergate_null_separation_results_batch078.json", "controllergate_nss_nonconflation_statement.json",
        "controllergate_elbow_shadow_contract_v1.json", "controllergate_elbow_comparison_batch078.jsonl",
        "controllergate_elbow_scaling_sensitivity.json", "controllergate_flatline_diagnostic_batch078.json",
        "batch078_tld_shadow_metrology_report.json", "batch078_tld_shadow_nonblocking_audit.json",
        "batch078_completion_decisions.json", "batch078_final_decision.json", "batch078_summary.md",
        "SHA256SUMS.txt",
    }
    missing = sorted(name for name in required if not (OUT / name).is_file())
    if missing:
        print("Batch078 audit: FAIL")
        print("errors: missing:" + ",".join(missing))
        return 1
    manifest_ok, manifest_count = manifest_valid()
    expect(errors, manifest_ok, "manifest")

    ingest = load("batch077_artifact_ingest.json")
    expect(errors, ingest.get("status") == "PASS" and ingest.get("observed_size_bytes") == EXPECTED_SIZE and ingest.get("observed_sha256") == EXPECTED_SHA and ingest.get("file_count") == 258, "batch077_identity")
    expect(errors, ingest.get("outer_manifest", {}).get("checked") == 257 and ingest.get("outer_manifest", {}).get("status") == "PASS", "outer_manifest")
    expect(errors, all(item.get("status") == "PASS" for item in ingest.get("internal_manifests", {}).values()), "internal_manifests")
    expect(errors, not ingest.get("forbidden_payloads") and ingest.get("raw_zip_committed") is False, "artifact_custody")

    identity = load("batch077_count6_identity_preservation.json")
    count_gate = load("cognicore_count6_existing_count_gate.json")
    count_decision = load("cognicore_count6_hardening_decision.json")
    expect(errors, identity.get("historical_count") == 6 and identity.get("count_increment") == 0 and identity.get("patch_sha256") == EXPECTED_PATCH_SHA, "count6_identity")
    expect(errors, count_gate.get("existing_count_records") == 1 and count_gate.get("count_increment") == 0 and count_gate.get("historical_count") == 6, "no_recount")
    if count_decision.get("COUNT_6_HARDENING") == "COUNT_6_HARDENING_PASS":
        prepatch = load("cognicore_count6_prepatch_replay.json")
        patch = load("cognicore_count6_patch_validation.json")
        semantic = load("cognicore_count6_semantic_invariants.json")
        duplicate = load("cognicore_count6_duplicate_replay.json")
        expect(errors, prepatch.get("status") == "PASS" and prepatch.get("capsule_count") == 2 and prepatch.get("equivalent_nonempty_failure_signature") is True, "count6_prepatch")
        expect(errors, patch.get("status") == "PASS" and patch.get("patch_sha256") == EXPECTED_PATCH_SHA and patch.get("preserved_patch_exact") is True, "count6_patch")
        expect(errors, semantic.get("status") == "PASS" and semantic.get("only_intended_title_branding_changed") is True, "count6_semantic")
        expect(errors, duplicate.get("status") == "PASS" and duplicate.get("capsule_count") == 2, "count6_duplicate")
    else:
        expect(errors, count_decision.get("status") == "NOT_RUN_LOCAL_EVIDENCE_ONLY", "local_count6_boundary")

    horde = load("hordeforge_causal_ownership_decision.json")
    origin = load("hordeforge_blocked_state_origin.json")
    expect(errors, horde.get("preserved_reproduction") == "ORIGINAL_ASSERTION_REPRODUCED" and horde.get("causal_ownership") == "fixture_or_harness_owned" and horde.get("patch_authority") is False, "horde_ownership")
    expect(errors, origin.get("BLOCKED_result_object_created") is False and origin.get("project_policy_expected_event") is False, "horde_reproduction_separation")

    traversal = load("batch077_complete_traversal_reconciliation.json")
    identifiable = load("batch077_memory_effect_identifiability_audit.json")
    expect(errors, traversal.get("arm_count") == 12 and traversal.get("raw_probe_count") == 96 and traversal.get("all_arms_used_eight_probes") is True, "complete_traversal")
    expect(errors, all(value == "NOT_IDENTIFIABLE_UNDER_COMPLETE_TRAVERSAL" for value in identifiable.get("endpoints", {}).values()), "identifiability")

    prereg = load("pathway_memory_calibration_preregistration.json")
    calibration = load("pathway_memory_calibration_metrics.json")
    freeze = load("pathway_memory_weight_freeze.json")
    rows = jsonl("pathway_memory_leave_one_out_results.jsonl")
    expect(errors, prereg.get("evaluation") == "leave_one_episode_out" and prereg.get("prospective_outcomes_used_for_tuning") is False and prereg.get("same_candidate_excluded") is True, "calibration_design")
    expect(errors, len(rows) == calibration.get("pathway_count") and "shuffled_mean_reciprocal_rank" in calibration, "calibration_results")
    expect(errors, freeze.get("frozen_before_wave1b") is True, "memory_freeze")

    corpus = jsonl("routing_event_pathway_corpus_v2_1.jsonl")
    groups = load("routing_event_pathway_independence_groups.json")
    expect(errors, len(corpus) >= 2 and all(row.get("proof_hash") and row.get("episode_independence_group") for row in corpus), "proof_corpus")
    proof_groups: dict[str, set[str]] = {}
    for row in corpus:
        proof_groups.setdefault(row["proof_hash"], set()).add(row["episode_independence_group"])
    expect(errors, all(len(values) == 1 for values in proof_groups.values()) and groups.get("status") == "PASS", "proof_independence")

    closure = load("minimal_causal_closure_contract.json")
    cost = load("probe_cost_model_freeze.json")
    transition = load("transition_closure_audit.json")
    expect(errors, closure.get("memory_can_waive") is False and closure.get("same_for_all_strategies") is True and closure.get("independent_verifier_required") is True, "closure_contract")
    expect(errors, cost.get("frozen_before_wave1b") is True and cost.get("probe_count_is_not_sole_objective") is True, "cost_freeze")
    expect(errors, transition.get("status") == "PASS" and transition.get("rollback_inverse") is True and transition.get("unsupported_topology_gate_used") is False, "transition_closure")

    frame = load("batch078_candidate_frame.json")
    frame_freeze = load("batch078_candidate_frame_freeze.json")
    admissions = jsonl("batch078_candidate_admission_registry.jsonl")
    cohort = load("batch078_admitted_cohort_freeze.json")
    arm_rows = jsonl("batch078_wave1b_arm_records.jsonl")
    ground = load("batch078_blinded_ground_truth.json")
    expect(errors, frame.get("candidate_count") == 4 and frame_freeze.get("no_adaptive_replenishment") is True and len(admissions) == 4, "frame_freeze")
    expect(errors, cohort.get("adaptive_replenishment") is False and cohort.get("frozen_before_diagnostics") is True, "cohort_freeze")
    if cohort.get("candidate_count", 0) >= 2:
        by_candidate: dict[str, set[str]] = {}
        for row in arm_rows:
            by_candidate.setdefault(row["candidate_id"], set()).add(row["arm"])
        expect(errors, all(values == set(ARM_CONDITIONS) for values in by_candidate.values()), "six_arm_design")
        expect(errors, all(row.get("isolated_state") is True and row.get("diagnostic_patch_generated") is False and row.get("memory_supplied_repair_content") is False for row in arm_rows), "arm_isolation")
        expect(errors, ground.get("all_arms_sealed_first") is True and ground.get("adjudicator_blinded") is True, "blinded_ground_truth")
        expect(errors, all(row.get("early_stop_verifier", {}).get("status") == "PASS" for row in arm_rows), "early_stop")
    else:
        expect(errors, not arm_rows and cohort.get("status") == "WAVE1B_ADMISSION_BLOCKED_MINIMUM_NOT_MET", "minimum_cohort_boundary")

    repair = load("batch078_authoritative_repair_decision.json")
    expect(errors, repair.get("attempts", 0) <= 1 and repair.get("authoritative_memory_condition") == "NO_MEMORY" and repair.get("memory_repair_content_used") is False, "repair_boundary")

    nss = load("tld_nss_source_audit_batch078.json")
    elbow = load("tld_elbow_source_audit_batch078.json")
    null_contract = load("controllergate_matched_null_contract_v1.json")
    null_audit = load("controllergate_null_generation_audit.json")
    metric = load("controllergate_null_separation_metric_v1.json")
    nonconflation = load("controllergate_nss_nonconflation_statement.json")
    scaling = load("controllergate_elbow_scaling_sensitivity.json")
    shadow = load("batch078_tld_shadow_nonblocking_audit.json")
    expect(errors, nss.get("formula") == "NSS = 1 - P_bootstrap(UI_null >= UI_observed)" and nss.get("generic_software_score") is False, "tld_nss_lineage")
    expect(errors, elbow.get("one_e_minus_nine_elbow_prominence_source_recovered") is False and elbow.get("production_gate") is False, "elbow_lineage")
    expect(errors, null_contract.get("candidate_matched") is True and null_contract.get("budget_matched") is True and null_contract.get("generated_before_outcome_evaluation") is True, "matched_null_contract")
    expect(errors, null_audit.get("cross_candidate_pooling") is False and metric.get("metric_id") == "CG_NSI_v1", "software_null_metric")
    expect(errors, metric.get("weights", {}).get("wrong_patch_authorization") == -1.0 and nonconflation.get("same_name_reused") is False, "composite_safety")
    expect(errors, scaling.get("classification") == "ABSOLUTE_THRESHOLD_NOT_SCALE_INVARIANT" and scaling.get("classification_changes_under_positive_rescaling") is True, "scale_sensitivity")
    expect(errors, shadow.get("status") == "PASS" and all(shadow.get(key) is False for key in ("candidate_admission_influence", "patch_authorization_influence", "repair_count_influence")), "shadow_nonblocking")

    final = load("batch078_final_decision.json")
    decisions = final.get("decisions", {})
    expect(errors, final.get("status") == "PASS" and final.get("issue_derived_repair_count") == 6 and final.get("native_external_repair_count") == 4, "final_counts")
    expect(errors, decisions.get("AMDS_PROSPECTIVE_EFFECTIVENESS") == "NOT_ESTABLISHED" and final.get("memory_lift") == "not_demonstrated", "claim_boundary")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed" and final.get("self_maintaining_software") == "false/not_demonstrated" and final.get("live_connectors") == "inactive", "global_claim_boundary")
    expect(errors, decisions.get("NSS_095_TRANSFER_STATUS") == "NOT_ESTABLISHED_FOR_CONTROLLERGATE" and decisions.get("ELBOW_PRODUCTION_READINESS") == "NOT_ESTABLISHED", "shadow_claim_boundary")

    if errors:
        print("Batch078 audit: FAIL")
        print("errors:", ", ".join(errors))
        return 1
    print(f"Batch078 audit: PASS ({manifest_count} manifest entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
