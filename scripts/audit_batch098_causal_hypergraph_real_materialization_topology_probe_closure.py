from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"
BLOCKER = "BATCH098_LOCAL_PROVIDER_INTERPRETER_PARITY_BLOCKED_EXACT"
DIRECT_ADDENDUM_HASH = "55602ec8d033d002feebcb99beebd8aa85c8fba4bbf3fd104d3576df13d51a97"
FINAL_COMPOSITE_HASH = "b01a1789159694ee8f8eb616cd4ac8bcdb52e765565f423321a3ab73765c8aa5"
DIRECT_BUNDLE_SHA256 = "e18d208e0428944674d6ca6aa9d50609e2256e28ab83dad92ad583dc1ad8a644"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> int:
    required = (
        "batch097_artifact_ingest.json", "batch097_artifact_manifest_verification.json",
        "batch098_pre_fix_causal_hypergraph_and_materialization_expected_failure.json",
        "batch098_pre_dispatch_real_depth_expected_failure.json", "candidate_contract_custody_audit.json",
        "materialization_compartment_contract_v3.json", "neutral_observation_schema_v2.json",
        "board_schema_v1.json", "topology_probe_compiler_policy_v3.json",
        "environment_exhausted_handoff_audit.json", "legal_probe_exhaustion_receipts.jsonl",
        "insufficient_evidence_earnability_audit.json", "failed_branch_recovery_registry.jsonl",
        "probe_neutrality_linter_results.json", "complete_decision_frame_binding_audit.json",
        "tld_shadow_state_transition_firewall.json", "batch098_addendum_metrics.json",
        "tld_direct_source_inventory_v1.jsonl", "tld_direct_source_notebook_map_v1.jsonl",
        "tld_direct_source_conflicts_v1.jsonl", "tld_direct_source_coverage_v1.json",
        "tld_direct_source_extraction_report_v1.json", "tld_direct_bundle_builder_report_v1.json",
        "tld_direct_bundle_builder_manifest_v1.json", "tld_direct_bundle_member_manifest_v1.jsonl",
        "tld_direct_bundle_canonical_identity_v1.json", "tld_direct_bundle_rebuild_audit_v1.json",
        "tld_direct_requirement_compilation_v1.json", "tld_direct_source_authority_firewall_v1.json",
        "tld_notebook26_direct_source_resolution_v2.json", "tld_notebook40_direct_source_resolution_v2.json",
        "tld_notebook44_direct_source_resolution_v2.json", "local_execution_independence_audit_v1.json",
        "batch098_tld_direct_source_current_status.json", "batch098_tld_bridge_current_status.json",
        "batch098_internal_release_decision.json", "batch098_claim_boundary.json", "batch098_consolidated_state.json",
        "public_quickstart_audit.json", "public_claim_envelope_audit.json", "campaign_summary.md",
        "materializer_chain_integrity_audit.json", "candidate_control_execution_audit.json",
        "exact_incident_node_and_product_audit.json", "openbb_complete_lifecycle_audit.json",
        "candidate_specific_probe_binding_audit.json", "probe_operation_existence_audit.json",
        "predicted_partition_semantic_reconstructability_audit.json", "same_operation_multi_hypothesis_negative_control.json",
        "dpp14_real_transition_audit.json", "probe_execution_to_fact_lineage_audit.json",
        "truth_maintenance_fixed_point_audit.json", "observation_driven_backtracking_audit.json",
        "controller_audit_sole_writer_audit.json", "ARTIFACT_SHA256SUMS.txt",
        "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt",
    )
    missing = [name for name in required if not (OUT / name).is_file()]
    if missing:
        raise SystemExit("BATCH098_REQUIRED_OUTPUT_MISSING:" + ",".join(missing))

    assert load("batch097_artifact_ingest.json")["status"] == "PASS"
    assert all(row["status"] == "PASS" for row in load("batch097_artifact_manifest_verification.json")["manifests"])
    assert load("batch098_pre_fix_causal_hypergraph_and_materialization_expected_failure.json")["status"] == "BATCH098_PRE_FIX_CAUSAL_HYPERGRAPH_AND_MATERIALIZATION_FAIL_EXPECTED"
    expected_red = load("batch098_pre_dispatch_real_depth_expected_failure.json")
    assert expected_red["status"] == "BATCH098_PRE_DISPATCH_REAL_DEPTH_FAIL_EXPECTED"
    assert expected_red["finding_count"] == 43
    assert load("candidate_contract_custody_audit.json")["candidate_count"] == 8
    assert load("materialization_compartment_contract_v3.json")["exact_compartment_count"] == 6
    assert load("mixed_depth_execution_audit.json")["mixed_depth_official_execution_count"] == 0
    assert load("configured_expected_value_injection_audit.json")["configured_expected_value_injection_count"] == 0
    assert load("marker_only_semantic_verification_audit.json")["marker_only_verifier_count"] == 0

    direct_contract = json.loads((ROOT / "configs" / "batch098_direct_source_addendum_contract.json").read_text(encoding="utf-8"))
    assert direct_contract["addendum_hash"] == DIRECT_ADDENDUM_HASH
    assert direct_contract["new_composite_contract_hash"] == FINAL_COMPOSITE_HASH
    coverage = load("tld_direct_source_coverage_v1.json")
    assert coverage["status"] == "PASS_44_OF_44"
    assert coverage["covered_count"] == 44 and coverage["missing_notebooks"] == []
    assert coverage["unresolved_conflict_count"] == 0
    identity = load("tld_direct_bundle_canonical_identity_v1.json")
    assert identity["status"] == "PASS_BYTE_IDENTICAL_REBUILD"
    assert identity["bundle_sha256"] == DIRECT_BUNDLE_SHA256
    rebuild = load("tld_direct_bundle_rebuild_audit_v1.json")
    assert rebuild["status"] == "PASS_BYTE_IDENTICAL_REBUILD"
    assert rebuild["separate_process_count"] == 2 and rebuild["separate_temporary_directory_count"] == 2
    firewall = load("tld_direct_source_authority_firewall_v1.json")
    assert firewall["raw_private_source_bytes_committed"] is False
    assert firewall["direct_state_write_count"] == 0 and firewall["authority_escalation_count"] == 0
    local = load("local_execution_independence_audit_v1.json")
    assert local["status"] == "BLOCK"
    assert local["exact_blocker"] == BLOCKER
    assert sorted(local["missing_provider_series"]) == ["3.11", "3.7"]
    direct_status = load("batch098_tld_direct_source_current_status.json")
    assert direct_status["status"] == "BATCH098_TLD_DIRECT_SOURCE_CUSTODY_PASS_LOCAL_EXACT"
    assert direct_status["github_scientific_workflow"] == "NOT_RUN_PRIVATE_SOURCE_MODE"
    assert load("batch098_tld_bridge_current_status.json")["status"] == "RETIRED_REPLACED_BY_DIRECT_SOURCE_MODE"

    assert load("environment_exhausted_handoff_audit.json")["false_handoff_count"] == 0
    assert load("insufficient_evidence_earnability_audit.json")["unearned_insufficient_evidence_count"] == 0
    assert load("probe_neutrality_linter_results.json")["probe_neutrality_rejection_count"] >= 1
    assert load("tld_shadow_state_transition_firewall.json")["TLD_shadow_direct_state_write_count"] == 0
    for name in (
        "materializer_chain_integrity_audit.json", "candidate_control_execution_audit.json",
        "exact_incident_node_and_product_audit.json", "openbb_complete_lifecycle_audit.json",
        "candidate_specific_probe_binding_audit.json", "probe_operation_existence_audit.json",
        "predicted_partition_semantic_reconstructability_audit.json", "same_operation_multi_hypothesis_negative_control.json",
        "dpp14_real_transition_audit.json", "probe_execution_to_fact_lineage_audit.json",
        "truth_maintenance_fixed_point_audit.json", "observation_driven_backtracking_audit.json",
        "controller_audit_sole_writer_audit.json",
    ):
        assert load(name)["status"] == "PASS"

    decision = load("batch098_internal_release_decision.json")
    assert decision["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT"
    assert decision["exact_blockers"] == [BLOCKER]
    claims = load("batch098_claim_boundary.json")
    assert claims["protocol"] == "v2.19" and claims["package_version"] == "0.2.0b2.dev0"
    assert claims["issue_derived_repairs"] == 6 and claims["native_external_repairs"] == 4
    assert claims["historical_increment"] == 0
    assert claims["public_writes"] == claims["automatic_merge"] == "inactive"
    assert claims["production_readiness"] is False and claims["self_maintaining_software"] == "false/not demonstrated"

    for manifest_name in ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"):
        lines = (OUT / manifest_name).read_text(encoding="utf-8").splitlines()
        assert all(not line.endswith("  " + manifest_name) for line in lines)
        for line in lines:
            expected, name = line.split("  ", 1)
            assert hashlib.sha256((OUT / name).read_bytes()).hexdigest() == expected

    assert (ROOT / "docs" / "QUICKSTART.md").is_file()
    assert (ROOT / "docs" / "CLAIM_ENVELOPE.md").is_file()
    assert (ROOT / ".github" / "workflows" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure.yml").is_file()
    assert not (ROOT / ".github" / "workflows" / "controllergate_batch098_tld_source_custody_bridge.yml").exists()
    print("BATCH098_DIRECT_SOURCE_CUSTODY_AUDIT_PASS_LOCAL_PROVIDER_PARITY_BLOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
