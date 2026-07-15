from __future__ import annotations

from typing import Any


GENERIC_PRIMITIVES = (
    "EVENT_CONTRACT", "ENTITY_STATE", "COMPLEX_ASSEMBLY", "CANDIDATE_SET", "DEMONSTRATED_MEMBER",
    "COMPARTMENT", "TRANSLOCATION", "TARGETING", "CATALYST", "COFACTOR", "POSITIVE_REGULATOR",
    "NEGATIVE_REGULATOR", "CHECKPOINT", "FEEDBACK_LOOP", "OSCILLATOR", "PHASE_MACHINE", "RESOURCE_FLUX",
    "FLOW_CONTROL", "REVERSIBLE_REACTION", "IRREVERSIBLE_REACTION", "PROCESSIVE_CYCLE", "QUALITY_CONTROL",
    "STALL_DETECTION", "COLLISION_DETECTION", "RESCUE", "RECYCLING", "DEGRADATION", "SELECTIVE_CLEANUP",
    "BULK_CLEANUP", "FOLDING_OR_CONFORMANCE", "MODIFICATION_CODE", "ACCESSIBILITY_STATE", "LINEAGE", "ORTHOLOGY",
    "NORMAL_VARIANT_PAIR", "NEGATIVE_REACTION", "RESIDUAL_ACTIVITY", "REDUNDANCY_COMPENSATION", "THREAT_HIJACK",
    "RESISTANCE_BYPASS", "LOCAL_CONTAINMENT", "CONTROLLED_TERMINATION", "SENSOR_TRANSDUCER", "EVENT_CHANNEL",
    "ACTUATOR", "DISTRIBUTION_CLEARANCE",
)


def primitive_registry() -> dict[str, Any]:
    return {
        "producer": "controllergate.isomorphism.primitives",
        "execution_depth": "reusable_primitive_contracts",
        "semantic_scope": "generic non-authorizing software mechanism vocabulary",
        "authority_allowed": "shadow simulation and candidate translation",
        "authority_forbidden": ["repair authorization", "production promotion", "source causal proof"],
        "primitives": [
            {
                "primitive_id": primitive,
                "input_contract": "typed_state_and_event",
                "output_contract": "typed_state_transition",
                "negative_control": "invalid_or_missing_precondition_is_rejected",
                "production_authority": False,
            }
            for primitive in GENERIC_PRIMITIVES
        ],
    }


def apply_primitive(primitive_id: str, state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    if primitive_id not in GENERIC_PRIMITIVES:
        return {"status": "BLOCK", "blocker": "unknown_generic_primitive", "state": state}
    if not event.get("source_occurrence_identity"):
        return {"status": "BLOCK", "blocker": "missing_source_occurrence_identity", "state": state}
    updated = dict(state)
    trace = list(updated.get("primitive_trace", []))
    trace.append(primitive_id)
    updated["primitive_trace"] = trace
    updated["last_source_occurrence_identity"] = event["source_occurrence_identity"]
    updated["authority"] = "shadow_non_authorizing"
    return {"status": "PASS", "blocker": None, "state": updated}
