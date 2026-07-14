from .state import DPP14State


def select_minimal_probe(state: DPP14State) -> DPP14State:
    probes = state.frozen_frame.get("probes", [])
    state.frozen_frame["selected_probes"] = sorted(probes, key=lambda item: (item.get("cost", 1), item.get("probe_id", "")))
    state.trace.append({"transition": "SelectMinimalProbe", "status": "PASS", "probe_count": len(probes)})
    return state
