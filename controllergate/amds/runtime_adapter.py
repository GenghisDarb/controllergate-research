from __future__ import annotations

from typing import Any, Callable
from .board import update_board, validate_board
from .branch_closure import close_branch
from .probe_executors import execute_probe
from .stop_policy import evaluate_stop


def run_amds_active_loop(board: dict[str,Any], probes: list[dict[str,Any]], executor_factory: Callable[[dict[str,Any]],Callable[[],dict[str,Any]]], *, budget: int = 16, interlock_pass: bool = True) -> dict[str,Any]:
    if validate_board(board)["status"] != "PASS": return {"status":"BLOCK","stop_reason":"board hash invalid","probes_executed":0,"board_updates":0,"branches_closed":0,"board":board,"observations":[]}
    observations=[]; updates=[]; closures=[]
    for probe in probes[:budget]:
        stop=evaluate_stop(unresolved_branches=max(1,len(probes)-len(observations)),legal_probes=len(probes)-len(observations),budget_remaining=budget-len(observations),interlock_pass=interlock_pass)
        if stop["stop"]: break
        auth={"authorization_id":f"auth-{probe['probe_id']}","allowed":True,"mutation_allowed":False}
        observation=execute_probe(probe["probe_type"],executor_factory(probe),auth); observations.append(observation)
        state="RESOLVED" if observation.get("status")=="PASS" else "BLOCKED"
        board,update=update_board(board,{probe["cell_id"]:state},f"observation-{len(observations):03d}"); updates.append(update.__dict__)
        closures.append(close_branch(probe["cell_id"],[observation],resolved=state=="RESOLVED",reopen_conditions=[] if state=="RESOLVED" else [observation.get("blocker","new evidence")]))
        if observation.get("status") in {"BLOCK","MANUAL_REVIEW"}: break
    unresolved=sum(c["state"] not in {"RESOLVED","SAFE","NOT_APPLICABLE"} for c in board["cells"])
    if observations and observations[-1].get("status")=="BLOCK":
        stop={"stop":True,"reason":"interlock blocked","legal_probe_count":max(0,len(probes)-len(observations))}
    else:
        stop=evaluate_stop(unresolved_branches=unresolved,legal_probes=max(0,len(probes)-len(observations)),budget_remaining=budget-len(observations),interlock_pass=interlock_pass,manual_review=bool(observations and observations[-1].get("status")=="MANUAL_REVIEW"))
    return {"status":"PASS","stop_reason":stop["reason"],"probes_executed":len(observations),"board_updates":len(updates),"branches_closed":sum(c["status"]=="RESOLVED" for c in closures),"board":board,"observations":observations,"updates":updates,"closures":closures,"stop_decision":stop}


def execute_amds_probe(*args, **kwargs):
    return execute_probe(*args, **kwargs)


def authorize_amds_probe(candidate_id: str, probe_id: str, *, interlock_pass: bool = True) -> dict:
    return {"authorization_id":f"amds-auth:{candidate_id}:{probe_id}","candidate_id":candidate_id,"probe_id":probe_id,"allowed":bool(interlock_pass),"single_use":True,"mutation_allowed":False}


def ingest_amds_observation(observation: dict) -> dict:
    return {"status":"PASS" if observation.get("status") in {"PASS","BLOCK","NOT_APPLICABLE","MANUAL_REVIEW"} else "BLOCK","observation":observation}
