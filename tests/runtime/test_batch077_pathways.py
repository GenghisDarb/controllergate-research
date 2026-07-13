from __future__ import annotations

from controllergate.pathways.compartment import ALL_COMPARTMENTS
from controllergate.pathways.entity import Entity
from controllergate.pathways.event import Event
from controllergate.pathways.pathway import Pathway
from controllergate.pathways.projection import Projection
from controllergate.pathways.regulation import Regulator
from controllergate.pathways.validator import validate_event, validate_pathway, validate_transition

SHA = "a" * 64


def entity(compartment: str, role: str, suffix: str = "") -> Entity:
    return Entity("evidence", SHA[:-len(suffix)] + suffix if suffix else SHA, compartment, role)


def valid_event(**overrides) -> Event:
    required = entity("source", "required_input")
    values = {
        "event_type": "source_identity",
        "schema_type": "evidence_transition",
        "compartment": "source",
        "input_entities": (required,),
        "required_input_entities": (required,),
        "catalyst_or_executor": entity("authorization", "executor", "b"),
        "positive_regulators": (Regulator("authorization", "positive", "PASS", "proof.json"),),
        "negative_regulators": (Regulator("forbidden_evidence", "negative", "PASS", "firewall.json"),),
        "output_entities": (entity("diagnostic", "output", "c"),),
        "expected_output": "verified",
        "observed_output": "verified",
        "evidence_references": ("proof.json",),
    }
    values.update(overrides)
    return Event(**values)


def test_required_compartment_set_is_complete() -> None:
    assert ALL_COMPARTMENTS == {
        "artifact", "source", "provider", "runtime", "harness", "test",
        "authorization", "diagnostic", "memory", "patch", "validation",
        "rollback", "proof",
    }


def test_stable_event_ids_and_versions() -> None:
    first = valid_event()
    second = valid_event()
    assert first.event_id == second.event_id
    assert first.to_record()["event_version"] == 1
    changed = valid_event(event_version=2)
    assert changed.event_id != first.event_id


def test_same_payload_has_compartment_specific_context_identity() -> None:
    source = entity("source", "input")
    runtime = entity("runtime", "input")
    assert source.underlying_identity == runtime.underlying_identity
    assert source.entity_id != runtime.entity_id


def test_required_input_enforcement_and_catalyst_separation() -> None:
    event = valid_event()
    assert event.required_input_entities[0].entity_id != event.catalyst_or_executor.entity_id
    broken = event.to_record()
    broken["input_entities"] = []
    assert "required_input_missing" in validate_event(broken)["errors"]


def test_positive_and_negative_regulators_gate_transition() -> None:
    assert validate_event(valid_event().to_record())["status"] == "PASS"
    blocked_positive = valid_event(positive_regulators=(Regulator("auth", "positive", "UNKNOWN", "p"),))
    assert "positive_regulator_not_passed" in validate_event(blocked_positive.to_record())["errors"]
    blocked_negative = valid_event(negative_regulators=(Regulator("leak", "negative", "BLOCK", "p"),))
    assert "negative_regulator_blocked" in validate_event(blocked_negative.to_record())["errors"]


def test_normal_incident_links_are_stable_fields() -> None:
    event = valid_event(normal_reference_event="event:normal", incident_variant_event="event:incident")
    record = event.to_record()
    assert record["normal_reference_event"] == "event:normal"
    assert record["incident_variant_event"] == "event:incident"


def test_direct_and_inferred_edges_require_distinct_provenance() -> None:
    direct = valid_event().to_record()
    assert direct["knowledge_status"] == "DIRECTLY_OBSERVED"
    inferred = valid_event(knowledge_status="INFERRED_FROM_PATHWAY", inferred_from_links=()).to_record()
    assert "inference_provenance_missing" in validate_event(inferred)["errors"]


def test_projection_records_provenance_and_forbidden_influences() -> None:
    projection = Projection(
        source_pathway_id="pathway:source", source_pathway_version=2,
        target_pathway_id="pathway:target", knowledge_status="STRUCTURALLY_PROJECTED",
        mapped_event_pairs=(("a", "b"),), unmapped_source_events=(),
        unmapped_target_events=("c",), matched_edge_types=("required_input",),
        compartment_compatibility=1.0, regulation_compatibility=0.5,
        normal_incident_compatibility=0.0, projection_confidence="NOT_ESTABLISHED",
        projection_evidence_hash=SHA, independent_verifier="batch077_audit",
        review_state="MANUAL_REVIEW",
    ).to_record()
    assert projection["source_pathway_version"] == 2
    assert "patch_authorization" in projection["forbidden_influences"]
    assert projection["review_state"] == "MANUAL_REVIEW"


def test_pathway_validation_and_proof_binding() -> None:
    pathway = Pathway("episode-1", 2, (valid_event(),), proof_references=("proof.json",)).to_record()
    assert validate_pathway(pathway)["status"] == "PASS"
    pathway["proof_references"] = []
    assert "proof_lineage_missing" in validate_pathway(pathway)["errors"]


def test_transition_requires_authorization_verification_and_ledger() -> None:
    record = valid_event().to_record()
    assert validate_transition(record, executor_authorized=True, semantic_verification="PASS", ledger_appended=True)["status"] == "PASS"
    result = validate_transition(record, executor_authorized=False, semantic_verification="FAIL", ledger_appended=False)
    assert result["status"] == "BLOCK"
    assert set(result["errors"]) >= {"executor_not_authorized", "semantic_verification_failed", "event_ledger_not_appended"}
