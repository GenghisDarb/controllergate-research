from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any, Iterable

from .primitives import PRIMITIVE_CONTRACTS
from .scenarios import CHAPTER_ENGINEERING_SCOPES
from .value_bound import ValueBindingResolver, canonical_hash, compile_value_bound_candidate


def _actual_event(record: dict[str, Any], candidate: dict[str, Any], resolver: ValueBindingResolver) -> dict[str, Any]:
    values = {
        field: resolver.resolve(record, field)
        for field in (
            "source_value_binding", "entity_set_members", "candidate_set_members", "complex_components",
            "entity_compartments", "source_destination_transitions", "stable_event_edges",
            "normal_variant_graph", "modification_details", "catalyst_details", "regulator_details",
            "edition_lineage",
        )
    }
    participants = values["source_value_binding"]
    inputs = [row for row in participants if row.get("role") in {"input", "required_input"}]
    outputs = [row for row in participants if row.get("role") == "output"]
    positive = [row for row in values["regulator_details"] if "positive" in str(row.get("regulation_class", "")).lower()]
    negative = [row for row in values["regulator_details"] if "negative" in str(row.get("regulation_class", "")).lower()]
    source_values: dict[str, Any] = {
        "event_type": record["source_class"],
        "entity_state": participants or {"state": "explicit_empty"},
        "members": values["complex_components"] or values["entity_set_members"] or participants,
        "candidates": values["candidate_set_members"] or values["entity_set_members"] or participants,
        "demonstrated_member": (values["entity_set_members"] or participants or [{"state": "explicit_empty"}])[0],
        "compartment": values["entity_compartments"] or {"state": "explicit_empty"},
        "destination": values["source_destination_transitions"] or values["entity_compartments"] or {"state": "explicit_empty"},
        "target": outputs or participants or {"state": "explicit_empty"},
        "catalyst": values["catalyst_details"] or {"state": "explicit_empty"},
        "cofactor": [row for row in participants if row.get("role") == "required_input"] or {"state": "explicit_empty"},
        "positive_signal": positive or {"state": "explicit_empty"},
        "negative_signal": negative or {"state": "explicit_empty"},
        "checkpoint": values["stable_event_edges"] or {"state": "no_predecessor"},
        "feedback": values["stable_event_edges"] or participants,
        "phase": values["stable_event_edges"] or {"phase": "source_sequence"},
        "phase_transition": values["stable_event_edges"] or {"phase": "source_sequence"},
        "resource_delta": max(0, len(inputs) - len(outputs)),
        "flow_limit": len(inputs) + len(outputs),
        "reverse_transition": {"reverse": False, "source_outputs": outputs, "destination_inputs": inputs},
        "commit_transition": {"reverse": False, "inputs": inputs, "outputs": outputs},
        "cycle_step": values["stable_event_edges"] or participants,
        "quality_measurement": {"evidence_maturity": record["evidence_maturity"], "tag_semantics": "conformance"},
        "progress_clock": values["edition_lineage"] or {"state": "source_time_not_exposed"},
        "collision_key": values["complex_components"] or participants,
        "rescue_route": values["stable_event_edges"] or participants,
        "recyclable_resource": outputs or participants,
        "degradation_target": inputs or participants,
        "selected_cleanup_target": (inputs or participants or [{"state": "explicit_empty"}])[0],
        "cleanup_scope": inputs or participants,
        "conformance_contract": {"source_class": record["source_class"], "evidence_maturity": record["evidence_maturity"]},
        "modification": values["modification_details"] or {"state": "explicit_empty"},
        "access_policy": values["entity_compartments"] or {"state": "explicit_empty"},
        "parent_identity": values["edition_lineage"] or {"source_occurrence_identity": record["source_occurrence_identity"]},
        "inference_source": {"evidence_maturity": record["evidence_maturity"]},
        "normal_variant_pair": values["normal_variant_graph"] or {"state": "source_explicitly_empty"},
        "negative_outcome": {"source_class": record["source_class"], "explicit": record["source_class"] == "FailedReaction"},
        "residual_fraction": 0.5 if values["normal_variant_graph"] else 1.0,
        "alternate_route": values["stable_event_edges"] or participants,
        "untrusted_controller": {"verifier_disabled": False, "source": record["source_stable_id"]},
        "bypass_route": values["normal_variant_graph"] or values["stable_event_edges"] or participants,
        "containment_scope": {"scope": "local", "compartments": values["entity_compartments"]},
        "termination_token": {"source_occurrence_identity": record["source_occurrence_identity"], "authorized": True},
        "sensor_reading": inputs or participants,
        "channel_message": outputs or participants,
        "actuation_request": {"outputs": outputs, "authorized": True},
        "clearance_target": outputs or participants,
    }
    event = {"source_occurrence_identity": record["source_occurrence_identity"]}
    for primitive in candidate["generic_primitive_bindings"]:
        required = PRIMITIVE_CONTRACTS[primitive]["required_event_field"]
        event[required] = source_values[required]
    return event


def select_source_bound_scenarios(records: Iterable[dict[str, Any]], resolver: ValueBindingResolver) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_chapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["chapter_identity"] in CHAPTER_ENGINEERING_SCOPES:
            by_chapter[record["chapter_identity"]].append(record)
    scenarios: list[dict[str, Any]] = []
    selections: list[dict[str, Any]] = []
    for index, chapter in enumerate(CHAPTER_ENGINEERING_SCOPES, 1):
        options = by_chapter.get(chapter, [])
        if not options:
            raise ValueError(f"no RPIR v2.1 source occurrence for chapter {chapter}")
        options.sort(key=lambda row: (
            row["source_class"] == "BlackBoxEvent",
            row["evidence_maturity"] != "DIRECT_CURATED",
            -sum(len((row.get(field, {}).get("value") or [])) for field in row if isinstance(row.get(field), dict)),
            row["source_stable_id"],
            row["source_occurrence_identity"],
        ))
        record = options[0]
        candidate, _ = compile_value_bound_candidate(record, resolver)
        event = _actual_event(record, candidate, resolver)
        scenario_id = f"reactome-r97-value-bound-{index:02d}"
        scenario = {
            "scenario_id": scenario_id,
            "chapter": chapter,
            "source_stable_id": record["source_stable_id"],
            "source_occurrence_identity": record["source_occurrence_identity"],
            "source_graph_hash": record["source_graph_hash"],
            "source_evidence_maturity": record["evidence_maturity"],
            "primitive_ids": candidate["generic_primitive_bindings"],
            "source_event": event,
            "source_derived_invariant": "all compiled primitive inputs resolve from the selected source graph",
            "source_derived_negative_control": "remove the first primitive precondition and require BLOCK",
            "chapter_specific_adversarial_control": "request repair authority and require BLOCK",
            "authority": "shadow_non_authorizing",
            "producer": "controllergate.isomorphism.source_bound:select_source_bound_scenarios",
            "execution_depth": "source_value_bound_scenario_preregistration",
        }
        scenarios.append(scenario)
        selections.append({
            "chapter": chapter,
            "scenario_id": scenario_id,
            "selected_before_execution": True,
            "selection_order": index,
            "source_stable_id": record["source_stable_id"],
            "source_occurrence_identity": record["source_occurrence_identity"],
            "source_graph_hash": record["source_graph_hash"],
            "selection_contract_sha256": canonical_hash([chapter, record["source_occurrence_identity"], index]),
        })
    return scenarios, selections


def integrated_source_bound_scenario(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    required = (
        "SENSOR_TRANSDUCER", "EVENT_CHANNEL", "TRANSLOCATION", "CHECKPOINT", "RESOURCE_FLUX", "ACTUATOR",
        "QUALITY_CONTROL", "STALL_DETECTION", "COLLISION_DETECTION", "RESCUE", "NORMAL_VARIANT_PAIR",
        "RESIDUAL_ACTIVITY", "REDUNDANCY_COMPENSATION", "RESISTANCE_BYPASS", "SELECTIVE_CLEANUP", "LINEAGE",
    )
    values: dict[str, Any] = {"source_occurrence_identity": "integrated-release97-source-bound"}
    parents = []
    for primitive in required:
        field = PRIMITIVE_CONTRACTS[primitive]["required_event_field"]
        source = next((scenario for scenario in scenarios if field in scenario["source_event"]), None)
        origin_field = field
        if source is None:
            for fallback in ("entity_state", "members", "event_type", "compartment", "checkpoint"):
                source = next((scenario for scenario in scenarios if fallback in scenario["source_event"]), None)
                if source is not None:
                    origin_field = fallback
                    break
        if source is None:
            raise ValueError(f"integrated source value unavailable for {primitive}")
        values[field] = source["source_event"][origin_field]
        parents.append({"primitive": primitive, "scenario_id": source["scenario_id"], "source_stable_id": source["source_stable_id"], "source_value_field": origin_field})
    return {
        "scenario_id": "reactome-r97-integrated-value-bound",
        "chapter": "cross_chapter_integrated",
        "source_stable_id": "R-HSA-integrated",
        "source_occurrence_identity": "integrated-release97-source-bound",
        "source_graph_hash": canonical_hash(parents),
        "primitive_ids": list(required),
        "source_event": values,
        "source_value_parents": parents,
        "authority": "shadow_non_authorizing",
        "producer": "controllergate.isomorphism.source_bound:integrated_source_bound_scenario",
        "execution_depth": "cross_chapter_source_value_composition",
    }
