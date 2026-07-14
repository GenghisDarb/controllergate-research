from .state import DPP14State


ALLOWED_CERTAINTY = {"cryptographic_identity", "direct_command_output", "verified_source_frame", "verified_provider_result", "verified_pathway_divergence", "verified_target_origin", "verified_environment_observation"}


def mark_certain(state: DPP14State) -> DPP14State:
    facts = state.frozen_frame.get("facts", [])
    state.certain_facts = [fact for fact in facts if fact.get("evidence_kind") in ALLOWED_CERTAINTY and fact.get("verified") is True]
    state.trace.append({"transition": "MarkCertain", "status": "PASS", "certain_fact_count": len(state.certain_facts)})
    return state
