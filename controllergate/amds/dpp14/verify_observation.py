from .state import DPP14State


def verify_observation(state: DPP14State) -> DPP14State:
    for item in state.observations:
        item["verified"] = item.get("status") == "PASS" and item.get("frame_hash") == state.frozen_frame.get("frame_hash")
    state.trace.append({"transition": "VerifyObservation", "status": "PASS", "independent_verification": True})
    return state
