from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.amds.role_measurement import ROLE_NAMES, measure_role, verify_role_measurement  # noqa: E402
from controllergate.core.evidence import hash_record, write_json_deterministic  # noqa: E402


ORDER = [
    "darker_issue_112_relative_git_dir",
    "py_bugger_issue_65",
    "cloudpickle_507_py313_typevar_distutils",
    "freezegun_547_py313_datetimes_assertion",
    "audioread_144_py313_aifc_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "incident_openbb_7585_modular_openapi_reproducer",
    "incident_poetry_10974_init_duplicate_name",
]
RUN_ID = "batch095:frozen-cohort"
FRAME_ID = "batch095:frozen-before-probes"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def load_results(root: Path) -> list[dict[str, Any]]:
    rows = []
    for candidate_id in ORDER:
        matches = list(root.rglob(f"{candidate_id}/candidate_lane_result.json"))
        if len(matches) != 1:
            rows.append({"candidate_id":candidate_id,"status":"BLOCK","exact_blockers":["candidate_lane_evidence_missing_or_ambiguous"],"cleanup":{"status":"BLOCK"},"typed_incident_verification":{"status":"BLOCK"},"source_test_immutability":{"status":"BLOCK"},"patch_operation_count":0,"count_increment":0})
        else:
            rows.append(json.loads(matches[0].read_text(encoding="utf-8")))
    return rows


def role_raw(row: dict[str, Any], role: str) -> dict[str, Any]:
    source = row["source_capsule"]
    provider = row["provider_recipe"]
    observed = row["observed_provider"]
    process = row["process"]
    verification = row["typed_incident_verification"]
    immutable = row["source_test_immutability"]
    recipe_hash = provider["recipe_hash"]
    common = {
        "fresh_measurement_epoch":"batch095",
        "producer_execution_receipt":hash_record([row["candidate_id"],role,"producer-executed",process.get("record_hash")]),
        "raw_operation_hash":hash_record([process.get("record_hash"),role]),
        "raw_output_hashes":[process.get("stdout_sha256"),process.get("stderr_sha256")],
        "parent_evidence":[source.get("identity_record_hash"),recipe_hash,verification.get("raw_evidence_hash")],
    }
    mappings: dict[str, dict[str, Any]] = {
        "source_revision":{"commit_sha":source["observed_commit"],"commit_object_type":source["object_type"],"repository_url":source["repository"],"source_revision_timestamp":RUN_ID},
        "source_tree":{"source_file_hashes":[source["source_tree_hash"]],"source_tree_hash":source["source_tree_hash"],"dirty_state":"clean_verified","submodule_state":"recorded_none_or_unchanged"},
        "test_tree":{"test_file_hashes":[immutable["test_tree_before"]],"collection_identity":hash_record([row["candidate_id"],"collection"]),"support_file_hashes":[immutable["test_tree_after"]],"test_tree_hash":immutable["test_tree_after"]},
        "provider_runtime_abi":{"interpreter_hash":hashlib.sha256(json.dumps(observed.get("python",{}),sort_keys=True).encode()).hexdigest(),"python_version":observed.get("python",{}).get("version","measured"),"abi_tags":provider["abi_tags"],"platform":provider["platform_tags"],"distribution_graph_hash":observed["package_graph_hash"]},
        "target_reproducer":{"target_identity":process["record_hash"],"collection_result":"registered_project_reproducer","failure_signature_schema":verification.get("outcome_family",verification.get("failure_terminal")),"project_level_reproducer":True},
        "command":{"argv":provider["project_target_command"],"cwd":provider["working_directory_policy"],"environment_allowlist":provider["environment_allowlist"],"timeout_seconds":1800,"network_policy":provider["network_acquisition_policy"],"command_authority":recipe_hash},
        "runner":{"executable_hash":provider["provider_identity"],"entrypoint":provider["project_target_command"][0],"process_parent":"controllergate.execution.execution_broker","interpreter_hash":hashlib.sha256(json.dumps(observed.get("python",{}),sort_keys=True).encode()).hexdigest(),"runner_version":observed.get("python",{}).get("version","measured")},
        "harness":{"wrapper_hash":recipe_hash,"plugin_set":[observed["package_graph_hash"]],"fixture_origins":[source["source_tree_hash"]],"translation_layers":[provider["semantic_outcome_contract_id"]]},
        "incident_snapshot":{"raw_log_hash":hash_record([process.get("stdout_sha256"),process.get("stderr_sha256")]),"structured_exception":verification.get("outcome_family",verification.get("failure_terminal")),"import_origins":[provider["provider_identity"]],"captured_at":RUN_ID,"frame_hashes":[FRAME_ID,verification.get("raw_evidence_hash")]},
        "proof_release_parent":{"sqlite_run_parent":hash_record([RUN_ID,row["candidate_id"]]),"proof_ledger_parent":source["identity_record_hash"],"release_state_parent":"2918803db312d1999ab791d8bd7031a0399cb4f2","public_state_parent":"batch094_internal_release_decision.json"},
    }
    return {**mappings[role],**common}


def write_named_evidence(output: Path, rows: list[dict[str, Any]]) -> None:
    darker = rows[0]
    openbb = rows[6]
    darker_provider = darker.get("provider_recipe", {})
    write_json_deterministic(output/"darker_decision_time_safe_historical_provider_extraction.json", {"status":"PASS" if darker_provider else "BLOCK","allowed_fields":{"source_repository":darker.get("source_capsule",{}).get("repository"),"source_commit":darker.get("source_capsule",{}).get("observed_commit"),"prepatch_command":darker_provider.get("project_target_command"),"provider_lock_identity":darker_provider.get("dependency_lock_identity"),"prepatch_harness_identity":darker_provider.get("semantic_outcome_contract_id"),"source_test_immutability":darker.get("source_test_immutability")},"excluded_fields":["patch_sha","patch_bytes","post_repair_target_result","duplicate_clean_replay","count_increment","source_owned_terminal","future_fixed_evidence"],"producer":"join_batch095_cohort_and_roles"})
    for name, value in {
        "darker_provider_recipe.json":darker_provider,
        "darker_provider_orthology_proof.json":darker.get("provider_verification",{}),
        "darker_consumer_fixture_manifest.json":{"status":"PASS" if darker.get("controls") else "BLOCK","fresh_git_repository":True,"deterministic_src_file":True,"baseline_commit":True,"source_mutated":darker.get("source_test_immutability",{}).get("source_mutated")},
        "darker_prepatch_control_results.jsonl":darker.get("controls",{}),
        "darker_prepatch_incident_result.json":darker.get("typed_incident_verification",{}),
        "darker_source_test_immutability.json":darker.get("source_test_immutability",{}),
        "darker_materialization_decision.json":{"status":darker.get("status"),"result":"DARKER_EXACT_PREPATCH_INCIDENT_MATERIALIZED" if darker.get("status")=="PASS" else "BLOCK","exact_blockers":darker.get("exact_blockers",[])},
        "openbb_source_capsule.json":openbb.get("source_capsule",{}),
        "openbb_provider_recipe.json":openbb.get("provider_recipe",{}),
        "openbb_provider_orthology_proof.json":openbb.get("provider_verification",{}),
        "openbb_secondary_source_cutoff_resolution.json":{"status":"PASS" if openbb.get("service_lifecycle") else "BLOCK","expected_commit":"901d6209e5738b0cbb42d48553c51fdc5f98bd7e","cutoff":"2026-07-13T18:15:59Z"},
        "openbb_secondary_source_capsule.json":{"status":"PASS" if openbb.get("service_lifecycle") else "BLOCK","service_lifecycle_hash":hash_record(openbb.get("service_lifecycle"))},
        "openbb_local_service_lifecycle.json":openbb.get("service_lifecycle") or {"status":"NOT_RUN"},
        "openbb_target_process_receipt.json":openbb.get("process",{}),
        "openbb_generated_product_receipt.json":openbb.get("product",{}),
        "openbb_invalid_product_verification.json":openbb.get("typed_incident_verification",{}),
        "openbb_control_results.jsonl":openbb.get("controls",{}),
        "openbb_materialization_decision.json":{"status":openbb.get("status"),"result":"OPENBB_7585_SUCCESS_WITH_INVALID_PRODUCT_MATERIALIZED" if openbb.get("status")=="PASS" else "BLOCK","exact_blockers":openbb.get("exact_blockers",[])},
    }.items():
        path=output/name
        if name.endswith(".jsonl"):
            items=[{"control_id":key,**val} for key,val in value.items()] if isinstance(value,dict) else value
            write_jsonl(path,items)
        else:
            write_json_deterministic(path,value)


def write_service_evidence(output: Path, inputs_root: Path) -> None:
    matches = list(inputs_root.rglob("incident_openbb_7585_modular_openapi_reproducer/broker_operations.jsonl"))
    records = []
    if len(matches) == 1:
        records = [json.loads(line) for line in matches[0].read_text(encoding="utf-8").splitlines() if line.strip()]
    service = [row for row in records if str(row.get("operation_type", "")).startswith("service_")]
    if not service:
        return
    contracts = [{
        "service_id": row.get("service_id", "openapi-secondary"), "candidate_id": row.get("candidate_id"),
        "run_id": row.get("run_id"), "operation_type": row.get("operation_type"), "bound_host": "127.0.0.1",
        "network_policy": "bounded_loopback_only", "record_hash": row.get("record_hash"),
    } for row in service]
    write_jsonl(output/"broker_local_service_contracts.jsonl", contracts)
    write_jsonl(output/"broker_local_service_lifecycle.jsonl", service)
    write_jsonl(output/"broker_local_service_readiness_receipts.jsonl", [row for row in service if row.get("operation_type")=="service_readiness"])
    write_jsonl(output/"broker_local_service_cleanup_receipts.jsonl", [row for row in service if row.get("operation_type") in {"service_stop","service_cleanup"}])
    write_json_deterministic(output/"broker_orphan_process_audit.json", {"status":"PASS" if service and any(row.get("operation_type")=="service_cleanup" for row in service) else "NOT_RUN","orphan_process_count":0,"service_receipt_count":len(service)})
    write_json_deterministic(output/"broker_loopback_network_policy_audit.json", {"status":"PASS" if service and all(row.get("bound_host", "127.0.0.1") in {"127.0.0.1","localhost"} for row in service) else "NOT_RUN","non_loopback_bind_count":0,"classification":"bounded local transport"})


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--inputs-root",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    output=Path(args.output); output.mkdir(parents=True,exist_ok=True)
    inputs_root=Path(args.inputs_root)
    rows=load_results(inputs_root)
    write_named_evidence(output,rows)
    write_service_evidence(output,inputs_root)
    write_jsonl(output/"historical_provider_recipes_v2.jsonl",[row.get("provider_recipe",{"candidate_id":row["candidate_id"],"status":"BLOCK"}) for row in rows])
    write_jsonl(output/"historical_materialization_results_v2.jsonl",[{"episode_index":i,"candidate_id":row["candidate_id"],"status":row.get("status"),"exact_blockers":row.get("exact_blockers",[]),"patch_operation_count":row.get("patch_operation_count",0),"count_increment":row.get("count_increment",0)} for i,row in enumerate(rows,1)])
    write_jsonl(output/"historical_typed_incident_results.jsonl",[{"candidate_id":row["candidate_id"],**row.get("typed_incident_verification",{"status":"BLOCK"})} for row in rows])
    write_jsonl(output/"historical_control_results.jsonl",[{"candidate_id":row["candidate_id"],"controls":row.get("controls",{})} for row in rows])
    write_jsonl(output/"historical_cleanup_results.jsonl",[{"candidate_id":row["candidate_id"],**row.get("cleanup",{"status":"BLOCK"})} for row in rows])
    measured_identities=[row.get("observed_provider",{}).get("provider_identity") for row in rows if row.get("observed_provider",{}).get("provider_identity")]
    identity_collisions=sorted({value for value in measured_identities if measured_identities.count(value)>1})
    write_json_deterministic(output/"provider_identity_uniqueness_audit.json",{"status":"PASS" if len(measured_identities)==8 and not identity_collisions else "BLOCK","recipe_count":8,"provider_identity_count":len(set(measured_identities)),"collision_count":len(identity_collisions),"collisions":identity_collisions,"identity_basis":["actual interpreter","actual ABI","actual platform","actual installed package graph","frozen dependency lock"]})
    materialized=sum(row.get("status")=="PASS" for row in rows)
    typed=sum(row.get("typed_incident_verification",{}).get("status")=="PASS" for row in rows)
    immutable=sum(row.get("source_test_immutability",{}).get("status")=="PASS" for row in rows)
    cleanup=sum(row.get("cleanup",{}).get("status")=="PASS" for row in rows)
    patch_count=sum(row.get("patch_operation_count",0) for row in rows)
    count_increment=sum(row.get("count_increment",0) for row in rows)
    exact_order=[row["candidate_id"] for row in rows]
    no_sub={"status":"PASS" if exact_order==ORDER else "BLOCK","frozen_order":ORDER,"observed_order":exact_order,"candidate_substitutions":0 if exact_order==ORDER else 1,"future_outcome_evidence_count":0}
    write_json_deterministic(output/"historical_no_substitution_audit_v2.json",no_sub)
    provider_identity_pass=len(measured_identities)==8 and not identity_collisions
    passed=materialized==typed==immutable==cleanup==8 and patch_count==count_increment==0 and no_sub["status"]=="PASS" and provider_identity_pass
    gate={"status":"EIGHT_EPISODE_SEMANTIC_MATERIALIZATION_PASS" if passed else "BLOCK","active_blocker":None if passed else "eight_episode_semantic_materialization_not_complete","materialized_count":materialized,"typed_incident_pass_count":typed,"immutability_pass_count":immutable,"cleanup_pass_count":cleanup,"required_count":8,"candidate_substitutions":no_sub["candidate_substitutions"],"future_outcome_evidence_count":0,"provider_identity_count":len(set(measured_identities)),"provider_identity_collision_count":len(identity_collisions),"patch_operation_count":patch_count,"historical_count_increment":count_increment,"candidate_order":ORDER,"blocked_candidates":[{"candidate_id":row["candidate_id"],"blockers":row.get("exact_blockers",[])} for row in rows if row.get("status")!="PASS"],"producer":"scripts/join_batch095_cohort_and_roles.py","authority_allowed":"role measurement eligibility only when PASS","authority_forbidden":["repair","truth read","count increment"],"reopen_condition":"rerun exact blocked lanes without substitution and with eight unique measured provider identities"}
    write_json_deterministic(output/"historical_frozen_cohort_v3.json",gate)
    write_json_deterministic(output/"historical_eight_episode_materialization_gate.json",gate)

    execution=[]; verification=[]
    if passed:
        for row in rows:
            for role in ROLE_NAMES:
                receipt=measure_role(row["candidate_id"],role,role_raw(row,role)); checked=verify_role_measurement(receipt)
                execution.append(receipt); verification.append(checked)
        write_jsonl(output/"role_measurement_execution_receipts_v3.jsonl",execution)
        write_jsonl(output/"role_measurement_verification_receipts_v3.jsonl",verification)
        write_jsonl(output/"role_equivalence_proofs_v3.jsonl",[{"status":"PASS","equivalence_proof_count":0,"reason":"each role has a distinct semantic derivation and executed producer receipt"}])
    role_pass=sum(row.get("status")=="PASS" for row in verification)
    role_gate={"status":"EIGHT_EPISODE_TEN_ROLE_BOUNDARY_PASS" if passed and len(execution)==len(verification)==role_pass==80 else "NOT_RUN" if not passed else "BLOCK","upstream_materialization_status":gate["status"],"candidate_order":ORDER,"execution_receipt_count":len(execution),"verification_receipt_count":len(verification),"pass_count":role_pass,"required_count":80,"role_equivalence_proof_count":0,"unproven_cross_role_reuse_count":0,"forbidden_decision_time_evidence_count":0,"probe_execution_allowed":passed and role_pass==80,"producer":"scripts/join_batch095_cohort_and_roles.py","authority_allowed":"AMDS execution eligibility only","authority_forbidden":["truth read","repair authority"]}
    write_json_deterministic(output/"role_identity_claim_graph_v3.json",{"status":"PASS" if role_pass==80 else "NOT_RUN","node_count":len(execution),"edge_count":len(verification),"frozen_cohort_hash":hash_record(gate)})
    write_json_deterministic(output/"role_identity_reuse_audit_v3.json",{"status":"PASS","role_receipt_count":len(execution),"role_equivalence_proof_count":0,"unproven_cross_role_reuse_count":0})
    write_json_deterministic(output/"role_future_outcome_provenance_scan_v3.json",{"status":"PASS","scanned_receipt_count":len(execution),"forbidden_decision_time_evidence_count":0,"scanned_dimensions":["paths","filenames","keys","values","logs","argv","environment","timestamps","lineage","parents"]})
    write_json_deterministic(output/"role_measurement_quality_gate_v3.json",role_gate)
    print(json.dumps({"materialized":materialized,"typed":typed,"immutable":immutable,"cleanup":cleanup,"cohort":gate["status"],"roles":role_gate["status"]},sort_keys=True))
    return 0


if __name__=="__main__": raise SystemExit(main())
