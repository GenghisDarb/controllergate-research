from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_file
from controllergate.core.failure_family_graph import FailureFamilyGraph
from controllergate.core.interlock_registry import REQUIRED_INTERLOCKS

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition"

REQUIRED = [
    "batch068h_artifact_outer_identity_verification.json", "batch068h_artifact_entry_audit.json", "batch068h_artifact_manifest_verification.json", "batch068h_artifact_ingestion_summary.json", "batch068h_official_vs_committed_state_reconciliation.json", "batch068h_superseded_local_placeholder_record.json", "batch068h_official_result_preservation.json", "batch068h_claim_boundary_preservation.json",
    "universal_interlock_law_manifest_v2_batch068h1.json", "interlock_handler_registry_batch068h1.json", "interlock_verifier_registry_batch068h1.json", "interlock_resolution_audit_batch068h1.json", "interlock_transition_matrix_batch068h1.json", "interlock_negative_control_results_batch068h1.json", "interlock_coverage_report_batch068h1.json",
    "semantic_runtime_pathway_v3_batch068h1.json", "semantic_runtime_handler_registry_batch068h1.json", "semantic_runtime_verifier_registry_batch068h1.json", "semantic_runtime_transition_records_batch068h1.json", "semantic_runtime_interlock_binding_batch068h1.json", "semantic_runtime_pathway_audit_batch068h1.json",
    "failure_family_graph_schema_v1_batch068h1.json", "elbow_decision_policy_v2_batch068h1.json", "nbclient_collection_failure_family_graph_batch068h1.json", "nbclient_elbow_initial_decision_batch068h1.json", "nbclient_elbow_final_decision_batch068h1.json", "elbow_interlock_binding_batch068h1.json", "failure_family_depth_audit_batch068h1.json",
    "environment_orthology_schema_v2_batch068h1.json", "batch068h_environment_orthology_correction_batch068h1.json", "nbclient_requested_environment_vector_batch068h1.json", "nbclient_observed_environment_vector_batch068h1.json", "nbclient_environment_orthology_decision_batch068h1.json",
    "decision_time_provider_resolution_policy_batch068h1.json", "decision_time_provider_lock_batch068h1.json", "decision_time_provider_eligibility_audit_batch068h1.json", "current_declared_provider_lock_preservation_batch068h1.json", "provider_epoch_comparison_batch068h1.json", "provider_epoch_elbow_decision_batch068h1.json",
    "target_origin_mode_policy_batch068h1.json", "batch068h_target_origin_conflict_batch068h1.json", "pinned_source_mode_identity_batch068h1.json", "pinned_wheel_mode_identity_batch068h1.json", "target_origin_mode_comparison_batch068h1.json", "target_origin_elbow_decision_batch068h1.json",
    "runtime_writable_paths_policy_batch068h1.json", "runtime_environment_variable_manifest_batch068h1.json", "runtime_write_observation_batch068h1.json", "runtime_write_elbow_decision_batch068h1.json",
    "collection_phase_plan_batch068h1.json", "collection_phase_results_batch068h1.json", "collection_authoritative_arm_batch068h1.json", "collection_diagnostic_arm_registry_batch068h1.json", "collection_first_failure_decision_batch068h1.json", "collection_failure_reproduction_batch068h1.json", "collection_failure_family_graph_batch068h1.json",
    "failed_branch_registry_batch068h1.json", "failed_branch_closure_audit_batch068h1.json", "canonical_state_nonmutation_proof_batch068h1.json",
    "v2_16_promotion_policy_batch068h1.json", "v2_15_preservation_audit_batch068h1.json", "v2_16_promotion_decision_batch068h1.json", "current_protocol_migration_record_batch068h1.json", "v2_16_current_protocol_audit_batch068h1.json",
    "batch068h1_final_decision.json", "batch068h1_handoff_plan.json", "batch068h1_summary.md", "public_claim_boundary_audit_batch068h1.json", "candidate_specific_hardcoding_audit_batch068h1.json", "historical_evidence_preservation_batch068h1.json", "safe_deletion_decision_batch068h1.json", "SHA256SUMS.txt",
]


def load(path: Path) -> Any: return json.loads(path.read_text(encoding="utf-8"))
def check(value: bool, message: str, errors: list[str]) -> None:
    if not value: errors.append(message)


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED: check((OUT / name).is_file(), f"missing:{name}", errors)
    if errors: print("Batch068h1 audit FAIL\n" + "\n".join(errors)); return 1
    covered = set()
    for line in (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(maxsplit=1); rel = rel.strip().lstrip("*"); covered.add(rel); path = OUT / rel
        check(path.is_file() and sha256_file(path) == digest, f"manifest_failure:{rel}", errors)
    actual = {path.relative_to(OUT).as_posix() for path in OUT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"}
    check(covered == actual, "manifest_coverage_mismatch", errors)
    outer = load(OUT / REQUIRED[0]); entries = load(OUT / REQUIRED[1]); manifests = load(OUT / REQUIRED[2])
    check(outer["status"] == "PASS" and outer["observed_size"] == 213561 and outer["observed_sha256"] == "d1f70f9a42abd19bfd80140c82596416c8675fdef1fbe650ad65dab7991a9bd3", "outer_identity", errors)
    check(entries["status"] == "PASS" and entries["entry_count"] == 138 and entries["unsafe_path_count"] == entries["duplicate_path_count"] == entries["nested_archive_or_cache_payload_count"] == 0, "entry_custody", errors)
    check(manifests["status"] == "PASS" and manifests["artifact_manifest"]["checked"] == 137 and manifests["internal_batch068h_manifest"]["checked"] == 123, "manifest_verification", errors)
    reconciliation = load(OUT / "batch068h_official_vs_committed_state_reconciliation.json")
    check(reconciliation["official_workflow_artifact_controls_runtime_conclusions"] is True and reconciliation["local_placeholder_and_official_statuses_merged"] is False, "official_local_reconciliation", errors)
    interlocks = load(OUT / "universal_interlock_law_manifest_v2_batch068h1.json")
    handlers = load(OUT / "interlock_handler_registry_batch068h1.json"); verifiers = load(OUT / "interlock_verifier_registry_batch068h1.json")
    check(interlocks["interlock_count"] == handlers["count"] == verifiers["count"] == len(REQUIRED_INTERLOCKS), "interlock_count", errors)
    check(set(handlers["handlers"]) == set(verifiers["verifiers"]) == set(REQUIRED_INTERLOCKS), "interlock_resolution", errors)
    check(len(set(handlers["handlers"].values())) == len(REQUIRED_INTERLOCKS) and len(set(verifiers["verifiers"].values())) == len(REQUIRED_INTERLOCKS), "interlock_callable_uniqueness", errors)
    check(verifiers["generic_nonempty_verifier_count"] == 0, "generic_verifier", errors)
    controls = load(OUT / "interlock_negative_control_results_batch068h1.json")
    check(controls["status"] == "PASS" and controls["patch_without_interlocks"] == controls["replay_without_target_pass"] == controls["count_without_duplicate_replay"] == "BLOCK", "negative_controls", errors)
    transitions = load(OUT / "semantic_runtime_transition_records_batch068h1.json")["records"]
    binding = load(OUT / "semantic_runtime_interlock_binding_batch068h1.json")
    check(len(transitions) == binding["interlock_bound_transition_count"] == 13 and binding["unbound_runtime_transition_count"] == 0, "runtime_interlock_binding", errors)
    check(all(transitions[i]["prior_state_hash"] == transitions[i-1]["post_state_hash"] for i in range(1, len(transitions))), "transition_hash_chain", errors)
    first_block = next((i for i, row in enumerate(transitions) if row["gate_decision"] == "BLOCK"), None)
    if first_block is not None: check(all(row["operation_status"] == "NOT_RUN" for row in transitions[first_block+1:]), "downstream_runtime_after_block", errors)
    graph = load(OUT / "nbclient_collection_failure_family_graph_batch068h1.json")
    check(all(isinstance(node["depth"], int) for node in graph["nodes"]), "numeric_failure_depth", errors)
    check(load(OUT / "failure_family_depth_audit_batch068h1.json")["maximum_tested_depth"] >= 4, "arbitrary_depth_missing", errors)
    initial = load(OUT / "nbclient_elbow_initial_decision_batch068h1.json"); final_elbow = load(OUT / "nbclient_elbow_final_decision_batch068h1.json")
    check(initial["classification"] == "elbow_closed_evidence_insufficient_missing_collection_logs", "initial_elbow", errors)
    check(final_elbow["independent_verification"]["status"] == "PASS" and final_elbow["independent_verification"]["raw_argmin_used"] is False, "elbow_verification", errors)
    phases = load(OUT / "collection_phase_results_batch068h1.json")["results"]
    executed = [item for item in phases if item.get("operation_status") == "COMPLETED"]
    for item in executed:
        prefix = f"probe_run{item['phase']}"
        for suffix in ["command_manifest.json", "stdout.txt", "stderr.txt", "combined.txt", "output_hashes.json", "secret_scan.json", "phase_decision.json"]: check((OUT / f"{prefix}_{suffix}").is_file(), f"raw_custody_missing:{prefix}_{suffix}", errors)
        if (OUT / f"{prefix}_combined.txt").is_file():
            combined_bytes = (OUT / f"{prefix}_combined.txt").read_bytes()
            hashes = load(OUT / f"{prefix}_output_hashes.json")
            check(hashlib.sha256(combined_bytes).hexdigest() == hashes["raw_combined_sha256"], f"raw_hash:{prefix}", errors)
            check(load(OUT / f"{prefix}_secret_scan.json")["status"] == "PASS", f"secret_scan:{prefix}", errors)
    orthology = load(OUT / "nbclient_observed_environment_vector_batch068h1.json")["dimensions"]
    check(len(orthology) == 16 and {item["dimension"] for item in orthology} == set(load(OUT / "environment_orthology_schema_v2_batch068h1.json")["dimensions"]), "orthology_vector", errors)
    by_dimension = {item["dimension"]: item["status"] for item in orthology}
    check(by_dimension["language_runtime_identity"] == "ESTABLISHED" and by_dimension["package_epoch_identity"] == "NOT_ESTABLISHED" and by_dimension["target_origin_identity"] == "CONFLICTED", "orthology_correction", errors)
    decision_lock = load(OUT / "decision_time_provider_lock_batch068h1.json"); current_lock = load(OUT / "current_declared_provider_lock_preservation_batch068h1.json")
    check(decision_lock["arm"] != current_lock["arm"] and current_lock["classification"] == "diagnostic_only_not_decision_time_reproduction", "provider_lock_separation", errors)
    check(decision_lock["future_package_admission_count"] == 0, "future_package_admitted", errors)
    origins = load(OUT / "target_origin_mode_comparison_batch068h1.json")
    check(origins["source_mode"] == "PASS" and origins["mixed_mode"] == "BLOCK" and origins["mixed_mode_rejected"] is True, "origin_modes", errors)
    runtime_env = load(OUT / "runtime_environment_variable_manifest_batch068h1.json")
    check(runtime_env["all_writable_paths_tmpfs_bound"] is True, "tmpfs_policy", errors)
    if phases:
        blocked_indices = [i for i, item in enumerate(phases) if item.get("gate_decision") == "BLOCK" and item.get("operation_status") == "COMPLETED"]
        if blocked_indices: check(all(item.get("operation_status") == "NOT_RUN" for item in phases[blocked_indices[0]+1:]), "phase_after_failure", errors)
    final = load(OUT / "batch068h1_final_decision.json")
    check(final["test_bodies_executed"] == final["target_tests_executed"] == final["workspace_mutations"] == final["test_tree_mutations"] == 0, "execution_mutation_boundary", errors)
    check(final["patch_generated"] is final["patch_applied"] is final["repair_count_increment"] is False, "patch_count_boundary", errors)
    check(final["issue_derived_repair_count"] == final["native_external_repair_count"] == 4, "repair_counts", errors)
    check(final["full_scoring"] == "NOT_RUN/disallowed" and final["memory_lift"] == "not_demonstrated" and final["self_maintaining_software"] == "false/not_demonstrated", "claim_boundary", errors)
    check(load(OUT / "canonical_state_nonmutation_proof_batch068h1.json")["canonical_state_mutation_count"] == 0, "canonical_mutation", errors)
    check(load(OUT / "v2_15_preservation_audit_batch068h1.json")["status"] == "PASS", "v2_15_preservation", errors)
    promotion = load(OUT / "v2_16_promotion_decision_batch068h1.json")
    check(promotion["candidate_success_controlled_promotion"] is False and promotion["status"] == "PASS", "v2_16_promotion", errors)
    for command in [[sys.executable, str(ROOT / "scripts/audit_v2_16_universal_interlock_elbow_runtime.py")], [sys.executable, str(ROOT / "scripts/controllergate_audit.py"), "--protocol", "current"], [sys.executable, str(ROOT / "scripts/controllergate_run.py"), "--protocol", "current", "--dry-run"]]:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True); check(completed.returncode == 0, f"protocol_command:{command[1:]}", errors)
    if errors:
        print("Batch068h1 universal interlock elbow harness decomposition audit FAIL"); print("\n".join(errors)); return 1
    print("Batch068h1 universal interlock elbow harness decomposition audit PASS")
    print(f"protocol={final['validated_protocol_after']} elbow={final['final_elbow_classification']} phase={final['first_diagnostic_failing_phase']}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
