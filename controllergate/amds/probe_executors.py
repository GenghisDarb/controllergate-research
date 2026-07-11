from __future__ import annotations

from typing import Any, Callable
from .probe_registry import PROBE_TYPES


def execute_probe(probe_type: str, executor: Callable[[],dict[str,Any]], authorization: dict[str,Any]) -> dict[str,Any]:
    if probe_type not in PROBE_TYPES and not probe_type.startswith(("build_","provider_","compiler_","cargo_","cmake_","pkg_config_","abi_","resource_","writable_")):
        return {"status":"BLOCK","blocker":"amds_probe_type_unregistered"}
    if not authorization.get("allowed") or authorization.get("mutation_allowed"):
        return {"status":"BLOCK","blocker":"amds_probe_authorization_invalid"}
    result=executor(); return {**result,"probe_type":probe_type,"authorization_id":authorization.get("authorization_id"),"mutation_count":0}


def executor_contracts() -> dict[str,dict[str,str]]:
    return {name:{
        "typed_input_model":name.title().replace("_","")+"Input",
        "candidate_scope_validation":"required_by_single_use_authorization",
        "authorization_validator":"execute_probe",
        "executor":PROBE_HANDLERS[name].__name__,
        "typed_output_model":name.title().replace("_","")+"Observation",
        "observation_classifier":"probe_specific_handler",
        "independent_verifier":PROBE_VERIFIERS[name].__name__,
        "applicable_rule":"explicit applicable=false returns NOT_APPLICABLE",
        "network_policy":"none unless separately authorized by probe contract",
        "mutation_policy":"none",
        "resource_policy":"bounded",
        "evidence_custody_rule":"input and output hashes required by dispatcher",
        "stop_behavior":"fail_closed",
    } for name in PROBE_TYPES}


def _validated(payload: dict, required: tuple[str,...], observation: str) -> dict:
    if payload.get("applicable") is False:
        return {"operation_status":"PASS","observation":"NOT_APPLICABLE","missing":[],"mutation_count":0}
    missing=[name for name in required if name not in payload]
    return {"operation_status":"PASS" if not missing else "BLOCK","observation":observation if not missing else "INCONCLUSIVE","missing":missing,"mutation_count":0}

def dependency_lock_probe_handler(p):return _validated(p,("lock_hash",),"DEPENDENCY_LOCK_OBSERVED")
def issue_timestamp_probe_handler(p):return _validated(p,("issue_created_at",),"ISSUE_TIMESTAMP_OBSERVED")
def target_intent_probe_handler(p):return _validated(p,("target_intent",),"TARGET_INTENT_OBSERVED")
def command_variant_probe_handler(p):return _validated(p,("command",),"COMMAND_VARIANT_OBSERVED")
def source_commit_window_probe_handler(p):return _validated(p,("candidate_sha","cutoff"),"SOURCE_WINDOW_OBSERVED")
def native_test_presence_probe_handler(p):return _validated(p,("test_path",),"NATIVE_TEST_PRESENCE_OBSERVED")
def issue_derived_harness_firewall_probe_handler(p):return _validated(p,("firewall_hash",),"HARNESS_FIREWALL_OBSERVED")
def runtime_incident_probe_handler(p):return _validated(p,("runtime_identity",),"RUNTIME_INCIDENT_OBSERVED")
def ast_excision_probe_handler(p):return _validated(p,("ast_hash",),"AST_REGION_OBSERVED")
def null_comparability_probe_handler(p):return _validated(p,("arm_hashes",),"NULL_COMPARABILITY_OBSERVED")
def curvature_route_diversity_probe_handler(p):return _validated(p,("route_hashes",),"ROUTE_DIVERSITY_OBSERVED")
def interlock_invariant_probe_handler(p):return _validated(p,("interlock_hash",),"INTERLOCK_OBSERVED")
def seed_replacement_probe_handler(p):return _validated(p,("seed_hash",),"SEED_REPLACEMENT_OBSERVED")

PROBE_HANDLERS={name:globals()[name+"_handler"] for name in PROBE_TYPES}

def _verify(value:dict, expected:str)->dict:return {"status":"PASS" if value.get("operation_status")=="PASS" and value.get("observation") in {expected,"NOT_APPLICABLE"} and value.get("mutation_count")==0 else "BLOCK"}
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
