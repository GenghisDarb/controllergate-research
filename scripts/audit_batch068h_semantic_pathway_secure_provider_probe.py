from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record, sha256_file
from controllergate.core.frontier_state import verify_state_hash
from controllergate.core.step_runtime import PRODUCTION_HANDLERS, PRODUCTION_VERIFIERS, execute_semantic_graph

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe"
PRIOR = ROOT / "outputs/post_v2_37_hardening_batch068g_tier2_metadata_command_orthology_hardening"

REQUIRED = [
    "batch068g_artifact_outer_identity_verification.json", "batch068g_artifact_entry_audit.json", "batch068g_artifact_manifest_verification.json", "batch068g_artifact_ingestion_summary.json", "batch068g_frontier_state_preservation.json", "batch068g_candidate_state_preservation.json", "batch068g_claim_boundary_preservation.json",
    "semantic_step_contract_v2_batch068h.json", "semantic_step_handler_registry_batch068h.json", "semantic_step_verifier_registry_batch068h.json", "semantic_step_resolution_audit_batch068h.json", "static_transition_graph_v2_batch068h.json", "static_graph_reexecution_result_batch068h.json", "static_graph_batch068g_equivalence_report_batch068h.json", "generic_passthrough_production_usage_audit_batch068h.json", "independent_verifier_recomputation_audit_batch068h.json",
    "candidate_state_index_batch068h.json", "candidate_state_equivalence_report_batch068h.json", "status_semantics_migration_batch068h.json", "aggregate_status_vocabulary_audit_batch068h.json", "command_resolution_counts_batch068h.json", "terminal_state_distribution_batch068h.json", "tier3_recomputed_promotion_registry_batch068h.json",
    "oci_runtime_capability_report_batch068h.json", "oci_base_image_identity_batch068h.json", "oci_container_security_policy_batch068h.json", "oci_container_security_observation_batch068h.json", "secret_isolation_audit_batch068h.json", "resource_limit_observation_batch068h.json", "network_isolation_observation_batch068h.json",
    "immutable_source_identity_batch068h.json", "workspace_snapshot_pre_build_batch068h.json", "workspace_snapshot_post_build_batch068h.json", "workspace_snapshot_pre_collection_run1_batch068h.json", "workspace_snapshot_post_collection_run1_batch068h.json", "workspace_snapshot_pre_collection_run2_batch068h.json", "workspace_snapshot_post_collection_run2_batch068h.json", "workspace_diff_run1_batch068h.json", "workspace_diff_run2_batch068h.json", "workspace_allowlist_verification_batch068h.json", "rollback_recreation_verification_batch068h.json", "stale_source_marker_audit_batch068h.json",
    "provider_strategy_policy_batch068h.json", "provider_resolution_plan_batch068h.json", "provider_resolution_network_log_batch068h.json", "provider_download_manifest_batch068h.json", "provider_archive_hash_verification_batch068h.json", "provider_lock_batch068h.json", "provider_offline_install_result_batch068h.json", "provider_installed_inventory_batch068h.json", "provider_sbom_batch068h.json", "provider_environment_identity_batch068h.json", "provider_strategy_isolation_audit_batch068h.json",
    "requested_runtime_identity_batch068h.json", "exact_runtime_availability_batch068h.json", "runtime_orthology_assessment_batch068h.json",
    "harness_origin_dynamic_record_batch068h.json", "runner_import_origin_batch068h.json", "target_import_origin_batch068h.json", "target_test_identity_pre_batch068h.json", "target_test_identity_post_batch068h.json", "test_tree_immutability_batch068h.json", "pytest_configuration_immutability_batch068h.json", "fixture_identity_batch068h.json", "oracle_immutability_decision_batch068h.json",
    "probe_authorization_manifest_batch068h.json", "probe_authorization_verification_batch068h.json", "probe_command_translation_batch068h.json", "probe_run1_result_batch068h.json", "probe_run2_result_batch068h.json", "probe_duplicate_equivalence_batch068h.json", "probe_collection_node_ids_run1.txt", "probe_collection_node_ids_run2.txt", "provider_command_probe_final_decision_batch068h.json",
    "patch_safety_v2_policy_batch068h.json", "patch_manifest_v2_schema_batch068h.json", "patch_semantic_risk_policy_batch068h.json", "future_post_repair_invariant_contract_batch068h.json", "patch_safety_v2_test_results_batch068h.json",
    "artifact_audit_policy_v2_batch068h.json", "artifact_auditor_negative_control_results_batch068h.json", "artifact_auditor_policy_parity_batch068h.json",
    "prospective_memory_validation_policy_batch068h.json", "prospective_memory_validation_readiness_batch068h.json", "memory_evidence_missing_vector_batch068h.json",
    "protocol_promotion_policy_batch068h.json", "static_planning_protocol_promotion_decision_batch068h.json", "bounded_probe_capability_validation_batch068h.json", "v2_14_preservation_audit_batch068h.json", "v2_15_current_protocol_audit_batch068h.json", "current_protocol_migration_record_batch068h.json",
    "batch068h_final_decision.json", "batch068h_handoff_plan.json", "batch068h_summary.md", "public_claim_boundary_audit_batch068h.json", "candidate_specific_hardcoding_audit_batch068h.json", "historical_evidence_preservation_batch068h.json", "safe_deletion_decision_batch068h.json", "SHA256SUMS.txt",
]


def load(path: Path) -> Any: return json.loads(path.read_text(encoding="utf-8"))
def check(value: bool, message: str, errors: list[str]) -> None:
    if not value: errors.append(message)


def manifest(errors: list[str]) -> None:
    covered = set()
    for line in (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(maxsplit=1); rel = rel.strip().lstrip("*"); covered.add(rel); path = OUT / rel
        check(path.is_file() and sha256_file(path) == digest, f"manifest_failure:{rel}", errors)
    actual = {path.relative_to(OUT).as_posix() for path in OUT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"}
    check(covered == actual, "manifest_coverage_mismatch", errors)


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED: check((OUT / name).is_file(), f"missing:{name}", errors)
    if errors: print("Batch068h audit FAIL\n" + "\n".join(errors)); return 1
    manifest(errors)
    outer = load(OUT / REQUIRED[0]); entries = load(OUT / REQUIRED[1]); manifests = load(OUT / REQUIRED[2])
    check(outer["status"] == "PASS" and outer["observed_size"] == 180238 and outer["observed_sha256"] == "b6b491085e5c9bd342621e31cd684fc6deb1e5494f5b110baef7fd52bd44775d", "Batch068g outer identity", errors)
    check(entries["status"] == "PASS" and entries["entry_count"] == 82 and entries["unsafe_path_count"] == entries["duplicate_path_count"] == entries["nested_archive_or_cache_payload_count"] == 0, "Batch068g entry custody", errors)
    check(manifests["status"] == "PASS" and manifests["artifact_manifest"]["checked"] == 81 and manifests["internal_batch068g_manifest"]["checked"] == 76, "Batch068g manifests", errors)
    resolution = load(OUT / "semantic_step_resolution_audit_batch068h.json")
    check(resolution["status"] == "PASS" and resolution["handler_count"] == resolution["verifier_count"] == 11, "semantic registry resolution", errors)
    generic = load(OUT / "generic_passthrough_production_usage_audit_batch068h.json")
    check(generic["passthrough_handler_production_count"] == generic["nonempty_output_verifier_production_count"] == 0, "generic production runtime used", errors)
    index = load(OUT / "candidate_state_index_batch068h.json"); prior_index = load(PRIOR / "candidate_state_index_batch068g.json")
    check(index["candidate_count"] == len(index["records"]) == 25, "candidate count", errors)
    check({row["candidate_id"] for row in index["records"]} == {row["candidate_id"] for row in prior_index["records"]}, "candidate dropped", errors)
    contract = load(OUT / "semantic_step_contract_v2_batch068h.json")
    policy = {
        key: contract[key]
        for key in [
            "schema_version",
            "status_model",
            "forbidden_evidence_derivation_required",
            "manual_review_is_terminal",
            "block_is_terminal",
        ]
    }
    for row in index["records"]:
        state = load(ROOT / row["state_path"]); check(verify_state_hash(state), f"state hash:{row['candidate_id']}", errors)
        check(state["state_hash"] == row["state_hash"], f"index hash:{row['candidate_id']}", errors)
        transitions = state["semantic_transitions"]
        check(len(transitions) == 11, f"transition count:{row['candidate_id']}", errors)
        terminal_seen = False; terminal_kind = None; output_hashes = set()
        for transition in transitions:
            if terminal_seen:
                check(transition["gate_decision"] == "NOT_RUN", f"downstream ran after terminal:{row['candidate_id']}", errors)
                expected = "not_run_upstream_manual_review" if terminal_kind == "MANUAL_REVIEW" else "not_run_upstream_block"
                check(transition["candidate_state"] == expected, f"wrong downstream state:{row['candidate_id']}", errors)
            elif transition["gate_decision"] in {"BLOCK", "MANUAL_REVIEW"}:
                terminal_seen = True; terminal_kind = transition["gate_decision"]
            if transition["gate_decision"] == "PASS":
                check(bool(transition["input_hashes"]), f"PASS without input hash:{row['candidate_id']}", errors)
                check(bool(transition["decision_time_evidence_consumed"]), f"PASS without evidence:{row['candidate_id']}", errors)
                check(transition["forbidden_evidence_checked"] is True, f"forbidden check missing:{row['candidate_id']}", errors)
                check(transition["verification_status"] == "PASS", f"verifier failed:{row['candidate_id']}", errors)
            check(transition["output_hash"] not in output_hashes, f"duplicate step output hash:{row['candidate_id']}", errors); output_hashes.add(transition["output_hash"])
        prior_row = next(item for item in prior_index["records"] if item["candidate_id"] == row["candidate_id"])
        raw = load(ROOT / prior_row["state_path"])
        recomputed = execute_semantic_graph(row["candidate_id"], raw, policy, contract["steps"])
        check(hash_record(recomputed) == hash_record(transitions), f"independent graph recomputation mismatch:{row['candidate_id']}", errors)
    controls = load(OUT / "independent_verifier_recomputation_audit_batch068h.json")
    check(controls["status"] == "PASS" and all(value is True for key, value in controls.items() if key != "status"), "handler injection controls", errors)
    counts = load(OUT / "command_resolution_counts_batch068h.json")
    check("command_selection_unresolved_count" in counts and "authoritative_command_conflict_count" in counts, "ambiguous command counts", errors)
    check(load(OUT / "artifact_auditor_negative_control_results_batch068h.json")["status"] == "PASS", "artifact auditor negative controls", errors)
    check(load(OUT / "patch_safety_v2_test_results_batch068h.json")["status"] == "PASS", "patch safety v2", errors)
    probe = load(OUT / "provider_command_probe_final_decision_batch068h.json")
    check(probe["target_test_bodies_executed_count"] == probe["target_tests_executed"] == 0, "test body execution", errors)
    check(probe["patch_authority"] is False, "probe patch authority", errors)
    if probe["operation_status"] == "NOT_RUN":
        permitted_pre_execution_blocks = {
            "blocked_secure_execution_substrate_unavailable",
            "blocked_exact_python_runtime_unavailable",
            "blocked_artifact_custody_failure",
            "blocked_provider_resolution_failure",
        }
        check(probe["candidate_state"] in permitted_pre_execution_blocks, "invalid pre-execution blocker", errors)
        check(probe["provider_probe_attempt_count"] == 0, "probe attempted after pre-execution block", errors)
    else:
        security = load(OUT / "oci_container_security_observation_batch068h.json")
        check(load(OUT / "immutable_source_identity_batch068h.json").get("candidate_sha") == "8514e919d8405eb832e80b9ea1925767e7431ee9", "candidate source SHA", errors)
        check(load(OUT / "immutable_source_identity_batch068h.json").get("immutable_reference_contains_git_directory") is False, ".git in execution source", errors)
        provider_hashes = load(OUT / "provider_archive_hash_verification_batch068h.json")
        offline_install = load(OUT / "provider_offline_install_result_batch068h.json")
        strategy_isolation = load(OUT / "provider_strategy_isolation_audit_batch068h.json")
        sbom = load(OUT / "provider_sbom_batch068h.json")
        runner_origin = load(OUT / "runner_import_origin_batch068h.json")
        target_origin = load(OUT / "target_import_origin_batch068h.json")
        check(provider_hashes["status"] == "PASS", "provider hashes", errors)
        check(strategy_isolation["status"] == "PASS", "strategy isolation", errors)
        check(load(OUT / "workspace_allowlist_verification_batch068h.json")["source_mutation_count"] == 0, "workspace mutation", errors)
        check(load(OUT / "test_tree_immutability_batch068h.json")["test_tree_mutation_count"] == 0, "test mutation", errors)
        check(load(OUT / "rollback_recreation_verification_batch068h.json")["status"] == "PASS", "rollback recreation", errors)
        check(load(OUT / "exact_runtime_availability_batch068h.json").get("exact_python_runtime_status") == "AVAILABLE", "exact runtime orthology", errors)
        if probe["gate_decision"] == "PASS":
            for key in ["non_root_verified", "read_only_root_filesystem_verified", "capabilities_dropped_verified", "no_new_privileges_verified", "network_isolation_verified"]:
                check(security.get(key) is True, f"OCI security:{key}", errors)
            check(load(OUT / "secret_isolation_audit_batch068h.json")["status"] == "PASS", "secret isolation", errors)
            check(load(OUT / "resource_limit_observation_batch068h.json")["status"] == "PASS", "resource limits", errors)
            check(load(OUT / "network_isolation_observation_batch068h.json")["status"] == "PASS", "network isolation", errors)
            check(offline_install["status"] == "PASS", "offline install", errors)
            check(sbom["status"] == "PASS", "SBOM", errors)
            check(runner_origin["status"] == "PASS", "runner origin", errors)
            check(target_origin["status"] == "PASS", "target origin", errors)
            check(load(OUT / "probe_duplicate_equivalence_batch068h.json")["status"] == "PASS", "duplicate collection", errors)
        else:
            check(probe["candidate_state"] in {"provider_probe_single_collection_only", "blocked_target_collection_failure"}, "invalid collection blocker", errors)
    final = load(OUT / "batch068h_final_decision.json")
    check(final["issue_derived_repair_count"] == final["native_external_repair_count"] == 4, "repair counts", errors)
    check(final["patch_generated"] is final["patch_applied"] is final["repair_count_increment"] is False, "patch/count boundary", errors)
    check(final["full_scoring"] == "NOT_RUN/disallowed" and final["memory_lift"] == "not_demonstrated" and final["self_maintaining_software"] == "false/not_demonstrated", "claim boundary", errors)
    check(load(OUT / "prospective_memory_validation_readiness_batch068h.json")["operation_status"] == "NOT_RUN", "memory protocol executed", errors)
    check(load(ROOT / "outputs/frontier/EVIDENCE_CATALOG.json")["status"] == "PASS", "evidence catalog", errors)
    check(load(OUT / "safe_deletion_decision_batch068h.json")["safe_to_delete_now_count"] == 0, "safe deletion", errors)
    check(load(OUT / "v2_14_preservation_audit_batch068h.json")["status"] == "PASS", "v2.14 preservation", errors)
    check(load(OUT / "static_planning_protocol_promotion_decision_batch068h.json")["status"] == "PASS", "v2.15 promotion", errors)
    check(load(OUT / "public_claim_boundary_audit_batch068h.json")["status"] == "PASS", "public claims", errors)
    check(load(OUT / "candidate_specific_hardcoding_audit_batch068h.json")["count"] == 0, "candidate hardcoding", errors)
    for command in [[sys.executable, str(ROOT / "scripts/audit_v2_15_semantic_frontier_protocol.py")], [sys.executable, str(ROOT / "scripts/controllergate_audit.py"), "--protocol", "current"], [sys.executable, str(ROOT / "scripts/controllergate_run.py"), "--protocol", "current", "--dry-run"]]:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True); check(completed.returncode == 0, f"protocol command failed:{command[1:]}", errors)
    if errors:
        print("Batch068h semantic pathway secure provider probe audit FAIL"); print("\n".join(errors)); return 1
    print("Batch068h semantic pathway secure provider probe audit PASS")
    print(f"probe={probe['candidate_state']} current_protocol=v2.15 candidates=25")
    return 0


if __name__ == "__main__": raise SystemExit(main())
