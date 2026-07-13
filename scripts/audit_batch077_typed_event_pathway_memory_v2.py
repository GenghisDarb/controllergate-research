from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.batch077_typed_event_pathway_memory_v2 import BATCH, EXPECTED_SHA, EXPECTED_SIZE, EXPECTED_MANIFESTS
from controllergate.pathways.validator import validate_pathway

OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line]


def expect(errors: list[str], condition: bool, label: str) -> None:
    if not condition:
        errors.append(label)


def manifest_valid() -> tuple[bool, int]:
    path = OUT / "SHA256SUMS.txt"
    if not path.is_file():
        return False, 0
    checked = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            return False, checked
        digest, relative = parts
        target = OUT / relative.strip().lstrip("*")
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            return False, checked
        checked += 1
    return checked > 0, checked


def main() -> int:
    errors: list[str] = []
    required = {
        "batch076_artifact_ingest.json", "batch076_state_preservation.json",
        "batch076_claim_boundary_preservation.json", "batch076_causal_evidence_preservation.json",
        "batch076_memory_corpus_diversity_audit.json", "batch076_memory_independence_audit.json",
        "batch076_real_vs_shuffled_identity_audit.json", "event_transition_contract_v1.json",
        "event_transition_validator_v1.json", "routing_event_pathway_corpus_v2.jsonl",
        "routing_event_pathway_manifest_v2.json", "routing_event_pathway_diversity_audit.json",
        "shuffled_routing_event_pathway_corpus_v2.jsonl", "shuffled_pathway_memory_manifest_v2.json",
        "pathway_memory_conditions_v2.json", "pathway_projection_contract_v1.json",
        "candidate_pathway_projection_records.jsonl", "pathway_projection_verifier.json",
        "cognicore_normal_expected_pathway.json", "cognicore_observed_incident_pathway.json",
        "cognicore_normal_incident_divergence.json", "hordeforge_runtime_compartment_correction.json",
        "hordeforge_causal_result.json", "hordeforge_corrected_admission_decision.json",
        "pathway_gap_amds_arm_summary.json", "pathway_gap_probe_event_ledger.jsonl",
        "pathway_gap_probe_fidelity_audit.json", "batch077_blinded_ground_truth.json",
        "batch077_pathway_memory_metrics.json", "batch077_authoritative_no_memory_repair.json",
        "batch077_final_decision.json", "batch077_summary.md", "batch077_provider_store_reconciliation.json",
        "reactome_literal_source_registry_batch077.jsonl", "reactome_source_hash_manifest_batch077.json",
        "reactome_class_field_relationship_matrix_batch077.json", "reactome_to_controllergate_event_mapping_batch077.json",
        "reactome_direct_vs_inferred_mapping_batch077.json", "reactome_stable_identity_mapping_batch077.json",
        "reactome_compartment_identity_contract_batch077.json", "reactome_pathway_cycle_reference_batch077.json",
        "reactome_generation_validation_boundary_batch077.json", "reactome_unresolved_source_questions_batch077.json",
        "batch077_schema_field_traceability.json", "SHA256SUMS.txt",
    }
    missing = sorted(name for name in required if not (OUT / name).is_file())
    if missing:
        errors.append("missing:" + ",".join(missing))
        print("Batch077 typed event pathway memory v2 audit: FAIL")
        print("errors:", ", ".join(errors))
        return 1
    manifest_ok, manifest_count = manifest_valid()
    expect(errors, manifest_ok and manifest_count >= 45, "manifest")

    ingest = load("batch076_artifact_ingest.json")
    expect(errors, ingest.get("status") == "PASS", "batch076_ingest")
    expect(errors, ingest.get("observed_size_bytes") == EXPECTED_SIZE and ingest.get("observed_sha256") == EXPECTED_SHA, "batch076_identity")
    expect(errors, ingest.get("file_count") == 210 and ingest.get("outer_manifest", {}).get("checked") == 209, "batch076_outer_manifest")
    expect(errors, all(ingest.get("internal_manifests", {}).get(name, {}).get("checked") == count for name, count in EXPECTED_MANIFESTS.items()), "batch076_internal_manifests")
    entry = ingest.get("entry_audit", {})
    expect(errors, all(entry.get(key) == 0 for key in ("unsafe_path_count", "duplicate_path_count", "pycache_payload_count", "pyc_payload_count", "nested_archive_or_cache_payload_count")), "batch076_path_custody")
    expect(errors, load("batch076_state_preservation.json").get("historical_records_modified") is False, "batch076_history")
    claims = load("batch076_claim_boundary_preservation.json")
    expect(errors, claims.get("validated_protocol") == "v2.19", "protocol")
    expect(errors, claims.get("issue_derived_repair_count") == 5 and claims.get("native_external_repair_count") == 4, "prior_counts")
    expect(errors, claims.get("AMDS_CAUSAL_EVIDENCE") == "AMDS_CAUSAL_EVIDENCE_HARDENED", "causal_preservation")

    diversity = load("batch076_memory_corpus_diversity_audit.json")
    expect(errors, diversity.get("record_count") == 9 and diversity.get("degenerate_flat_topology") is True, "memory_v1_degeneracy")
    expect(errors, all(item.get("unique_count") == 1 for item in diversity.get("field_diversity", {}).values()), "memory_v1_field_diversity")
    independence = load("batch076_memory_independence_audit.json")
    expect(errors, independence.get("unique_episode_ids") == 9 and independence.get("independently_identified_records") is True, "memory_independence")
    expect(errors, bool(independence.get("shared_proof_hash_groups")), "shared_proof_hash_disclosed")
    old_control = load("batch076_real_vs_shuffled_identity_audit.json")
    expect(errors, old_control.get("complete_shuffled_corpus_persisted_in_batch076") is False, "old_control_limit")

    real = jsonl("routing_event_pathway_corpus_v2.jsonl")
    shuffled = jsonl("shuffled_routing_event_pathway_corpus_v2.jsonl")
    pathway_manifest = load("routing_event_pathway_manifest_v2.json")
    expect(errors, len(real) == len(shuffled) == pathway_manifest.get("pathway_count") == 9, "pathway_count")
    expect(errors, all(validate_pathway(row)["status"] == "PASS" for row in real), "pathway_validation")
    expect(errors, len({row["pathway_hash"] for row in real}) == 9, "unique_pathway_hashes")
    expect(errors, pathway_manifest.get("unique_event_type_sequences", 0) > 1 and pathway_manifest.get("unique_compartment_transition_sequences", 0) > 1, "pathway_structural_diversity")
    expect(errors, all(row.get("proof_references") for row in real), "pathway_proof_binding")
    shuffled_manifest = load("shuffled_pathway_memory_manifest_v2.json")
    expect(errors, shuffled_manifest.get("status") == "PASS" and shuffled_manifest.get("hashes_distinct") is True, "genuine_shuffled_control")
    expect(errors, shuffled_manifest.get("distribution_comparison", {}).get("marginals_preserved") is True, "shuffled_marginals")
    expect(errors, load("pathway_memory_conditions_v2.json").get("all_identities_distinct") is True, "condition_identity")

    all_events = [event for row in real for event in row["events"]]
    expect(errors, all(event.get("required_input_entities") and event.get("catalyst_or_executor") and event.get("positive_regulators") and event.get("negative_regulators") and event.get("output_entities") for event in all_events), "typed_event_roles")
    expect(errors, all(event.get("compartment") and event.get("evidence_references") for event in all_events), "event_compartment_custody")
    underlying_context: dict[str, set[str]] = {}
    for event in all_events:
        for entity in event["input_entities"] + event["output_entities"]:
            underlying_context.setdefault(entity["underlying_identity"], set()).add(entity["entity_id"])
    expect(errors, all(len(contexts) >= 1 for contexts in underlying_context.values()), "contextual_identity")

    projections = jsonl("candidate_pathway_projection_records.jsonl")
    expect(errors, len(projections) == 18, "projection_count")
    expect(errors, all(item.get("knowledge_status") == "STRUCTURALLY_PROJECTED" and item.get("projection_evidence_hash") and item.get("independent_verifier") and item.get("review_state") for item in projections), "projection_provenance")
    expect(errors, all("ground_truth" in item.get("forbidden_influences", []) and "patch_authorization" in item.get("forbidden_influences", []) for item in projections), "projection_firewall")
    verifier = load("pathway_projection_verifier.json")
    expect(errors, verifier.get("same_repository_records") == 0 and verifier.get("all_similarity_one") is False and verifier.get("unique_component_vectors", 0) > 1, "graph_matching")

    normal = load("cognicore_normal_expected_pathway.json")
    incident = load("cognicore_observed_incident_pathway.json")
    cog = load("cognicore_normal_incident_divergence.json")
    expect(errors, normal.get("incident_variant_pathway") == incident.get("pathway_id") and incident.get("normal_reference_pathway") == normal.get("pathway_id"), "normal_incident_pair")
    expect(errors, cog.get("first_divergence_event") and cog.get("classification") in {"SOURCE_OWNED_OUTPUT_DIVERGENCE", "TEST_EXPECTATION_DIVERGENCE", "MIXED_EXPECTATION_AND_SOURCE", "INSUFFICIENT_EVIDENCE"}, "cognicore_divergence")

    horde = load("hordeforge_runtime_compartment_correction.json")
    horde_decision = load("hordeforge_corrected_admission_decision.json")
    expect(errors, horde.get("source_read_only") is True and horde.get("runtime_scratch_writable") is True, "horde_compartments")
    expect(errors, horde.get("source_hashes_unchanged") is True and horde.get("harness_view_source_hashes_match") is True, "horde_source_preservation")
    expect(errors, horde.get("prior_oserror_removed") is True, "horde_old_blocker_removed")
    expect(errors, horde_decision.get("classification") in {"HARNESS_COMPARTMENT_BLOCKER_REMOVED", "ORIGINAL_ASSERTION_REPRODUCED", "SOURCE_LOOP_OR_DEADLOCK", "FIXTURE_OR_HARNESS_STALL", "PROVIDER_STALL", "RESOURCE_TIMEOUT", "INSUFFICIENT_EVIDENCE"}, "horde_classification")
    if horde_decision.get("corrected_admission") == "ADMITTED_CANDIDATE_FAILURE":
        expect(errors, horde_decision.get("nonempty_causal_signature") is True, "horde_nonempty_signature")

    arms = load("pathway_gap_amds_arm_summary.json")
    ledger = jsonl("pathway_gap_probe_event_ledger.jsonl")
    expect(errors, arms.get("arm_count") == 12 and arms.get("candidate_count") == 2, "arm_design")
    expect(errors, arms.get("accepted_probes") == arms.get("event_count") == len(ledger), "probe_event_bijection")
    expect(errors, all(item["selected_gap"] in item["unresolved_pathway_before_probe"] and item["semantic_verification"] == "PASS" and item["event_ledger_appended"] is True for item in ledger), "gap_probe_fidelity")
    expect(errors, arms.get("backtracking_count", 0) > 0 and arms.get("posterior_updates") == len(ledger), "backtracking_posterior")
    expect(errors, all(row.get("observation_sharing") is False and row.get("patch_authority") is False for row in arms.get("records", [])), "arm_isolation")
    ground = load("batch077_blinded_ground_truth.json")
    expect(errors, ground.get("arms_sealed_before_adjudication") is True and all(ground.get(key) is False for key in ("arm_labels_available", "memory_conditions_available", "probe_order_available", "arm_terminal_results_available")), "blinded_ground_truth")

    repair = load("batch077_authoritative_no_memory_repair.json")
    expect(errors, repair.get("memory_condition") == "NO_MEMORY" and repair.get("patch_content_from_memory") is False and repair.get("attempts", 0) <= 1, "repair_boundary")
    if repair.get("attempts") == 1:
        expect(errors, repair.get("source_only") is True and repair.get("tests_modified") is False, "repair_source_only")
        if repair.get("status") == "PASS":
            expect(errors, repair.get("duplicate_replay") == "PASS" and repair.get("rollback_proof") == "PASS" and repair.get("count_gate") == "PASS" and repair.get("unique_candidate") is True, "repair_success_gates")
            expect(errors, repair.get("issue_derived_repair_count") == 6, "repair_count")
    else:
        expect(errors, repair.get("issue_derived_repair_count") == 5, "no_repair_count")

    source_manifest = load("reactome_source_hash_manifest_batch077.json")
    matrix = load("reactome_class_field_relationship_matrix_batch077.json")
    trace = load("batch077_schema_field_traceability.json")
    cycle = load("reactome_pathway_cycle_reference_batch077.json")
    generation = load("reactome_generation_validation_boundary_batch077.json")
    unresolved = load("reactome_unresolved_source_questions_batch077.json")
    expect(errors, source_manifest.get("status") == "PASS" and all(item.get("commit") and item.get("sha256") for item in source_manifest.get("files", [])), "reactome_source_hashes")
    expect(errors, matrix.get("status") == "PASS" and all(item.get("verification_status") == "PASS" and item.get("source_sha256") and item.get("reactome_commit") for item in matrix.get("records", [])), "reactome_mappings")
    expect(errors, trace.get("status") == "PASS" and trace.get("coverage_percent") == 100.0 and trace.get("covered_field_count") == trace.get("field_count"), "schema_traceability")
    expect(errors, cycle.get("literal_source_comment_verified") is True and cycle.get("controllergate_cycle_policy", {}).get("excluded_edges") and cycle.get("controllergate_cycle_policy", {}).get("silent_edge_deletion") is False, "cycle_policy")
    expect(errors, generation.get("claim_promotion_requires_independent_validation") is True and generation.get("staging_success_is_validation_success") is False, "generation_validation_boundary")
    expect(errors, unresolved.get("unresolved_receives_implementation_credit") is False and all(item.get("verification_status") == "SOURCE_NOT_RESOLVED" for item in unresolved.get("records", [])), "unresolved_source_credit")

    final = load("batch077_final_decision.json")
    expect(errors, final.get("status") == "PASS" and final.get("validated_protocol") == "v2.19", "final")
    expect(errors, final.get("AMDS_CAUSAL_EVIDENCE") == "AMDS_CAUSAL_EVIDENCE_HARDENED" and final.get("AMDS_PROSPECTIVE_EFFECTIVENESS") == "NOT_ESTABLISHED", "amds_claim")
    expect(errors, final.get("ROUTING_MEMORY_MECHANISM") == "DEMONSTRATED_NO_EFFECT" and final.get("memory_lift") == "not_demonstrated", "memory_claim")
    expect(errors, final.get("native_external_repair_count") == 4 and final.get("issue_derived_repair_count") in {5, 6}, "final_counts")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed" and final.get("self_maintaining_software") == "false/not_demonstrated" and final.get("live_connectors") == "inactive", "claim_boundary")

    if errors:
        print("Batch077 typed event pathway memory v2 audit: FAIL")
        print("errors:", ", ".join(errors))
        return 1
    print(f"Batch077 typed event pathway memory v2 audit: PASS ({manifest_count} manifest entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
