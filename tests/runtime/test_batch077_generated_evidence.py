from __future__ import annotations

import json
from pathlib import Path

from controllergate.pathways.validator import validate_pathway

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch077_typed_event_pathway_memory_v2"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line]


def test_batch076_artifact_identity() -> None:
    value = load("batch076_artifact_ingest.json")
    assert value["observed_size_bytes"] == 658_771
    assert value["observed_sha256"] == "b9c769514a0a02ef5937b6ccce24c12d1a759a2c18eecfb3717c0273a590b2c5"
    assert value["file_count"] == 210
    assert value["raw_zip_committed"] is False


def test_flat_memory_degeneracy_is_honest() -> None:
    value = load("batch076_memory_corpus_diversity_audit.json")
    assert value["record_count"] == 9
    assert value["degenerate_flat_topology"] is True
    assert all(item["unique_count"] == 1 for item in value["field_diversity"].values())


def test_pathways_are_proof_bound_and_diverse() -> None:
    records = jsonl("routing_event_pathway_corpus_v2.jsonl")
    manifest = load("routing_event_pathway_manifest_v2.json")
    assert len(records) == 9
    assert all(validate_pathway(record)["status"] == "PASS" for record in records)
    assert len({record["pathway_hash"] for record in records}) == 9
    assert manifest["unique_event_type_sequences"] > 1
    assert manifest["unique_compartment_transition_sequences"] > 1


def test_shuffled_control_is_materially_distinct() -> None:
    real = jsonl("routing_event_pathway_corpus_v2.jsonl")
    shuffled = jsonl("shuffled_routing_event_pathway_corpus_v2.jsonl")
    manifest = load("shuffled_pathway_memory_manifest_v2.json")
    assert len(real) == len(shuffled) == 9
    assert manifest["real_corpus_hash"] != manifest["shuffled_corpus_hash"]
    assert manifest["distribution_comparison"]["marginals_preserved"] is True
    assert any(left["terminal_ownership"] != right["terminal_ownership"] or left["branch_points"] != right["branch_points"] for left, right in zip(real, shuffled))


def test_graph_projection_has_component_scores_and_provenance() -> None:
    records = jsonl("candidate_pathway_projection_records.jsonl")
    assert len(records) == 18
    assert all(len(record["component_scores"]) == 11 for record in records)
    assert all(record["projection_evidence_hash"] and record["independent_verifier"] and record["review_state"] for record in records)
    assert all(record["same_repository_excluded"] is True for record in records)
    assert len({tuple(record["component_scores"].values()) for record in records}) > 1


def test_cognicore_expected_and_incident_pathways_pair() -> None:
    normal = load("cognicore_normal_expected_pathway.json")
    incident = load("cognicore_observed_incident_pathway.json")
    divergence = load("cognicore_normal_incident_divergence.json")
    assert normal["incident_variant_pathway"] == incident["pathway_id"]
    assert incident["normal_reference_pathway"] == normal["pathway_id"]
    assert divergence["expected_output"] == "CogniCore Studio"
    assert divergence["observed_output"] == "<title>CogniCore Observability</title>"
    assert divergence["first_divergence_event"]


def test_hordeforge_runtime_scratch_and_source_preservation() -> None:
    value = load("hordeforge_runtime_compartment_correction.json")
    assert value["source_read_only"] is True
    assert value["runtime_scratch_writable"] is True
    assert value["source_hashes_unchanged"] is True
    assert value["harness_view_source_hashes_match"] is True
    assert value["prior_oserror_removed"] is True


def test_pathway_gap_probes_create_events_and_update_state() -> None:
    summary = load("pathway_gap_amds_arm_summary.json")
    events = jsonl("pathway_gap_probe_event_ledger.jsonl")
    assert summary["accepted_probes"] == summary["event_count"] == len(events)
    assert summary["posterior_updates"] == len(events)
    assert summary["backtracking_count"] > 0
    assert all(event["selected_gap"] in event["unresolved_pathway_before_probe"] for event in events)
    assert all(event["resolved_edges"] and event["pathway_state_hash"] for event in events)


def test_memory_arms_are_isolated_and_patch_free() -> None:
    arms = load("pathway_gap_amds_arm_summary.json")["records"]
    assert len(arms) == 12
    assert {arm["memory_condition"] for arm in arms} == {"REAL_PATHWAY_MEMORY", "NO_MEMORY", "SHUFFLED_PATHWAY_MEMORY"}
    assert all(arm["observation_sharing"] is False for arm in arms)
    assert all(arm["patch_authority"] is False for arm in arms)


def test_blinded_ground_truth_and_no_memory_repair_boundary() -> None:
    ground = load("batch077_blinded_ground_truth.json")
    repair = load("batch077_authoritative_no_memory_repair.json")
    assert ground["arms_sealed_before_adjudication"] is True
    assert ground["memory_conditions_available"] is False
    assert repair["memory_condition"] == "NO_MEMORY"
    assert repair["patch_content_from_memory"] is False
    assert repair["attempts"] <= 1
    if repair["status"] == "PASS":
        assert repair["duplicate_replay"] == repair["count_gate"] == "PASS"
        assert repair["issue_derived_repair_count"] == 6


def test_reactome_source_gate_and_schema_traceability() -> None:
    source = load("reactome_source_hash_manifest_batch077.json")
    matrix = load("reactome_class_field_relationship_matrix_batch077.json")
    trace = load("batch077_schema_field_traceability.json")
    unresolved = load("reactome_unresolved_source_questions_batch077.json")
    assert source["status"] == matrix["status"] == trace["status"] == "PASS"
    assert all(item["sha256"] and item["commit"] for item in source["files"])
    assert all(item["source_sha256"] and item["verification_status"] == "PASS" for item in matrix["records"])
    assert trace["coverage_percent"] == 100.0
    assert unresolved["unresolved_receives_implementation_credit"] is False


def test_claim_boundary() -> None:
    final = load("batch077_final_decision.json")
    assert final["validated_protocol"] == "v2.19"
    assert final["AMDS_PROSPECTIVE_EFFECTIVENESS"] == "NOT_ESTABLISHED"
    assert final["ROUTING_MEMORY_MECHANISM"] == "DEMONSTRATED_NO_EFFECT"
    assert final["memory_lift"] == "not_demonstrated"
    assert final["native_external_repair_count"] == 4
    assert final["issue_derived_repair_count"] in {5, 6}
    assert final["self_maintaining_software"] == "false/not_demonstrated"
    assert final["live_connectors"] == "inactive"
