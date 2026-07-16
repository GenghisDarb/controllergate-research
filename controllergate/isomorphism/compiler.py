from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from .primitives import GENERIC_PRIMITIVES, PRIMITIVE_CONTRACTS


def _identity(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


KEYWORD_PRIMITIVES = {
    "transport": "TRANSLOCATION", "translocat": "TRANSLOCATION", "import": "TARGETING", "export": "TARGETING",
    "bind": "COMPLEX_ASSEMBLY", "complex": "COMPLEX_ASSEMBLY", "catal": "CATALYST", "cofactor": "COFACTOR",
    "activate": "POSITIVE_REGULATOR", "inhibit": "NEGATIVE_REGULATOR", "checkpoint": "CHECKPOINT",
    "feedback": "FEEDBACK_LOOP", "oscillat": "OSCILLATOR", "phase": "PHASE_MACHINE", "flux": "RESOURCE_FLUX",
    "flow": "FLOW_CONTROL", "recycl": "RECYCLING", "degrad": "DEGRADATION", "cleanup": "SELECTIVE_CLEANUP",
    "fold": "FOLDING_OR_CONFORMANCE", "modif": "MODIFICATION_CODE", "access": "ACCESSIBILITY_STATE",
    "lineage": "LINEAGE", "ortholog": "ORTHOLOGY", "variant": "NORMAL_VARIANT_PAIR", "disease": "NORMAL_VARIANT_PAIR",
    "residual": "RESIDUAL_ACTIVITY", "redundan": "REDUNDANCY_COMPENSATION", "resistan": "RESISTANCE_BYPASS",
    "terminate": "CONTROLLED_TERMINATION", "sensor": "SENSOR_TRANSDUCER", "signal": "EVENT_CHANNEL",
    "channel": "EVENT_CHANNEL", "contract": "ACTUATOR", "clearance": "DISTRIBUTION_CLEARANCE",
}


def compile_candidate(record: dict[str, Any]) -> dict[str, Any]:
    text = " ".join((record.get("title", ""), record.get("description_excerpt", ""))).lower()
    primitives = ["EVENT_CONTRACT", "ENTITY_STATE"]
    for keyword, primitive in KEYWORD_PRIMITIVES.items():
        if keyword in text and primitive not in primitives:
            primitives.append(primitive)
    if record.get("compartment") or record.get("source_compartment") or record.get("destination_compartment"):
        primitives.append("COMPARTMENT")
    if record.get("positive_regulators") and "POSITIVE_REGULATOR" not in primitives:
        primitives.append("POSITIVE_REGULATOR")
    if record.get("negative_regulators") and "NEGATIVE_REGULATOR" not in primitives:
        primitives.append("NEGATIVE_REGULATOR")
    if record.get("reversibility") == "reversible":
        primitives.append("REVERSIBLE_REACTION")
    elif record.get("reversibility") == "irreversible":
        primitives.append("IRREVERSIBLE_REACTION")
    if record.get("negative_reaction_semantics"):
        primitives.append("NEGATIVE_REACTION")
    if record.get("orthology_status") == "inferred":
        primitives.append("ORTHOLOGY")
    primitives = list(dict.fromkeys(item for item in primitives if item in GENERIC_PRIMITIVES))
    source_type = record.get("source_event_type")
    blocked = source_type in {"uncertain", "omitted"}
    translation_state = "BLOCKED_MISSING_SOURCE_DETAIL" if blocked else "SCHEMA_COMPILED"
    candidate = {
        "translation_candidate_id": _identity([record["source_occurrence_identity"], primitives]),
        "source_stable_id": record["stable_source_identity"],
        "source_occurrence_identity": record["source_occurrence_identity"],
        "source_chapter": record["chapter_identity"],
        "source_mechanism_summary": record.get("title"),
        "plain_engineering_translation": f"Validate and execute a typed {source_type} state contract using reusable primitives.",
        "candidate_generic_primitive_ids": primitives,
        "required_input_types": ["typed_event", "typed_state", "source_identity"],
        "output_types": ["mechanism_outcome", "test_assertion"],
        "state_transitions": [source_type],
        "compartment_semantics": {"source": record.get("source_compartment", []), "destination": record.get("destination_compartment", []), "memberships": record.get("compartment", [])},
        "regulators_and_checkpoints": {"positive": record.get("positive_regulators", []), "negative": record.get("negative_regulators", [])},
        "evidence_maturity": record.get("source_evidence_maturity"),
        "authority_allowed": ["candidate tests", "shadow execution"],
        "authority_forbidden": ["repair authorization", "production promotion", "software causal authority from source metadata"],
        "positive_test_template": "valid inputs satisfy the typed transition contract",
        "negative_test_template": "missing required input is rejected without state promotion",
        "adversarial_test_template": "source evidence maturity cannot be escalated by translation",
        "shadow_executable_identity": "controllergate.isomorphism.primitives:apply_primitive",
        "production_overlap": [],
        "potential_subsystem_targets": ["diagnostic_planning", "maintenance_simulation"],
        "translation_state": translation_state,
        "rejection_or_blocker_reason": "source event explicitly uncertain or omitted" if blocked else None,
        "reopen_condition": "additional release-bound source detail and independent review" if blocked else None,
        "producer": "controllergate.isomorphism.compiler",
        "execution_depth": "schema_translation",
        "semantic_scope": "candidate translation only",
    }
    return candidate


def compile_registry(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [compile_candidate(record) for record in records]


def _source_values(record: dict[str, Any], field: str) -> list[Any]:
    wrapped = record.get(field, {})
    if not isinstance(wrapped, dict) or wrapped.get("state") != "SOURCE_VALUE":
        return []
    value = wrapped.get("value")
    return value if isinstance(value, list) else [value]


def compile_structured_candidate(record: dict[str, Any]) -> dict[str, Any]:
    """Compile RPIR v2 topology into generic contracts without title routing."""
    primitives = ["EVENT_CONTRACT", "ENTITY_STATE"]
    participants = _source_values(record, "participants")
    catalysts = _source_values(record, "catalysts")
    positive = _source_values(record, "positive_regulators")
    negative = _source_values(record, "negative_regulators")
    compartments = _source_values(record, "compartments")
    modifications = _source_values(record, "modifications")
    preceding = _source_values(record, "preceding_events")
    normal = _source_values(record, "normal_event")
    inferred = _source_values(record, "orthology_sources")
    if any(item.get("class") == "Complex" for item in participants):
        primitives.append("COMPLEX_ASSEMBLY")
    if any(item.get("class") in {"DefinedSet", "EntitySet"} for item in participants):
        primitives.extend(["CANDIDATE_SET", "DEMONSTRATED_MEMBER"])
    if any(item.get("class") == "CandidateSet" for item in participants):
        primitives.append("CANDIDATE_SET")
    if compartments:
        primitives.append("COMPARTMENT")
    if catalysts:
        primitives.append("CATALYST")
    if positive:
        primitives.append("POSITIVE_REGULATOR")
    if negative:
        primitives.append("NEGATIVE_REGULATOR")
    if modifications:
        primitives.append("MODIFICATION_CODE")
    if preceding:
        primitives.append("CHECKPOINT")
    if normal:
        primitives.append("NORMAL_VARIANT_PAIR")
    if inferred:
        primitives.append("ORTHOLOGY")
    source_class = record["source_class"]
    if source_class == "FailedReaction":
        primitives.extend(["NEGATIVE_REACTION", "QUALITY_CONTROL"])
    elif source_class == "Polymerisation":
        primitives.extend(["PROCESSIVE_CYCLE", "IRREVERSIBLE_REACTION"])
    elif source_class == "Depolymerisation":
        primitives.extend(["DEGRADATION", "RECYCLING"])
    elif source_class == "CellDevelopmentStep":
        primitives.extend(["PHASE_MACHINE", "LINEAGE"])
    elif source_class == "BlackBoxEvent":
        primitives.append("QUALITY_CONTROL")
    else:
        primitives.append("IRREVERSIBLE_REACTION")
    primitives = list(dict.fromkeys(primitive for primitive in primitives if primitive in GENERIC_PRIMITIVES))
    missing_detail = not participants or source_class == "BlackBoxEvent"
    state = "BLOCKED_MISSING_SOURCE_DETAIL" if missing_detail else "SCHEMA_COMPILED"
    contracts = [PRIMITIVE_CONTRACTS[primitive] for primitive in primitives]
    topology = {
        "participant_count": len(participants), "catalyst_count": len(catalysts),
        "positive_regulator_count": len(positive), "negative_regulator_count": len(negative),
        "compartment_count": len(compartments), "modification_count": len(modifications),
        "preceding_event_count": len(preceding), "normal_event_count": len(normal),
    }
    graph_basis = {
        "source_database_id": record["source_database_id"], "source_class": source_class,
        "participants": participants, "catalysts": catalysts, "positive_regulators": positive,
        "negative_regulators": negative, "compartments": compartments, "modifications": modifications,
        "preceding_events": preceding, "normal_event": normal, "orthology_sources": inferred,
    }
    source_graph_hash = _identity(graph_basis)
    plain_translation = (
        f"Apply {len(primitives)} typed transition contracts to {len(participants)} participants, "
        f"{len(catalysts)} catalysts, {len(positive)} positive controls, {len(negative)} negative controls, "
        f"{len(compartments)} compartments, and {len(preceding)} predecessor constraints; graph {source_graph_hash[:16]}."
    )
    return {
        "translation_candidate_id": _identity([record["source_occurrence_identity"], primitives, "structured-v2"]),
        "source_stable_id": record["source_stable_id"],
        "source_database_id": record["source_database_id"],
        "source_occurrence_identity": record["source_occurrence_identity"],
        "source_chapter": record["chapter_identity"],
        "source_class": source_class,
        "source_mechanism_summary": record["display_name"],
        "source_graph_hash": source_graph_hash,
        "plain_engineering_translation": plain_translation,
        "candidate_generic_primitive_ids": primitives,
        "primitive_contract_ids": [contract["primitive_id"] for contract in contracts],
        "required_input_types": sorted({contract["required_event_field"] for contract in contracts}),
        "output_types": sorted({contract["effect_key"] for contract in contracts}),
        "structured_topology": topology,
        "preconditions": sorted(contract["required_event_field"] for contract in contracts),
        "state_transition": [contract["effect_key"] for contract in contracts],
        "postconditions": [f"state.{contract['effect_key']} is source-bound" for contract in contracts],
        "invariants": ["source occurrence identity is immutable", "translation cannot grant repair authority"],
        "compartment_constraints": {"count": len(compartments), "hash": _identity(compartments)},
        "catalyst_worker_constraints": {"count": len(catalysts), "hash": _identity(catalysts)},
        "positive_regulators": {"count": len(positive), "hash": _identity(positive)},
        "negative_regulators": {"count": len(negative), "hash": _identity(negative)},
        "resource_cofactor_constraints": {"count": sum(item.get("role") == "required_input" for item in participants), "hash": _identity([item for item in participants if item.get("role") == "required_input"])},
        "failure_terminals": [f"missing_{contract['required_event_field']}" for contract in contracts],
        "compensating_actions": [contract["negative_control"] for contract in contracts],
        "uncertainty_boundary": record["evidence_maturity"],
        "evidence_maturity": record["evidence_maturity"],
        "authority_allowed": ["candidate tests", "shadow execution"],
        "authority_forbidden": ["repair authorization", "production promotion", "software causal authority from source metadata"],
        "positive_test_template": "all primitive preconditions produce their distinct typed effects",
        "negative_test_template": "each missing primitive precondition blocks without the corresponding effect",
        "adversarial_test_template": "source maturity and execution depth cannot be escalated by compilation",
        "shadow_executable_identity": "controllergate.isomorphism.primitives:apply_primitive",
        "translation_state": state,
        "rejection_or_blocker_reason": "structured event is a black-box or exposes no participants" if missing_detail else None,
        "reopen_condition": "additional release-bound source detail and independent execution" if missing_detail else None,
        "compiler_basis": "structured_topology",
        "keyword_baseline_used_for_authority": False,
        "producer": "controllergate.isomorphism.compiler:structured_v2",
        "execution_depth": "structured_contract_compilation",
        "semantic_scope": "candidate translation only",
    }
