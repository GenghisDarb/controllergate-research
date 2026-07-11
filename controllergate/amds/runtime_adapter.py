from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Callable

from controllergate.core.evidence import hash_record
from .board import update_board, validate_board
from .goal_predicates import build_branch_goal
from .observation_classifier import classify_build_observation
from .probe_executors import PROBE_VERIFIERS, execute_probe
from .propagation import propagate_constraints
from .authorization import consume_probe_authorization, issue_probe_authorization
from .probe_planner import expected_information_gain
from .semantic_verification import verify_semantic_claim
from .stop_policy import evaluate_stop


def _reseal(board: dict[str,Any], cells: list[dict[str,Any]]|None=None, branches: dict[str,Any]|None=None) -> dict[str,Any]:
    value={**board}
    if cells is not None:
        sealed=[]
        for cell in cells:
            raw={key:item for key,item in cell.items() if key!="state_hash"};raw["state_hash"]=hash_record(raw);sealed.append(raw)
        value["cells"]=sealed
    if branches is not None:value["branches"]=branches
    value.pop("board_hash",None);value["board_hash"]=hash_record(value);return value


def _default_registry(probes: list[dict[str,Any]], executed: set[str]) -> list[dict[str,Any]]:
    return [dict(probe) for probe in probes if probe.get("probe_id") not in executed]


def _branch_key(board: dict[str,Any], probe: dict[str,Any]) -> str|None:
    requested=probe.get("branch_key") or probe.get("branch_id")
    if requested in board.get("branches",{}):return str(requested)
    cell_id=probe.get("cell_id") or probe.get("metadata",{}).get("cell_id")
    for key,value in board.get("branches",{}).items():
        if value.get("branch_id")==cell_id:return key
    return None


def observation_driven_posterior(probe: dict[str,Any], observation: dict[str,Any]) -> dict[str,Any]:
    targeted=list(probe.get("targeted_hypotheses",[]));prior_values=dict(probe.get("prior_probabilities",{}))
    prior={name:float(prior_values.get(name,1.0/len(targeted) if targeted else 0.0)) for name in targeted}
    likelihoods=dict(observation.get("hypothesis_likelihoods",{}));supported=set(observation.get("supported_hypotheses",[]));refuted=set(observation.get("refuted_hypotheses",[]))
    if not likelihoods and (supported or refuted): likelihoods={name:(1.0 if name in supported else 0.0 if name in refuted else None) for name in targeted}
    weights={name:prior[name]*float(likelihoods[name]) for name in targeted if likelihoods.get(name) is not None}
    denominator=sum(weights.values());posterior={name:(weights.get(name,0.0)/denominator if denominator else prior[name]) for name in targeted}
    entropy=lambda values:-sum(value*math.log(value) for value in values if value>0)
    return {"prior":prior,"likelihoods":{name:likelihoods.get(name,"NOT_ESTABLISHED") for name in targeted},"posterior":posterior,"supported_hypotheses":sorted(supported),"refuted_hypotheses":sorted(refuted),"unchanged_hypotheses":sorted(set(targeted)-supported-refuted),"entropy_before":entropy(prior.values()),"entropy_after":entropy(posterior.values()),"likelihood_basis":"observation" if likelihoods else "NOT_ESTABLISHED"}


def run_amds_active_loop(
    board: dict[str,Any], probes: list[dict[str,Any]]|None,
    executor_factory: Callable[[dict[str,Any]],Callable[[],dict[str,Any]]], *,
    budget: int=16, interlock_pass: bool=True,
    registry_factory: Callable[[dict[str,Any],list[dict[str,Any]]],list[dict[str,Any]]]|None=None,
    observation_classifier: Callable[[dict[str,Any]],dict[str,Any]]|None=None,
    goal_evaluator: Callable[[dict[str,Any],dict[str,Any],dict[str,Any]],dict[str,Any]]|None=None,
    information_gain_floor: float|None=None,
    authorization_store: Path|None=None,
    candidate_sha: str|None=None,
    semantic_verifier_factory: Callable[[dict[str,Any],dict[str,Any]],Callable[[],dict[str,Any]]|None]|None=None,
) -> dict[str,Any]:
    validation=validate_board(board)
    if validation["status"]!="PASS":return {"status":"BLOCK","stop_reason":"board hash invalid","probes_executed":0,"board_updates":0,"branches_closed":0,"board":board,"observations":[],"registry_versions":[],"posterior_updates":[],"rerank_events":[]}
    probes=list(probes or []);observations=[];updates=[];branch_trace=[];registry_versions=[];posterior_updates=[];rerank_events=[];executed:set[str]=set();contradictions=[];backtracking_trace=[]
    initial_closed=sum(value.get("branch_state")=="CLOSED" for value in board.get("branches",{}).values())
    while len(observations)<budget:
        propagation=propagate_constraints(board)
        contradictions=propagation.get("contradictions",[])
        backtracking_trace.extend(propagation.get("backtracking", []))
        board=_reseal(board,cells=propagation.get("cells",board.get("cells",[])))
        factory=registry_factory or (lambda current,history:_default_registry(probes,executed))
        registry=factory(board,list(observations));generation=len(registry_versions)+1
        ranked=[]
        prior=dict(board.get("hypothesis_state",{}).get("probabilities",{}))
        for item in registry:
            value=dict(item); outcomes=value.get("likelihood_outcomes",{})
            information_gain=expected_information_gain(prior,outcomes) if prior and outcomes else None
            value["expected_information_gain_nats"]=information_gain if information_gain is not None else "NOT_ESTABLISHED"
            deterministic=bool(value.get("deterministic_necessity"))
            value["utility"]=(information_gain-float(value.get("execution_cost",1.0))*0.05-float(value.get("security_risk",0.0))) if information_gain is not None else (0.0 if deterministic else None)
            value["selection_rule"]="expected_information_gain" if information_gain is not None else "deterministic_necessity" if deterministic else "unknown_information_gain_last"
            ranked.append(value)
        ranked=sorted(ranked,key=lambda item:(item.get("utility") is None,-float(item.get("utility") or 0),str(item.get("probe_id"))))
        registry_versions.append({"generation":generation,"board_hash":board["board_hash"],"observation_count":len(observations),"probes":ranked,"registry_hash":hash_record(ranked)})
        rerank_events.append({"generation":generation,"probe_ids":[item.get("probe_id") for item in ranked],"derived_after_observation":bool(observations),"selected":ranked[0].get("probe_id") if ranked else None,"outranking_basis":[{"probe_id":item.get("probe_id"),"utility":item.get("utility"),"selection_rule":item.get("selection_rule")} for item in ranked]})
        unresolved=sum(value.get("branch_state")!="CLOSED" for value in board.get("branches",{}).values()) or sum(cell.get("state") not in {"RESOLVED","SAFE","NOT_APPLICABLE"} for cell in board.get("cells",[]))
        stop=evaluate_stop(unresolved_branches=unresolved,legal_probes=len(ranked),budget_remaining=budget-len(observations),interlock_pass=interlock_pass,contradictions=len(contradictions))
        if stop["stop"]:break
        probe=ranked[0]
        if information_gain_floor is not None and probe.get("expected_information_gain_nats") not in {None,"NOT_ESTABLISHED"} and float(probe["expected_information_gain_nats"])<information_gain_floor:
            stop={"stop":True,"reason":"information-gain floor not met","legal_probe_count":len(ranked)};break
        if authorization_store is not None:
            executor_name=str(probe.get("allowed_executor") or probe.get("probe_type"))
            canonical=issue_probe_authorization(candidate_id=board.get("candidate_id","unknown"),candidate_sha=str(candidate_sha or board.get("candidate_sha") or ""),board_hash=board["board_hash"],probe_id=str(probe["probe_id"]),allowed_executor=executor_name,network_policy=probe.get("network_policy") or {"network_mode":"none"},mutation_policy="none",resource_budget=probe.get("resource_budget") or {"max_seconds":120,"max_memory_mb":1024})
            consumed=consume_probe_authorization(canonical,store_path=authorization_store,candidate_id=board.get("candidate_id","unknown"),candidate_sha=str(candidate_sha or board.get("candidate_sha") or ""),board_hash=board["board_hash"],probe_id=str(probe["probe_id"]),executor=executor_name)
            auth={"authorization_id":canonical["authorization_hash"],"candidate_id":board.get("candidate_id","unknown"),"probe_id":str(probe["probe_id"]),"allowed":consumed["status"]=="PASS","single_use":True,"mutation_allowed":False,"canonical_authorization":canonical,"consumption":consumed}
        else: auth=authorize_amds_probe(board.get("candidate_id","unknown"),str(probe["probe_id"]),interlock_pass=interlock_pass)
        if not auth["allowed"]:stop={"stop":True,"reason":"authorization blocked","legal_probe_count":len(ranked)};break
        observation=execute_probe(str(probe["probe_type"]),executor_factory(probe),auth);executed.add(str(probe["probe_id"]))
        verifier=PROBE_VERIFIERS.get(str(probe["probe_type"]));verification=verifier(observation) if verifier else {"status":"PASS" if observation.get("mutation_count",0)==0 else "BLOCK"}
        if verification.get("status")!="PASS":observation={**observation,"status":"BLOCK","blocker":"independent_observation_verification_failed"}
        recompute=semantic_verifier_factory(probe,observation) if semantic_verifier_factory else None
        semantic_verification=verify_semantic_claim(probe,observation,recompute)
        semantic=(observation_classifier or classify_build_observation)(observation);observation={**observation,"semantic":semantic,"verification":verification,"custody_verification":verification,"semantic_verification":semantic_verification,"registry_generation":generation};observations.append(observation)
        posterior=observation_driven_posterior(probe,observation);posterior_updates.append({"observation":len(observations),"probe_id":probe["probe_id"],"prior_classification":probe.get("prior_classification","structural_uniform_uncalibrated"),**posterior,"posterior_hash":hash_record(posterior)})
        hypothesis=dict(board.get("hypothesis_state",{}));events=list(hypothesis.get("events",[]));event={"observation":len(observations),"probe_id":probe["probe_id"],**posterior,"evidence_hash":hash_record(observation),"update_event":f"posterior-{len(observations):03d}"};event["state_hash"]=hash_record(event);events.append(event);hypothesis.update({"probabilities":posterior["posterior"],"classification":"observation_derived" if posterior["likelihood_basis"]!="NOT_ESTABLISHED" else hypothesis.get("classification","NOT_ESTABLISHED"),"events":events});board={**board,"hypothesis_state":hypothesis};board.pop("board_hash",None);board["board_hash"]=hash_record(board)
        branch_key=_branch_key(board,probe);branches={key:dict(value) for key,value in board.get("branches",{}).items()};goal={"goal_passed":False,"status":"BLOCK"}
        if branch_key is not None:
            branch=branches[branch_key];goal=(goal_evaluator(branch,observation,probe) if goal_evaluator else build_branch_goal(observation.get("goal_evidence",{})))
            next_state="CLOSED" if goal.get("goal_passed") else semantic.get("branch_state","REMEDIATION_PENDING")
            if next_state=="REMEDIATION_VERIFIED" and not goal.get("goal_passed"):next_state="REMEDIATION_PENDING"
            branch.update({"branch_state":next_state,"last_observation_hash":hash_record(observation),"goal_result":goal,"reopen_conditions":[] if next_state=="CLOSED" else branch.get("reopen_conditions") or [observation.get("blocker") or "new evidence"]});branches[branch_key]=branch
            branch_trace.append({"observation":len(observations),"branch_key":branch_key,"state":next_state,"goal_passed":bool(goal.get("goal_passed")),"observation_hash":hash_record(observation)})
        cell_id=probe.get("cell_id") or probe.get("metadata",{}).get("cell_id");state="RESOLVED" if goal.get("goal_passed") else ("NOT_APPLICABLE" if observation.get("observation")=="NOT_APPLICABLE" else "CAUSAL_MINE")
        if cell_id and any(cell.get("cell_id")==cell_id for cell in board.get("cells",[])):
            board,update=update_board(_reseal(board,branches=branches),{str(cell_id):state},f"observation-{len(observations):03d}");updates.append(update.__dict__)
        else:
            before=board["board_hash"];board=_reseal(board,branches=branches);updates.append({"event_id":f"observation-{len(observations):03d}","changed_cells":[],"board_hash_before":before,"board_hash_after":board["board_hash"]})
        if observation.get("status") in {"MANUAL_REVIEW"}:stop={"stop":True,"reason":"manual review required","legal_probe_count":0};break
        if observation.get("blocker") in {"security_violation","authorization_blocked"}:stop={"stop":True,"reason":observation["blocker"].replace("_"," "),"legal_probe_count":0};break
    else:stop={"stop":True,"reason":"probe budget exhausted","legal_probe_count":0}
    if 'stop' not in locals() or not stop.get("stop"):
        unresolved=sum(value.get("branch_state")!="CLOSED" for value in board.get("branches",{}).values()) or sum(cell.get("state") not in {"RESOLVED","SAFE","NOT_APPLICABLE"} for cell in board.get("cells",[]));stop=evaluate_stop(unresolved_branches=unresolved,legal_probes=0,budget_remaining=budget-len(observations),interlock_pass=interlock_pass,contradictions=len(contradictions))
    final_closed=sum(value.get("branch_state")=="CLOSED" for value in board.get("branches",{}).values())
    status="PASS" if observations and not contradictions else "BLOCK"
    return {"status":status,"stop_reason":stop["reason"],"probes_executed":len(observations),"board_updates":len(updates),"branches_closed":max(0,final_closed-initial_closed),"board":board,"observations":observations,"updates":updates,"closures":branch_trace,"registry_versions":registry_versions,"posterior_updates":posterior_updates,"persistent_hypothesis_state":board.get("hypothesis_state",{}),"rerank_events":rerank_events,"contradictions":contradictions,"backtracking_trace":backtracking_trace,"backtracking_components":len(backtracking_trace),"stop_decision":stop,"vacuous_completion_rejected":not observations}


def execute_amds_probe(*args,**kwargs):return execute_probe(*args,**kwargs)


def authorize_amds_probe(candidate_id: str,probe_id: str,*,interlock_pass: bool=True)->dict:
    return {"authorization_id":f"amds-auth:{candidate_id}:{probe_id}","candidate_id":candidate_id,"probe_id":probe_id,"allowed":bool(interlock_pass),"single_use":True,"mutation_allowed":False}


def ingest_amds_observation(observation: dict)->dict:
    return {"status":"PASS" if observation.get("status") in {"PASS","BLOCK","NOT_APPLICABLE","MANUAL_REVIEW"} and observation.get("evidence_hash") else "BLOCK","observation":observation}
