from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"
BLOCKER = "BATCH098_TLD_SOURCE_CUSTODY_BRIDGE_AWAITING_BRAD_URL"
PRIOR_BRIDGE_BLOCKER = "BATCH098_TLD_SOURCE_CUSTODY_BRIDGE_BLOCKED_EXACT"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> int:
    required = (
        "batch097_artifact_ingest.json", "batch097_artifact_manifest_verification.json",
        "batch098_pre_fix_causal_hypergraph_and_materialization_expected_failure.json",
        "candidate_contract_custody_audit.json", "materialization_compartment_contract_v3.json",
        "neutral_observation_schema_v2.json", "board_schema_v1.json", "topology_probe_compiler_policy_v3.json",
        "tld_raw_ci_custody_v1.json", "tld_raw_parse_audit_v1.json", "tld_notebook26_source_resolution_v1.json",
        "batch098_internal_release_decision.json", "batch098_claim_boundary.json", "batch098_consolidated_state.json",
        "public_quickstart_audit.json", "public_claim_envelope_audit.json", "campaign_summary.md",
        "environment_exhausted_handoff_audit.json", "legal_probe_exhaustion_receipts.jsonl",
        "insufficient_evidence_earnability_audit.json", "failed_branch_recovery_registry.jsonl",
        "probe_neutrality_linter_results.json", "complete_decision_frame_binding_audit.json",
        "tld_shadow_state_transition_firewall.json", "batch098_addendum_metrics.json",
        "batch098_pre_dispatch_real_depth_expected_failure.json", "batch098_tld_bridge_current_status.json",
        "materializer_chain_integrity_audit.json", "candidate_control_execution_audit.json",
        "exact_incident_node_and_product_audit.json", "openbb_complete_lifecycle_audit.json",
        "candidate_specific_probe_binding_audit.json", "probe_operation_existence_audit.json",
        "predicted_partition_semantic_reconstructability_audit.json", "same_operation_multi_hypothesis_negative_control.json",
        "dpp14_real_transition_audit.json", "probe_execution_to_fact_lineage_audit.json",
        "truth_maintenance_fixed_point_audit.json", "observation_driven_backtracking_audit.json",
        "controller_audit_sole_writer_audit.json",
        "ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt",
    )
    missing = [name for name in required if not (OUT / name).is_file()]
    if missing:
        raise SystemExit("BATCH098_REQUIRED_OUTPUT_MISSING:" + ",".join(missing))
    assert load("batch097_artifact_ingest.json")["status"] == "PASS"
    assert all(row["status"] == "PASS" for row in load("batch097_artifact_manifest_verification.json")["manifests"])
    assert load("batch098_pre_fix_causal_hypergraph_and_materialization_expected_failure.json")["status"] == "BATCH098_PRE_FIX_CAUSAL_HYPERGRAPH_AND_MATERIALIZATION_FAIL_EXPECTED"
    assert load("batch098_pre_dispatch_real_depth_expected_failure.json")["status"] == "BATCH098_PRE_DISPATCH_REAL_DEPTH_FAIL_EXPECTED"
    assert load("batch098_pre_dispatch_real_depth_expected_failure.json")["finding_count"] == 43
    assert load("candidate_contract_custody_audit.json")["candidate_count"] == 8
    assert load("materialization_compartment_contract_v3.json")["exact_compartment_count"] == 6
    assert load("mixed_depth_execution_audit.json")["mixed_depth_official_execution_count"] == 0
    assert load("configured_expected_value_injection_audit.json")["configured_expected_value_injection_count"] == 0
    assert load("marker_only_semantic_verification_audit.json")["marker_only_verifier_count"] == 0
    bridge = load("tld_raw_ci_custody_v1.json")
    assert bridge["status"] in {"PASS", "BLOCK"}
    if bridge["status"] == "BLOCK":
        assert bridge["exact_blocker"] in {PRIOR_BRIDGE_BLOCKER, BLOCKER}
    assert load("tld_raw_parse_audit_v1.json")["notebook_count"] == 44
    assert load("tld_notebook26_source_resolution_v1.json")["status"] == "PASS"
    addendum = json.loads((ROOT / "configs" / "batch098_addendum_contract.json").read_text(encoding="utf-8"))
    assert addendum["addendum_hash"] == "11cf7042c2978be24f9b9268a3819517811597c247cc495187e0b4ea86a9c37a"
    assert addendum["final_composite_contract_hash"] == "5a641f70e13e0be6c205b47edfbbe10cacc246c48fa75aecef8f8756a82d0850"
    assert load("environment_exhausted_handoff_audit.json")["false_handoff_count"] == 0
    assert load("insufficient_evidence_earnability_audit.json")["unearned_insufficient_evidence_count"] == 0
    assert load("probe_neutrality_linter_results.json")["probe_neutrality_rejection_count"] >= 1
    assert load("tld_shadow_state_transition_firewall.json")["TLD_shadow_direct_state_write_count"] == 0
    assert load("batch098_tld_bridge_current_status.json")["exact_blocker"] == BLOCKER
    for name in ("materializer_chain_integrity_audit.json", "candidate_control_execution_audit.json", "exact_incident_node_and_product_audit.json", "openbb_complete_lifecycle_audit.json", "candidate_specific_probe_binding_audit.json", "probe_operation_existence_audit.json", "predicted_partition_semantic_reconstructability_audit.json", "same_operation_multi_hypothesis_negative_control.json", "dpp14_real_transition_audit.json", "probe_execution_to_fact_lineage_audit.json", "truth_maintenance_fixed_point_audit.json", "observation_driven_backtracking_audit.json", "controller_audit_sole_writer_audit.json"):
        assert load(name)["status"] == "PASS"
    decision = load("batch098_internal_release_decision.json")
    assert decision["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT"
    if bridge["status"] == "BLOCK":
        assert decision["exact_blockers"] == [BLOCKER]
    else:
        assert decision["exact_blockers"]
    claims = load("batch098_claim_boundary.json")
    assert claims["protocol"] == "v2.19" and claims["package_version"] == "0.2.0b2.dev0"
    assert claims["issue_derived_repairs"] == 6 and claims["native_external_repairs"] == 4 and claims["historical_increment"] == 0
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
    print("BATCH098_CAUSAL_HYPERGRAPH_REAL_MATERIALIZATION_TOPOLOGY_PROBE_CLOSURE_AUDIT_PASS_WITH_EXACT_BLOCK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
