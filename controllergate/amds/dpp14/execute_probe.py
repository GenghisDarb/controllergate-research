from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from .state import DPP14State


def _read_only_lane(probe: dict, frozen: dict) -> dict:
    if probe.get("mutates") or probe.get("patch_authority"):
        return {"probe_id": probe.get("probe_id"), "status": "BLOCK", "blocker": "parallel_probe_not_read_only"}
    return {"probe_id": probe.get("probe_id"), "lane": probe.get("lane", "default"), "status": probe.get("status", "PASS"),
            "classification": probe.get("classification"), "direct": bool(probe.get("direct")), "frame_hash": frozen.get("frame_hash")}


def execute_probe(state: DPP14State) -> DPP14State:
    frozen = deepcopy(state.frozen_frame)
    probes = frozen.get("selected_probes", [])
    with ThreadPoolExecutor(max_workers=max(1, min(4, len(probes)))) as pool:
        results = list(pool.map(lambda probe: _read_only_lane(probe, frozen), probes))
    state.observations = sorted(results, key=lambda item: (item.get("lane", ""), item.get("probe_id", "")))
    state.trace.append({"transition": "ExecuteProbe", "status": "PASS", "round_start_barrier": True, "read_only_lanes": True})
    return state
