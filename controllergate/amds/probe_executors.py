from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import subprocess
from typing import Any, Callable

from controllergate.core.evidence import hash_record, sha256_file
from controllergate.core.command_orthology import command_token_safety
from controllergate.core.harness_origin import validate_harness_origin_record
from controllergate.core.clean_repair import comparable_matched_null_arms
from controllergate.core.curvature_selection import curvature_feature_vector
from controllergate.core.candidate_seed_classes import classify_seed_for_repair
from controllergate.runtime.historical_lock_verifier import verify_historical_lock
from controllergate.runtime.incident_capture import capture_incident
from controllergate.runtime.active_ast_excision_probe import plan_excision_probe
from .probe_registry import PROBE_TYPES


def execute_probe(probe_type: str, executor: Callable[[],dict[str,Any]], authorization: dict[str,Any]) -> dict[str,Any]:
    if probe_type not in PROBE_TYPES and not probe_type.startswith(("build_","provider_","compiler_","cargo_","cmake_","pkg_config_","abi_","resource_","writable_")):
        return {"status":"BLOCK","operation_status":"BLOCK","blocker":"amds_probe_type_unregistered"}
    if not authorization.get("allowed") or authorization.get("mutation_allowed") or not authorization.get("single_use",True):
        return {"status":"BLOCK","operation_status":"BLOCK","blocker":"amds_probe_authorization_invalid"}
    result=executor()
    return {**result,"probe_type":probe_type,"authorization_id":authorization.get("authorization_id"),"mutation_count":0}


def _result(observation: str, evidence: dict[str,Any], *, status: str="PASS", blocker: str|None=None) -> dict[str,Any]:
    return {"status":status,"operation_status":"PASS","observation":observation,"evidence":evidence,"evidence_hash":hash_record(evidence),"raw_evidence_captured":True,"blocker":blocker,"mutation_count":0}


def _not_applicable(payload: dict[str,Any]) -> dict[str,Any]|None:
    return _result("NOT_APPLICABLE",{"applicability_reason":payload.get("applicability_reason","probe explicitly not applicable")}) if payload.get("applicable") is False else None


def dependency_lock_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    lock=payload.get("lock")
    if lock is None and payload.get("lock_path"):
        lock=json.loads(Path(payload["lock_path"]).read_text(encoding="utf-8"))
    if not isinstance(lock,dict):return _result("INCONCLUSIVE",{"reason":"lock evidence missing"},status="BLOCK",blocker="dependency_lock_evidence_missing")
    if isinstance(lock.get("selected_artifacts"),dict):lock={**lock,"selected_artifacts":list(lock["selected_artifacts"].values())}
    verified=verify_historical_lock(lock,payload["cutoff"]);return _result("DEPENDENCY_LOCK_OBSERVED",verified,status="PASS" if verified["status"]=="PASS" else "BLOCK",blocker=None if verified["status"]=="PASS" else "dependency_lock_incomplete")


def issue_timestamp_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    try:issue=datetime.fromisoformat(str(payload["issue_created_at"]).replace("Z","+00:00"));cutoff=datetime.fromisoformat(str(payload["cutoff"]).replace("Z","+00:00"));safe=issue<=cutoff
    except Exception:return _result("INCONCLUSIVE",{"reason":"timestamp parse failed"},status="BLOCK",blocker="issue_timestamp_invalid")
    return _result("ISSUE_TIMESTAMP_OBSERVED",{"issue_created_at":issue.isoformat(),"cutoff":cutoff.isoformat(),"decision_time_safe":safe},status="PASS" if safe else "BLOCK",blocker=None if safe else "issue_after_cutoff")


def target_intent_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    expected=[str(item) for item in payload.get("expected_indicators",[])];text=str(payload.get("observed_output",""));hits=[item for item in expected if item in text];aligned=bool(expected) and len(hits)==len(expected)
    return _result("TARGET_INTENT_OBSERVED",{"expected":expected,"hits":hits,"aligned":aligned,"output_hash":hash_record(text)},status="PASS" if aligned else "BLOCK",blocker=None if aligned else "target_intent_mismatch")


def command_variant_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    command=payload.get("command");argv=list(command) if isinstance(command,list) else []
    safety=command_token_safety(argv);evidence={"argv":argv,"safety":safety,"authority":payload.get("authority"),"cwd":payload.get("cwd")}
    passed=bool(argv) and safety.get("status")=="PASS" and bool(payload.get("authority"));return _result("COMMAND_VARIANT_OBSERVED",evidence,status="PASS" if passed else "BLOCK",blocker=None if passed else "command_authority_or_safety_failed")


def source_commit_window_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    root=Path(payload.get("source_root","."));sha=str(payload.get("candidate_sha",""));run=subprocess.run(["git","-C",str(root),"cat-file","-t",sha],capture_output=True,text=True,timeout=30);passed=run.returncode==0 and run.stdout.strip()=="commit" and len(sha)==40
    return _result("SOURCE_WINDOW_OBSERVED",{"candidate_sha":sha,"object_type":run.stdout.strip(),"source_root":str(root),"cutoff":payload.get("cutoff")},status="PASS" if passed else "BLOCK",blocker=None if passed else "candidate_commit_unresolved")


def native_test_presence_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    root=Path(payload["source_root"]).resolve();path=(root/payload["test_path"]).resolve();inside=root==path or root in path.parents;passed=inside and path.is_file();evidence={"source_root":str(root),"test_path":str(path),"exists":path.is_file(),"sha256":sha256_file(path) if passed else None}
    return _result("NATIVE_TEST_PRESENCE_OBSERVED",evidence,status="PASS" if passed else "BLOCK",blocker=None if passed else "native_test_missing")


def issue_derived_harness_firewall_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    record=dict(payload.get("harness_record") or {});validation=validate_harness_origin_record(record);passed=validation.get("status")=="PASS" and payload.get("solution_guidance_used") is not True
    return _result("HARNESS_FIREWALL_OBSERVED",{"validation":validation,"solution_guidance_used":payload.get("solution_guidance_used",False),"record_hash":hash_record(record)},status="PASS" if passed else "BLOCK",blocker=None if passed else "harness_firewall_failed")


def runtime_incident_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    incident=capture_incident(command=list(payload.get("command",[])),cwd=payload.get("cwd","."),env=dict(payload.get("env",{})),stack_trace=str(payload.get("stack_trace","")),dependency_metadata=payload.get("dependency_metadata"),source_closure_hint=payload.get("source_closure_hint"),timestamp=payload.get("timestamp"));return _result("RUNTIME_INCIDENT_OBSERVED",incident)


def ast_excision_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    source_path=Path(payload["source_path"]);plan=plan_excision_probe(source_path,source_path.read_text(encoding="utf-8"),payload["sandbox_path"],payload["repo_root"]);return _result("AST_REGION_OBSERVED",plan,status="PASS" if plan["status"]=="PASS" else "BLOCK",blocker=plan.get("blocker"))


def null_comparability_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    comparable=comparable_matched_null_arms(payload.get("arm_a",{}),payload.get("arm_b",{}));return _result("NULL_COMPARABILITY_OBSERVED",{"comparable":comparable,"arm_a_hash":hash_record(payload.get("arm_a",{})),"arm_b_hash":hash_record(payload.get("arm_b",{}))},status="PASS" if comparable else "BLOCK",blocker=None if comparable else "null_arms_not_comparable")


def curvature_route_diversity_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    vector=curvature_feature_vector(payload.get("candidate",{}));routes=list(payload.get("routes",[]));passed=len({hash_record(route) for route in routes})>=2;return _result("ROUTE_DIVERSITY_OBSERVED",{"feature_vector":vector,"route_hashes":[hash_record(route) for route in routes],"diverse":passed},status="PASS" if passed else "BLOCK",blocker=None if passed else "route_diversity_not_established")


def interlock_invariant_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    from controllergate.core.interlock_runtime import evaluate_interlocks
    result=evaluate_interlocks(list(payload.get("interlock_ids",[])),candidate_id=payload["candidate_id"],prior_state=payload["prior_state"],proposed_next_state=payload["proposed_next_state"],evidence=dict(payload.get("interlock_evidence",{})),evidence_hashes=list(payload.get("evidence_hashes",[])));return _result("INTERLOCK_OBSERVED",result,status="PASS" if result["status"]=="PASS" else "BLOCK",blocker=None if result["status"]=="PASS" else "interlock_blocked")


def seed_replacement_probe_handler(payload):
    if (value:=_not_applicable(payload)):return value
    seed=dict(payload.get("seed") or {});result=classify_seed_for_repair(seed);return _result("SEED_REPLACEMENT_OBSERVED",result,status="PASS" if result["status"]=="PASS" else "BLOCK",blocker=result.get("blocker"))


PROBE_HANDLERS={name:globals()[name+"_handler"] for name in PROBE_TYPES}


def _verify(value:dict,expected:str)->dict:
    errors=[]
    if value.get("operation_status")!="PASS":errors.append("operation_not_completed")
    if value.get("observation") not in {expected,"NOT_APPLICABLE"}:errors.append("observation_type_mismatch")
    if value.get("evidence_hash")!=hash_record(value.get("evidence",{})):errors.append("evidence_hash_mismatch")
    if value.get("mutation_count")!=0:errors.append("mutation_detected")
    return {"status":"PASS" if not errors else "BLOCK","errors":errors,"independent_evidence_hash":hash_record(value.get("evidence",{}))}


def verify_dependency_lock_probe(v):return _verify(v,"DEPENDENCY_LOCK_OBSERVED")
def verify_issue_timestamp_probe(v):return _verify(v,"ISSUE_TIMESTAMP_OBSERVED")
def verify_target_intent_probe(v):return _verify(v,"TARGET_INTENT_OBSERVED")
def verify_command_variant_probe(v):return _verify(v,"COMMAND_VARIANT_OBSERVED")
def verify_source_commit_window_probe(v):return _verify(v,"SOURCE_WINDOW_OBSERVED")
def verify_native_test_presence_probe(v):return _verify(v,"NATIVE_TEST_PRESENCE_OBSERVED")
def verify_issue_derived_harness_firewall_probe(v):return _verify(v,"HARNESS_FIREWALL_OBSERVED")
def verify_runtime_incident_probe(v):return _verify(v,"RUNTIME_INCIDENT_OBSERVED")
def verify_ast_excision_probe(v):return _verify(v,"AST_REGION_OBSERVED")
def verify_null_comparability_probe(v):return _verify(v,"NULL_COMPARABILITY_OBSERVED")
def verify_curvature_route_diversity_probe(v):return _verify(v,"ROUTE_DIVERSITY_OBSERVED")
def verify_interlock_invariant_probe(v):return _verify(v,"INTERLOCK_OBSERVED")
def verify_seed_replacement_probe(v):return _verify(v,"SEED_REPLACEMENT_OBSERVED")
PROBE_VERIFIERS={name:globals()["verify_"+name] for name in PROBE_TYPES}


def executor_contracts() -> dict[str,dict[str,str]]:
    subsystems={
        "dependency_lock_probe":"historical_lock_verifier","issue_timestamp_probe":"decision_time_cutoff_verifier","target_intent_probe":"target_intent_alignment","command_variant_probe":"command_orthology_safety","source_commit_window_probe":"git_commit_object_verifier","native_test_presence_probe":"immutable_test_tree_verifier","issue_derived_harness_firewall_probe":"harness_origin_firewall","runtime_incident_probe":"runtime_incident_capture","ast_excision_probe":"active_ast_excision_probe","null_comparability_probe":"matched_null_comparability","curvature_route_diversity_probe":"curvature_feature_vector","interlock_invariant_probe":"interlock_runtime_and_verifier","seed_replacement_probe":"candidate_seed_admissibility",
    }
    return {name:{"typed_input_model":name.title().replace("_","")+"Input","candidate_scope_validation":"single_use_authorization","authorization_validator":"execute_probe","executor":PROBE_HANDLERS[name].__name__,"evidence_subsystem":subsystems[name],"typed_output_model":name.title().replace("_","")+"Observation","independent_verifier":PROBE_VERIFIERS[name].__name__,"applicable_rule":"explicit applicable=false returns NOT_APPLICABLE","network_policy":"none unless subsystem authority explicitly permits","mutation_policy":"none","resource_policy":"bounded","evidence_custody_rule":"raw evidence plus deterministic SHA256","stop_behavior":"fail_closed"} for name in PROBE_TYPES}
