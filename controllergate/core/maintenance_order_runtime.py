from __future__ import annotations

from dataclasses import asdict
from typing import Any

from controllergate.core.evidence import hash_record
from .maintenance_transition_guard import REQUIRED_PREDECESSORS, guard_transition

MAINTENANCE_ORDER = tuple(REQUIRED_PREDECESSORS)


def execute_maintenance_order(candidate_state: dict[str, Any], phase_authorizations: dict[str, dict[str, Any]], phase_interlocks: dict[str, dict[str, str]], *, stop_before: str = "bounded_action") -> list[dict[str, Any]]:
    completed: set[str] = set(); prior = hash_record({"candidate": candidate_state.get("candidate_id"), "state": "maintenance_genesis"}); trace = []
    for phase in MAINTENANCE_ORDER:
        if phase == stop_before:
            decision = guard_transition(phase, completed, prior, {"status": "BLOCK", "allowed_phase": None}, candidate_state, phase_interlocks.get(phase, {}))
        else:
            decision = guard_transition(phase, completed, prior, phase_authorizations.get(phase, {}), candidate_state, phase_interlocks.get(phase, {}))
        record = asdict(decision); record["required_predecessors"] = list(REQUIRED_PREDECESSORS[phase]); record["applicable_interlocks"] = phase_interlocks.get(phase, {}); trace.append(record); prior = decision.post_state_hash
        if decision.status == "PASS": completed.add(phase)
        else:
            for downstream in MAINTENANCE_ORDER[len(trace):]:
                blocked = guard_transition(downstream, completed, prior, {"status": "BLOCK", "allowed_phase": None}, candidate_state, phase_interlocks.get(downstream, {})); trace.append(asdict(blocked)); prior = blocked.post_state_hash
            break
    return trace
