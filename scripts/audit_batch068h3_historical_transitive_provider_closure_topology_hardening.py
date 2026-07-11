from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch068h3_historical_transitive_provider_closure_topology_hardening"


def load(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def jsonl(name: str):
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def audit_manifest(errors: list[str]) -> None:
    manifest = OUT / "SHA256SUMS.txt"
    if not manifest.is_file():
        errors.append("manifest_missing")
        return
    covered: set[str] = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(maxsplit=1)
        rel = rel.strip().lstrip("*")
        path = OUT / rel
        covered.add(rel)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"manifest_mismatch:{rel}")
    actual = {path.relative_to(OUT).as_posix() for path in OUT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"}
    if covered != actual: errors.append("manifest_coverage_mismatch")


def main() -> int:
    errors: list[str] = []
    required = [
        "batch068h2_artifact_ingest.json", "batch068h2_official_state_preservation.json",
        "candidate_contact_ledger_catalog.jsonl", "candidate_contact_independent_verification.json",
        "reference_core_role_verification.json", "ast_extrusion_coverage_audit.json",
        "cross_family_homology_ledger.jsonl", "tot_brot_coupled_graph_v2.json",
        "tot_bulb_probe_selection_trace_batch068h3.jsonl", "proof_matrix_196_v3.json",
        "topology_falsification_results.jsonl", "tld_notebook_1_44_lineage_resolution.json",
        "locks_40_literal_authority_audit.json", "tld_metric_contract_registry.json",
        "tld_elbow_not_recovered_decision.json", "historical_provider_complete_lock.json",
        "historical_provider_lock_verification.json", "maintenance_order_execution_trace_batch068h3.json",
        "maintenance_order_out_of_order_negative_controls_batch068h3.json", "nbclient_collection_decision_batch068h3.json",
        "v2_18_promotion_decision_batch068h3.json", "product_goal_progress_matrix_batch068h3.json",
        "fifth_issue_repair_readiness_batch068h3.json", "product_capability_evidence_distinction_batch068h3.json",
        "executable_runtime_consolidation_batch068h3.json", "repository_maintainability_delta_batch068h3.json",
        "public_language_audit_batch068h3.json",
        "batch068h3_final_decision.json", "SHA256SUMS.txt",
    ]
    for name in required:
        if not (OUT / name).is_file(): errors.append(f"required_output_missing:{name}")
    if errors:
        print("Batch068h3 audit FAIL\n" + "\n".join(errors)); return 1
    audit_manifest(errors)
    ingest = load("batch068h2_artifact_ingest.json")
    outer = ingest.get("outer", {})
    if ingest.get("status") != "PASS" or outer.get("observed_size_bytes") != 125646 or outer.get("observed_sha256") != "b2f43b59fa9ddf966cef92a6c5bdcb451d425f648fd003a6cb0484c8895ba6d9": errors.append("batch068h2_identity_invalid")
    if ingest.get("entries", {}).get("entry_count") != 92 or ingest.get("outer_manifest", {}).get("checked") != 91 or ingest.get("internal_manifest", {}).get("checked") != 66: errors.append("batch068h2_manifest_or_entry_count_invalid")
    ledgers = jsonl("candidate_contact_ledger_catalog.jsonl")
    if len(ledgers) != 25 or any(row.get("contact_count") != 14 or row.get("generic_template_derived") for row in ledgers): errors.append("contact_ledgers_not_evidence_derived_25x14")
    contacts = [contact for row in ledgers for contact in row["contacts"]]
    if any(contact.get("gate_decision") == "PASS" and (not contact.get("evidence_sources") or not contact.get("evidence_hashes")) for contact in contacts): errors.append("synthetic_or_empty_contact_pass")
    pairs = jsonl("cross_family_homology_ledger.jsonl")
    if len(pairs) != 300 or any(row.get("candidate_adjacency_used") for row in pairs): errors.append("all_pairs_homology_or_adjacency_invalid")
    proof = load("proof_matrix_196_v3.json")
    verification = proof.get("verification", {})
    if len(proof.get("cells", [])) != 196 or verification.get("resolved_cell_count") != 196 or verification.get("unresolved_fallback_cell_count") != 0: errors.append("proof_matrix_not_semantically_resolved")
    controls = jsonl("topology_falsification_results.jsonl")
    if len(controls) < 196 or any("result" not in row for row in controls): errors.append("falsification_controls_not_executed")
    lineage = load("tld_notebook_1_44_lineage_resolution.json")
    if lineage.get("winner_N_argmin_historical_status") != "RECOVERED" or lineage.get("winner_N_elbow_historical_status") != "NOT_RECOVERED": errors.append("tld_winner_lineage_invalid")
    locks = load("locks_40_literal_authority_audit.json")
    if locks.get("locks_40_elbow_authority") is not False or "second_difference_formula" not in locks.get("absent_fields", []): errors.append("locks_40_elbow_overclaim")
    contracts = {item.get("metric_contract_id") for item in load("tld_metric_contract_registry.json").get("contracts", [])}
    if contracts != {"TLD-IX-CONSENSUS-v1", "TLD-XI-BYN-v1"}: errors.append("metric_contracts_invalid")
    provider = load("historical_provider_complete_lock.json")
    if provider.get("status") != "BLOCK" or len(provider.get("selected_artifacts", [])) != 15 or len(provider.get("unresolved_nodes", [])) != 15: errors.append("historical_provider_decomposition_invalid")
    if provider.get("post_cutoff_selected_artifact_count") != 0 or provider.get("runtime_dependency_closure") != "NOT_ESTABLISHED": errors.append("historical_provider_overclaim")
    collection = load("nbclient_collection_decision_batch068h3.json")
    if collection.get("collection_run_1") != "NOT_RUN" or collection.get("collection_run_2") != "NOT_RUN" or collection.get("target_tests_executed") != 0: errors.append("collection_boundary_violated")
    order = load("maintenance_order_execution_trace_batch068h3.json")
    negative = load("maintenance_order_out_of_order_negative_controls_batch068h3.json")
    if order.get("transition_count") != 14 or order.get("bounded_action_authorized") is not False or negative.get("successfully_blocked") != negative.get("control_count"): errors.append("maintenance_order_guard_invalid")
    product = load("product_goal_progress_matrix_batch068h3.json")
    if len(product.get("objectives", [])) != 20 or not product.get("completion_requires_executable_evidence"): errors.append("product_goal_matrix_invalid")
    distinctions = load("product_capability_evidence_distinction_batch068h3.json")
    if distinctions.get("capability_demonstrated", {}).get("transitive_closure") is not False or distinctions.get("generalization_demonstrated") is not False: errors.append("artifact_theater_credit_detected")
    consolidation = load("executable_runtime_consolidation_batch068h3.json")
    if consolidation.get("status") != "PASS" or consolidation.get("unbound_reusable_mechanism_count") != 0 or consolidation.get("unbound_mechanisms") != []: errors.append("runtime_binding_incomplete")
    if load("public_language_audit_batch068h3.json").get("status") != "PASS": errors.append("public_language_audit_failed")
    promotion = load("v2_18_promotion_decision_batch068h3.json")
    criteria = promotion.get("criteria", {})
    if promotion.get("status") != "PASS" or promotion.get("protocol_before") != "v2.17" or promotion.get("protocol_after") != "v2.18" or not criteria or any(value not in {True, "verified_by_local_validation_and_required_workflow"} for value in criteria.values()): errors.append("v2_18_conditional_promotion_invalid")
    final = load("batch068h3_final_decision.json")
    if final.get("patch_generated") or final.get("patch_applied") or final.get("repair_increment"): errors.append("repair_boundary_violated")
    if final.get("issue_derived_repair_count") != 4 or final.get("native_external_repair_count") != 4: errors.append("repair_counts_changed")
    if final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not_demonstrated" or final.get("self_maintaining_software") != "false/not_demonstrated": errors.append("claim_boundary_changed")
    if final.get("exact_next_allowed_action") != "batch068h4_dynamic_historical_metadata_recovery" or final.get("tld_blocked_primary_product_work") is not False: errors.append("product_priority_route_invalid")
    if errors:
        print("Batch068h3 historical provider/topology hardening audit FAIL")
        print("\n".join(errors)); return 1
    print("Batch068h3 historical provider/topology hardening audit PASS")
    return 0


if __name__ == "__main__": raise SystemExit(main())
