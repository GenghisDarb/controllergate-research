"""Source-grounded Reactome reaction-to-shadow-scenario compiler.

The compiler consumes public RPIR v2.1 relations.  It does not assign
primitives by chapter position and it never grants causal or repair authority.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable


WRAPPED_REACTION_FIELDS = (
    "candidate_set_members",
    "catalyst_details",
    "complex_components",
    "edition_lineage",
    "entity_compartments",
    "entity_set_members",
    "literature_records",
    "modification_details",
    "nested_membership_closure",
    "normal_variant_graph",
    "regulator_details",
    "source_destination_transitions",
    "source_value_binding",
    "stable_event_edges",
    "stoichiometry",
    "timing_annotations",
)

FIELD_PRIMITIVES = {
    "candidate_set_members": ("CANDIDATE_SET", "DEMONSTRATED_MEMBER"),
    "catalyst_details": ("CATALYST", "COFACTOR"),
    "complex_components": ("COMPLEX_ASSEMBLY",),
    "edition_lineage": ("LINEAGE",),
    "entity_compartments": ("COMPARTMENT",),
    "entity_set_members": ("ENTITY_STATE", "CANDIDATE_SET"),
    "literature_records": ("EVENT_CONTRACT",),
    "modification_details": ("MODIFICATION_CODE",),
    "nested_membership_closure": ("PROCESSIVE_CYCLE",),
    "normal_variant_graph": ("NORMAL_VARIANT_PAIR", "NEGATIVE_REACTION"),
    "regulator_details": ("POSITIVE_REGULATOR", "NEGATIVE_REGULATOR"),
    "source_destination_transitions": ("TRANSLOCATION", "TARGETING"),
    "source_value_binding": ("EVENT_CONTRACT", "IRREVERSIBLE_REACTION"),
    "stable_event_edges": ("CHECKPOINT", "PHASE_MACHINE"),
    "stoichiometry": ("RESOURCE_FLUX",),
    "timing_annotations": ("STALL_DETECTION", "QUALITY_CONTROL"),
}

OPERATION_FAMILIES = (
    "source_identity_resolution",
    "compartment_materialization",
    "required_input_acquisition",
    "cofactor_materialization",
    "activation_gate",
    "inhibitor_check",
    "ordered_stage_transition",
    "parallel_pathway_exploration",
    "alternative_route_recovery",
    "failed_reaction_capture",
    "rollback_and_quarantine",
    "duplicate_replay",
    "proof_ledger_commit",
    "safe_termination",
)


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def source_has_value(record: dict[str, Any], field: str) -> bool:
    wrapped = record.get(field)
    return (
        isinstance(wrapped, dict)
        and wrapped.get("state") == "SOURCE_VALUE"
        and wrapped.get("value") not in (None, [], {}, "")
    )


def derive_primitive_ids(record: dict[str, Any]) -> list[str]:
    """Derive primitives only from present reaction relations."""
    ordered = ["EVENT_CONTRACT"]
    for field in WRAPPED_REACTION_FIELDS:
        if source_has_value(record, field):
            for primitive in FIELD_PRIMITIVES[field]:
                if primitive not in ordered:
                    ordered.append(primitive)
    return ordered


def field_origin(record: dict[str, Any], field: str) -> str:
    if field in {
        "source_stable_id",
        "source_database_id",
        "source_class",
        "source_occurrence_identity",
        "chapter_identity",
        "display_name",
        "evidence_maturity",
        "source_graph_hash",
    }:
        return "DIRECT_REACTOME_VALUE"
    wrapped = record.get(field)
    if not isinstance(wrapped, dict):
        return "UNKNOWN"
    if wrapped.get("state") == "SOURCE_VALUE":
        return "RPIR_STRUCTURAL_RELATION"
    if wrapped.get("state") in {
        "SOURCE_EXPLICITLY_EMPTY",
        "SOURCE_NOT_APPLICABLE",
        "SOURCE_NOT_EXPOSED_BY_FORMAT",
        "PARSER_FAILED",
        "UNRESOLVED_REFERENCE",
    }:
        return "DERIVED_REACTOME_VALUE"
    return "UNKNOWN"


def operation_sequence(record: dict[str, Any]) -> list[str]:
    operations = ["source_identity_resolution"]
    if source_has_value(record, "entity_compartments") or source_has_value(
        record, "source_destination_transitions"
    ):
        operations.append("compartment_materialization")
    if source_has_value(record, "source_value_binding"):
        operations.append("required_input_acquisition")
    if source_has_value(record, "catalyst_details"):
        operations.append("cofactor_materialization")
    if source_has_value(record, "stable_event_edges"):
        operations.extend(("activation_gate", "ordered_stage_transition"))
    if source_has_value(record, "regulator_details"):
        operations.append("inhibitor_check")
    if source_has_value(record, "nested_membership_closure"):
        operations.append("parallel_pathway_exploration")
    if source_has_value(record, "normal_variant_graph"):
        operations.extend(("alternative_route_recovery", "failed_reaction_capture"))
    if source_has_value(record, "timing_annotations"):
        operations.append("rollback_and_quarantine")
    operations.extend(("duplicate_replay", "proof_ledger_commit", "safe_termination"))
    return list(dict.fromkeys(operations))


def compile_source_grounded_scenario(record: dict[str, Any]) -> dict[str, Any]:
    primitives = derive_primitive_ids(record)
    operations = operation_sequence(record)
    lineage = {
        field: {
            "origin": field_origin(record, field),
            "state": record[field].get("state"),
            "source": record[field].get("source"),
        }
        for field in WRAPPED_REACTION_FIELDS
    }
    scenario = {
        "schema": "ReactomeSourceGroundedScenarioV2",
        "scenario_id": f"reactome-r97-source-grounded:{record['source_occurrence_identity']}",
        "reaction": record["source_stable_id"],
        "pathway": record["chapter_identity"],
        "source_object": record["source_occurrence_identity"],
        "source_hash": record["source_graph_hash"],
        "primitive_ids": primitives,
        "operation_families": operations,
        "field_lineage": lineage,
        "round_robin_authority": False,
        "authority_allowed": "nonauthorizing structural planning input",
        "authority_forbidden": [
            "biological proof",
            "causal fact",
            "ownership",
            "patch",
            "repair count",
            "release",
        ],
    }
    scenario["scenario_hash"] = canonical_hash(scenario)
    return scenario


def compile_scenarios(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [compile_source_grounded_scenario(record) for record in records]
