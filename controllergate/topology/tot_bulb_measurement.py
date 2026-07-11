from __future__ import annotations

from typing import Any, Callable

from .tot_bulb_information_gain import score_probe
from .tot_bulb_stop_policy import stop_reason
from .tot_bulb_update import update_volume


def run_measurement_loop(volume: dict[str, Any], probes: list[dict[str, Any]], executor: Callable[[dict[str, Any]], dict[str, Any]], *, information_gain_floor: float = 0.25, budget_limit: int = 4) -> dict[str, Any]:
    candidates = [{**probe, "score": score_probe(probe)} for probe in probes]
    candidates.sort(key=lambda item: (-item["score"], str(item["probe_id"])))
    trace = []; updates = []; used = 0; current = volume; blocked = False
    for probe in candidates:
        reason = stop_reason(isolated=False, legal_remaining=len(candidates) - used, information_gain=float(probe["expected_information_gain"]), floor=information_gain_floor, budget_used=used, budget_limit=budget_limit, interlock_blocked=blocked)
        if reason: break
        if probe.get("interlock_status") != "PASS": blocked = True; trace.append({"probe_id": probe["probe_id"], "status": "BLOCK", "score": probe["score"], "reason": "interlock_blocked"}); break
        result = executor(probe); used += 1; trace.append({"probe_id": probe["probe_id"], "status": "COMPLETED", "score": probe["score"], "result": result})
        current = update_volume(current, probe, result); updates.append({"probe_id": probe["probe_id"], "volume_hash": current["volume_hash"]})
        if result.get("causal_family_isolated") is True: break
    final_reason = stop_reason(isolated=bool(trace and trace[-1].get("result", {}).get("causal_family_isolated")), legal_remaining=max(0, len(candidates) - used), information_gain=float(candidates[min(used, len(candidates)-1)]["expected_information_gain"]) if candidates else 0.0, floor=information_gain_floor, budget_used=used, budget_limit=budget_limit, interlock_blocked=blocked) or "bounded_measurement_complete"
    return {"probe_candidates": candidates, "selection_trace": trace, "volume_updates": updates, "final_volume": current, "probes_executed": used, "stop_reason": final_reason}
