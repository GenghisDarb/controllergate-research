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


_CONTRACT_ROWS = (
    ("EVENT_CONTRACT", "event_type", "accepted_event"),
    ("ENTITY_STATE", "entity_state", "entity_state"),
    ("COMPLEX_ASSEMBLY", "members", "assembled_complex"),
    ("CANDIDATE_SET", "candidates", "candidate_frontier"),
    ("DEMONSTRATED_MEMBER", "demonstrated_member", "demonstrated_member"),
    ("COMPARTMENT", "compartment", "active_compartment"),
    ("TRANSLOCATION", "destination", "translocation_destination"),
    ("TARGETING", "target", "selected_target"),
    ("CATALYST", "catalyst", "active_catalyst"),
    ("COFACTOR", "cofactor", "bound_cofactor"),
    ("POSITIVE_REGULATOR", "positive_signal", "positive_regulation"),
    ("NEGATIVE_REGULATOR", "negative_signal", "negative_regulation"),
    ("CHECKPOINT", "checkpoint", "checkpoint_state"),
    ("FEEDBACK_LOOP", "feedback", "feedback_state"),
    ("OSCILLATOR", "phase", "oscillator_phase"),
    ("PHASE_MACHINE", "phase_transition", "phase_machine_state"),
    ("RESOURCE_FLUX", "resource_delta", "resource_balance"),
    ("FLOW_CONTROL", "flow_limit", "flow_limit"),
    ("REVERSIBLE_REACTION", "reverse_transition", "reversible_transition"),
    ("IRREVERSIBLE_REACTION", "commit_transition", "irreversible_commit"),
    ("PROCESSIVE_CYCLE", "cycle_step", "processive_cycle"),
    ("QUALITY_CONTROL", "quality_measurement", "quality_state"),
    ("STALL_DETECTION", "progress_clock", "stall_state"),
    ("COLLISION_DETECTION", "collision_key", "collision_state"),
    ("RESCUE", "rescue_route", "rescue_state"),
    ("RECYCLING", "recyclable_resource", "recycled_resource"),
    ("DEGRADATION", "degradation_target", "degraded_target"),
    ("SELECTIVE_CLEANUP", "selected_cleanup_target", "selective_cleanup"),
    ("BULK_CLEANUP", "cleanup_scope", "bulk_cleanup"),
    ("FOLDING_OR_CONFORMANCE", "conformance_contract", "conformance_state"),
    ("MODIFICATION_CODE", "modification", "modification_state"),
    ("ACCESSIBILITY_STATE", "access_policy", "accessibility_state"),
    ("LINEAGE", "parent_identity", "lineage_parent"),
    ("ORTHOLOGY", "inference_source", "inference_lineage"),
    ("NORMAL_VARIANT_PAIR", "normal_variant_pair", "variant_comparison"),
    ("NEGATIVE_REACTION", "negative_outcome", "negative_reaction"),
    ("RESIDUAL_ACTIVITY", "residual_fraction", "residual_activity"),
    ("REDUNDANCY_COMPENSATION", "alternate_route", "redundancy_state"),
    ("THREAT_HIJACK", "untrusted_controller", "hijack_state"),
    ("RESISTANCE_BYPASS", "bypass_route", "bypass_state"),
    ("LOCAL_CONTAINMENT", "containment_scope", "containment_state"),
    ("CONTROLLED_TERMINATION", "termination_token", "termination_state"),
    ("SENSOR_TRANSDUCER", "sensor_reading", "sensor_signal"),
    ("EVENT_CHANNEL", "channel_message", "channel_state"),
    ("ACTUATOR", "actuation_request", "actuator_state"),
    ("DISTRIBUTION_CLEARANCE", "clearance_target", "clearance_state"),
)


PRIMITIVE_CONTRACTS = {
    primitive: {
        "primitive_id": primitive,
        "required_event_field": required,
        "effect_key": effect,
        "input_contract": f"source_occurrence_identity + {required}",
        "output_contract": f"state.{effect}",
        "negative_control": f"missing_{required}_blocks_without_{effect}",
        "authority": "shadow_non_authorizing",
    }
    for primitive, required, effect in _CONTRACT_ROWS
}


def primitive_registry() -> dict[str, Any]:
    return {
        "producer": "controllergate.isomorphism.primitives",
        "execution_depth": "distinct_executable_primitive_contracts",
        "semantic_scope": "generic non-authorizing state transition mechanisms",
        "authority_allowed": "shadow simulation and candidate translation",
        "authority_forbidden": ["repair authorization", "production promotion", "source causal proof"],
        "primitives": [PRIMITIVE_CONTRACTS[primitive] for primitive in GENERIC_PRIMITIVES],
    }


def conformance_event() -> dict[str, Any]:
    event: dict[str, Any] = {"source_occurrence_identity": "structured-source-conformance"}
    for index, primitive in enumerate(GENERIC_PRIMITIVES, 1):
        event[PRIMITIVE_CONTRACTS[primitive]["required_event_field"]] = {"sequence": index, "primitive": primitive}
    return event


def apply_primitive(primitive_id: str, state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    contract = PRIMITIVE_CONTRACTS.get(primitive_id)
    if contract is None:
        return {"status": "BLOCK", "blocker": "unknown_generic_primitive", "state": dict(state)}
    if not event.get("source_occurrence_identity"):
        return {"status": "BLOCK", "blocker": "missing_source_occurrence_identity", "state": dict(state)}
    required = contract["required_event_field"]
    if required not in event or event[required] in (None, "", [], {}):
        return {"status": "BLOCK", "blocker": f"missing_{required}", "state": dict(state)}
    observed = event[required]
    # The conformance path supplies structured mappings. Explicit control
    # values exercise the stronger primitive-specific laws below.
    if primitive_id == "CHECKPOINT" and observed is False:
        return {"status": "BLOCK", "blocker": "checkpoint_prerequisite_unmet", "state": dict(state)}
    if primitive_id == "TRANSLOCATION" and isinstance(observed, dict):
        source = observed.get("source")
        current = state.get("active_compartment")
        if source and current and current.get("observed") != source:
            return {"status": "BLOCK", "blocker": "wrong_source_compartment", "state": dict(state)}
    if primitive_id == "IRREVERSIBLE_REACTION" and isinstance(observed, dict) and observed.get("reverse") is True:
        return {"status": "BLOCK", "blocker": "irreversible_transition_cannot_reverse", "state": dict(state)}
    if primitive_id == "RESOURCE_FLUX" and isinstance(observed, (int, float)):
        if float(state.get("resource_balance", {}).get("balance", 0.0)) + float(observed) < 0:
            return {"status": "BLOCK", "blocker": "resource_budget_underflow", "state": dict(state)}
    if primitive_id == "OSCILLATOR" and isinstance(observed, dict) and observed.get("drift") and not observed.get("authorized_reset"):
        return {"status": "BLOCK", "blocker": "phase_drift_requires_authorized_reset", "state": dict(state)}
    if primitive_id == "THREAT_HIJACK" and isinstance(observed, dict) and observed.get("verifier_disabled"):
        return {"status": "BLOCK", "blocker": "untrusted_controller_disabled_verifier", "state": dict(state)}
    if primitive_id == "LOCAL_CONTAINMENT" and isinstance(observed, dict) and observed.get("scope") == "global" and not observed.get("global_authority"):
        return {"status": "BLOCK", "blocker": "local_containment_cannot_escalate_global", "state": dict(state)}
    if primitive_id == "ACTUATOR" and contract["effect_key"] in state:
        return {"status": "BLOCK", "blocker": "actuator_single_use_violation", "state": dict(state)}
    updated = dict(state)
    trace = list(updated.get("primitive_trace", []))
    trace.append(primitive_id)
    updated["primitive_trace"] = trace
    effect = {
        "observed": observed,
        "source_occurrence_identity": event["source_occurrence_identity"],
        "transition_sequence": len(trace),
    }
    if primitive_id == "RESOURCE_FLUX" and isinstance(observed, (int, float)):
        effect["balance"] = float(state.get("resource_balance", {}).get("balance", 0.0)) + float(observed)
    elif primitive_id == "REVERSIBLE_REACTION" and isinstance(observed, dict):
        effect["direction"] = "reverse" if observed.get("reverse") else "forward"
    elif primitive_id == "OSCILLATOR" and isinstance(observed, dict):
        effect["resynchronized"] = bool(observed.get("drift") and observed.get("authorized_reset"))
    elif primitive_id == "STALL_DETECTION":
        effect["condition"] = "stalled"
    elif primitive_id == "COLLISION_DETECTION":
        effect["condition"] = "collision"
    elif primitive_id == "RESCUE":
        effect["incomplete_product_promoted"] = False
        effect["stalled_worker_cleared"] = True
    elif primitive_id == "RECYCLING":
        effect["resource_restored"] = True
    elif primitive_id == "QUALITY_CONTROL" and isinstance(observed, dict):
        effect["tag_semantics"] = observed.get("tag_semantics", "coordination")
    elif primitive_id == "NORMAL_VARIANT_PAIR" and isinstance(observed, dict):
        effect["first_divergent_transition"] = observed.get("first_divergent_transition")
    elif primitive_id == "RESIDUAL_ACTIVITY" and isinstance(observed, (int, float)):
        fraction = max(0.0, min(1.0, float(observed)))
        effect.update({"fraction": fraction, "health_grade": "healthy" if fraction >= 0.8 else "degraded" if fraction > 0 else "failed"})
    elif primitive_id == "REDUNDANCY_COMPENSATION":
        effect.update({"failure_masked": True, "latent_debt_preserved": True})
    elif primitive_id == "RESISTANCE_BYPASS":
        effect["unresolved_defect_debt_preserved"] = True
    elif primitive_id == "CONTROLLED_TERMINATION":
        effect.update({"proof_lineage_preserved": True, "cleanup_lineage_preserved": True})
    elif primitive_id == "DISTRIBUTION_CLEARANCE":
        effect["residue_removed"] = True
    updated[contract["effect_key"]] = effect
    updated["authority"] = "shadow_non_authorizing"
    return {
        "status": "PASS",
        "blocker": None,
        "state": updated,
        "contract": contract,
        "mechanism_outcome": {"effect_key": contract["effect_key"], "transition_sequence": len(trace)},
    }
