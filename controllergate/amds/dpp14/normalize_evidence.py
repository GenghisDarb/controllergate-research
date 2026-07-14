from .state import DPP14State


def normalize_evidence(state: DPP14State) -> DPP14State:
    state.frozen_frame = {key: state.frozen_frame[key] for key in sorted(state.frozen_frame)}
    state.trace.append({"transition": "NormalizeEvidence", "status": "PASS"})
    return state
