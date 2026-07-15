from __future__ import annotations

from typing import Any


RPIR_VERSION = "controllergate-rpir-v1"
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
