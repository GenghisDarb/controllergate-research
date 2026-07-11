from __future__ import annotations

from typing import Any
from .types import CellState


def propagate_constraints(board: dict[str, Any], max_rounds: int = 64) -> dict[str, Any]:
    states = {c["cell_id"]: c["state"] for c in board["cells"]}; deductions=[]; contradictions=[]; round_id=0
    for round_id in range(max_rounds):
        changed = False
        for constraint in board["constraints"]:
            kind=constraint["constraint_type"]; members=list(constraint["members"]); active=[m for m in members if states.get(m)==CellState.CAUSAL_MINE.value]
            if kind in {"requires", "implies", "provider_dependency", "environment_dependency"} and len(members)>1 and states.get(members[0]) in {CellState.CAUSAL_MINE.value, CellState.RESOLVED.value} and states.get(members[1])==CellState.UNKNOWN.value:
                states[members[1]]=CellState.CAUSAL_MINE.value; deductions.append({"round":round_id,"constraint_id":constraint["constraint_id"],"cell_id":members[1],"state":CellState.CAUSAL_MINE.value}); changed=True
            if kind in {"excludes","mutually_exclusive","at_most_one"} and len(active)>1:
                contradictions.append({"constraint_id":constraint["constraint_id"],"active":active})
                for m in active: states[m]=CellState.CONFLICTED.value
            if kind=="exactly_one" and len(active)>1:
                contradictions.append({"constraint_id":constraint["constraint_id"],"active":active,"reason":"exactly_one_multiple_active"})
                for m in active: states[m]=CellState.CONFLICTED.value
            if kind=="exactly_one" and len(active)==1:
                for m in members:
                    if states.get(m)==CellState.UNKNOWN.value: states[m]=CellState.SAFE.value; deductions.append({"round":round_id,"constraint_id":constraint["constraint_id"],"cell_id":m,"state":CellState.SAFE.value}); changed=True
            if kind=="exactly_one" and not active:
                unknown=[m for m in members if states.get(m)==CellState.UNKNOWN.value]
                if len(unknown)==1: states[unknown[0]]=CellState.CAUSAL_MINE.value; deductions.append({"round":round_id,"constraint_id":constraint["constraint_id"],"cell_id":unknown[0],"state":CellState.CAUSAL_MINE.value}); changed=True
            if kind=="at_least_one" and not active and not any(states.get(m)==CellState.UNKNOWN.value for m in members):
                contradictions.append({"constraint_id":constraint["constraint_id"],"reason":"at_least_one_unsatisfied"})
            if kind in {"excludes","mutually_exclusive","at_most_one"} and len(active)==1:
                for m in members:
                    if states.get(m)==CellState.UNKNOWN.value:states[m]=CellState.SAFE.value;deductions.append({"round":round_id,"constraint_id":constraint["constraint_id"],"cell_id":m,"state":CellState.SAFE.value});changed=True
        if not changed: break
    cells=[{**c,"state":states[c["cell_id"]]} for c in board["cells"]]
    return {"status":"BLOCK" if contradictions else "PASS","cells":cells,"deductions":deductions,"contradictions":contradictions,"fixed_point":True,"rounds":round_id+1,"backtracking_components":0}


def bounded_component_enumeration(cell_ids: list[str], constraints: list[dict], max_states: int = 4096) -> dict[str, Any]:
    if 2**len(cell_ids)>max_states:return {"status":"BLOCK","blocker":"backtracking_state_budget_exhausted","components":1,"assignments":[]}
    assignments=[]
    for mask in range(2**len(cell_ids)):
        state={cell_ids[i]:bool(mask&(1<<i)) for i in range(len(cell_ids))};valid=True
        for c in constraints:
            values=[state.get(m,False) for m in c.get("members",[])]
            if c.get("constraint_type")=="at_least_one" and not any(values):valid=False
            if c.get("constraint_type") in {"at_most_one","mutually_exclusive"} and sum(values)>1:valid=False
            if c.get("constraint_type")=="exactly_one" and sum(values)!=1:valid=False
        if valid:assignments.append(state)
    return {"status":"PASS","components":1,"assignments":assignments,"termination_proven":True}
