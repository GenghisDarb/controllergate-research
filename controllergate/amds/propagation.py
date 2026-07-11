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
            if kind=="exactly_one" and len(active)==1:
                for m in members:
                    if states.get(m)==CellState.UNKNOWN.value: states[m]=CellState.SAFE.value; deductions.append({"round":round_id,"constraint_id":constraint["constraint_id"],"cell_id":m,"state":CellState.SAFE.value}); changed=True
            if kind=="exactly_one" and not active:
                unknown=[m for m in members if states.get(m)==CellState.UNKNOWN.value]
                if len(unknown)==1: states[unknown[0]]=CellState.CAUSAL_MINE.value; deductions.append({"round":round_id,"constraint_id":constraint["constraint_id"],"cell_id":unknown[0],"state":CellState.CAUSAL_MINE.value}); changed=True
        if not changed: break
    cells=[{**c,"state":states[c["cell_id"]]} for c in board["cells"]]
    return {"status":"BLOCK" if contradictions else "PASS","cells":cells,"deductions":deductions,"contradictions":contradictions,"fixed_point":True,"rounds":round_id+1,"backtracking_components":0}
