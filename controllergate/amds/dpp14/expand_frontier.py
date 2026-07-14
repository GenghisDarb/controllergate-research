from .state import DPP14State


def expand_frontier(state: DPP14State) -> DPP14State:
    state.trace.append({"transition": "ExpandFrontier", "status": "PASS", "hypotheses": list(state.hypotheses)})
    return state
