from .state import DPP14State


def seed(candidate_id: str, evidence: dict) -> DPP14State:
    if not candidate_id or not isinstance(evidence, dict):
        raise ValueError("candidate identity and evidence required")
    state = DPP14State(candidate_id, dict(evidence))
    state.trace.append({"transition": "Seed", "status": "PASS"})
    return state
