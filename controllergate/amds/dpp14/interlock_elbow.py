from .state import DPP14State


def interlock_and_elbow_audit(state: DPP14State) -> DPP14State:
    interlocks = state.frozen_frame.get("interlocks", {})
    state.frozen_frame["repair_interlocks_pass"] = bool(interlocks) and all(value == "PASS" for value in interlocks.values())
    state.trace.append({"transition": "InterlockAndElbowAudit", "status": "PASS", "interlocks_can_authorize": False})
    return state
