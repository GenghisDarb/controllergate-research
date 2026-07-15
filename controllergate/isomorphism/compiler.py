from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from .primitives import GENERIC_PRIMITIVES


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
