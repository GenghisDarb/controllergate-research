from .state import DPP14State


def materialize_requirements(state: DPP14State) -> DPP14State:
    required = ("source", "provider", "runtime", "command", "target")
    state.frozen_frame["requirements_materialized"] = {key: bool(state.frozen_frame.get(key)) for key in required}
    state.trace.append({"transition": "MaterializeRequirements", "status": "PASS"})
    return state
