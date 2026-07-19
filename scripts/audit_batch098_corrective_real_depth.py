from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"
BLOCKER = "BATCH098_LOCAL_PROVIDER_INTERPRETER_PARITY_BLOCKED_EXACT"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> int:
    contract = json.loads((ROOT / "configs/batch098_corrective_continuation_contract.json").read_text(encoding="utf-8"))
    assert contract["expected_starting_head"] == "b68b0a5c37d12daa21d2e0366179caf2771cd1ea"
    assert contract["new_composite_contract_hash"] == "37af35bebff5547ab5e2f74d86ca9c842ab5b6a37abcaa76cf6715cf489e6e90"
    direct = json.loads((ROOT / "configs/batch098_direct_source_addendum_contract.json").read_text(encoding="utf-8"))
    assert direct["previous_composite_contract_hash"] == contract["new_composite_contract_hash"]
    assert direct["new_composite_contract_hash"] == "b01a1789159694ee8f8eb616cd4ac8bcdb52e765565f423321a3ab73765c8aa5"
    expected_red = load("batch098_pre_dispatch_real_depth_expected_failure.json")
    assert expected_red["status"] == "BATCH098_PRE_DISPATCH_REAL_DEPTH_FAIL_EXPECTED"
    assert expected_red["finding_count"] == 43

    workflow_path = ROOT / ".github/workflows/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)
    assert len(workflow["jobs"]) >= 30
    assert workflow["jobs"]["public_state_and_main_artifact"]["steps"][-1]["with"]["retention-days"] == 30
    assert "tld_source_artifact_id" not in workflow[True]["workflow_dispatch"].get("inputs", {})
    assert "CONTROLLERGATE_TLD_BUNDLE_URL" not in workflow_text
    assert "PUBLIC_REGRESSION_NO_PRIVATE_TLD" in workflow_text
    assert workflow["jobs"]["tld_source_artifact_custody"]["if"] == "${{ false }}"
    assert not (ROOT / ".github/workflows/controllergate_batch098_tld_source_custody_bridge.yml").exists()
    assert not (ROOT / "scripts/configure_batch098_tld_bridge.ps1").exists()

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
    assert load("tld_direct_source_coverage_v1.json")["status"] == "PASS_44_OF_44"
    assert load("tld_direct_bundle_rebuild_audit_v1.json")["status"] == "PASS_BYTE_IDENTICAL_REBUILD"
    local = load("local_execution_independence_audit_v1.json")
    assert local["exact_blocker"] == BLOCKER
    decision = load("batch098_internal_release_decision.json")
    assert decision["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT" and decision["exact_blockers"] == [BLOCKER]
    claims = load("batch098_claim_boundary.json")
    assert (claims["protocol"], claims["package_version"], claims["issue_derived_repairs"], claims["native_external_repairs"], claims["historical_increment"]) == ("v2.19", "0.2.0b2.dev0", 6, 4, 0)
    assert claims["public_writes"] == claims["automatic_merge"] == "inactive"
    assert claims["production_readiness"] is False and claims["self_maintaining_software"] == "false/not demonstrated"
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    assert not any(line[:2].strip() and "incoming_artifacts" in line and not line.startswith("??") for line in status.splitlines())
    print("BATCH098_CORRECTIVE_REAL_DEPTH_AUDIT_PASS_PRIVATE_SOURCE_MODE_LOCAL_PROVIDER_PARITY_BLOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
