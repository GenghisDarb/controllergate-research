from __future__ import annotations

from typing import Any


RPIR_VERSION = "controllergate-rpir-v1"
RPIR_V2_VERSION = "controllergate-rpir-v2"
FIELD_STATES = (
    "SOURCE_VALUE",
    "SOURCE_EXPLICITLY_EMPTY",
    "SOURCE_NOT_APPLICABLE",
    "SOURCE_NOT_EXPOSED_BY_FORMAT",
    "PARSER_FAILED",
    "UNRESOLVED_REFERENCE",
)
EVENT_TYPES = ("transition", "binding", "dissociation", "uncertain", "omitted")
EVIDENCE_CLASSES = (
    "DIRECT_CURATED",
    "INFERRED_ORTHOLOGY",
    "INFERRED_RELATED_MECHANISM",
    "UNCERTAIN_BLACK_BOX",
    "OMITTED_DETAIL",
    "DISEASE_VARIANT_CURATED",
    "NEGATIVE_REACTION_CURATED",
    "UNRESOLVED",
)


def rpir_schema() -> dict[str, Any]:
    fields = [
        "stable_source_identity", "chapter_identity", "pathway_hierarchy", "source_event_type",
        "source_evidence_maturity", "species", "orthology_status", "normal_or_variant_role",
        "inputs", "required_inputs", "outputs", "catalyst_activity", "active_unit",
        "positive_regulators", "negative_regulators", "entity_sets", "candidate_sets",
        "demonstrated_members", "complex_membership", "stoichiometry", "compartment",
        "source_compartment", "destination_compartment", "transport_or_translocation",
        "modifications", "preceding_events", "following_events", "reversibility",
        "timing_annotations", "uncertainty", "omitted_mechanism", "negative_reaction_semantics",
        "literature_references", "edition_lineage",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": RPIR_VERSION,
        "title": "Reactome Pathway Intermediate Representation event",
        "type": "object",
        "required": fields,
        "properties": {name: {} for name in fields},
        "source_event_types": list(EVENT_TYPES),
        "software_evidence_classes": list(EVIDENCE_CLASSES),
        "authority_rule": "source evidence defines candidate laws and tests but never grants repair or product authority",
    }


def maturity_for(*, event_type: str, inferred_from: str | None, chapter: str, text: str) -> str:
    lowered = text.lower()
    if event_type == "uncertain":
        return "UNCERTAIN_BLACK_BOX"
    if event_type == "omitted":
        return "OMITTED_DETAIL"
    if inferred_from:
        return "INFERRED_ORTHOLOGY"
    if "does not react" in lowered or "failed reaction" in lowered:
        return "NEGATIVE_REACTION_CURATED"
    if chapter == "Disease":
        return "DISEASE_VARIANT_CURATED"
    return "DIRECT_CURATED"


def field_value(value: Any, *, state: str, source: str, note: str | None = None) -> dict[str, Any]:
    """Wrap an RPIR v2 field without collapsing absent-source states."""
    if state not in FIELD_STATES:
        raise ValueError(f"invalid RPIR v2 field state: {state}")
    if state == "SOURCE_VALUE" and value is None:
        raise ValueError("SOURCE_VALUE requires a value")
    if state != "SOURCE_VALUE" and value not in (None, [], {}, ""):
        raise ValueError(f"{state} cannot carry an asserted value")
    result = {"state": state, "source": source, "value": value}
    if note:
        result["note"] = note
    return result


def rpir_v2_schema() -> dict[str, Any]:
    field_names = [
        "participants", "catalysts", "active_units", "positive_regulators", "negative_regulators",
        "entity_sets", "candidate_sets", "complexes", "stoichiometry", "compartments",
        "modifications", "preceding_events", "following_events", "normal_event", "variant_events",
        "orthology_sources", "literature_references", "edition_lineage", "timing_annotations",
    ]
    wrapped = {
        "type": "object",
        "required": ["state", "source", "value"],
        "properties": {
            "state": {"enum": list(FIELD_STATES)},
            "source": {"type": "string", "minLength": 1},
            "value": {},
            "note": {"type": "string"},
        },
        "additionalProperties": False,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": RPIR_V2_VERSION,
        "title": "ControllerGate structured pathway event",
        "type": "object",
        "required": [
            "rpir_version", "source_stable_id", "source_database_id", "source_class",
            "source_occurrence_identity", "chapter_identity", "display_name", "evidence_maturity",
            *field_names,
        ],
        "properties": {
            "rpir_version": {"const": RPIR_V2_VERSION},
            "source_stable_id": {"type": "string", "pattern": "^R-HSA-[0-9]+$"},
            "source_database_id": {"type": "integer", "minimum": 1},
            "source_class": {"type": "string", "minLength": 1},
            "source_occurrence_identity": {"type": "string", "minLength": 16},
            "chapter_identity": {"type": "string", "minLength": 1},
            "display_name": {"type": "string", "minLength": 1},
            "evidence_maturity": {"enum": list(EVIDENCE_CLASSES)},
            **{name: wrapped for name in field_names},
        },
        "field_states": list(FIELD_STATES),
        "authority_rule": "structured source values define candidate translations; only ControllerGate execution may grant software authority",
    }
