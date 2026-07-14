from .state import DPP14State


def update_constraints(state: DPP14State) -> DPP14State:
    directly_supported = {item.get("classification") for item in state.observations if item.get("verified") and item.get("direct")}
    if directly_supported:
        state.hypotheses = [item for item in state.hypotheses if item in directly_supported or item == "insufficient_evidence"]
    state.trace.append({"transition": "UpdateConstraints", "status": "PASS", "deterministic_merge": True})
    return state
