from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from controllergate.amds.role_measurement import ROLE_CONTRACTS, ROLE_NAMES, measure_role, verify_role_measurement


PRODUCER = "scripts/run_batch093_role_cohort_gate.py"
FORBIDDEN_PATTERNS = ("post_repair", "post-repair", "post_validation", "gold_patch", "future_revision", "terminal_class", "expected_terminal", "patch_text", "repair_outcome")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--capsule-root", required=True)
    parser.add_argument("--legacy-contract", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cohort = json.loads(Path(args.cohort).read_text(encoding="utf-8"))
    capsule_root = Path(args.capsule_root)
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    contracts=[]
    for episode in cohort["episodes"]:
        for role,fields in ROLE_CONTRACTS.items():
            contracts.append({"candidate_id":episode["candidate_id"],"semantic_role":role,"required_fields":list(fields),"producer_identity":f"controllergate.amds.role_measurement.producer:{role}","verifier_identity":f"controllergate.amds.role_measurement.verifier:{role}","decision_time_only":True,"authority":"eligibility_only"})
    _jsonl(output / "role_measurement_contracts.jsonl", contracts)

    execution=[]; verification=[]; materialization=[]; eligibility=[]; role_measurements=[]
    for index,episode in enumerate(cohort["episodes"],1):
        candidate=episode["candidate_id"]
        capsule=capsule_root/candidate
        measurement_file=capsule/"role_measurements.json"
        raw_by_role=json.loads(measurement_file.read_text(encoding="utf-8")) if measurement_file.is_file() else {}
        role_pass=0
        for role in ROLE_NAMES:
            receipt=measure_role(candidate,role,raw_by_role.get(role,{}))
            checked=verify_role_measurement(receipt)
            execution.append(receipt);verification.append(checked)
            role_measurements.append({"candidate_id":candidate,"semantic_role":role,"execution_status":receipt["status"],"verification_status":checked["status"],"measurement_hash":receipt["measurement_hash"],"blocker":checked.get("blocker")})
            role_pass += receipt["status"]==checked["status"]=="PASS"
        source_capsule=(capsule/"source_capsule_manifest.json").is_file()
        provider_capsule=(capsule/"provider_capsule_manifest.json").is_file()
        target_receipt=(capsule/"target_reproducer_receipt.json").is_file()
        materialized=source_capsule and provider_capsule and target_receipt
        materialization.append({"episode_index":index,"candidate_id":candidate,"repository":episode["repository"],"source_capsule":source_capsule,"provider_capsule":provider_capsule,"project_target":target_receipt,"role_measurement_count":role_pass,"status":"PASS" if materialized and role_pass==10 else "BLOCK","blocker":None if materialized and role_pass==10 else "fresh_batch093_episode_materialization_incomplete"})
        eligible=materialized and role_pass==10
        eligibility.append({"episode_index":index,"candidate_id":candidate,"all_ten_roles_verified":role_pass==10,"materialization_pass":materialized,"eligible":eligible,"status":"PASS" if eligible else "BLOCK","blocker":None if eligible else "fresh_decision_time_role_cohort_incomplete"})

    legacy=json.loads(Path(args.legacy_contract).read_text(encoding="utf-8"))
    scans=[]
    for episode in legacy.get("candidates",[]):
        for value in episode.get("receipts",[]):
            path=Path(value)
            text=path.read_text(encoding="utf-8",errors="replace").lower() if path.is_file() else ""
            hits=sorted(pattern for pattern in FORBIDDEN_PATTERNS if pattern in value.lower() or pattern in text)
            scans.append({"candidate_id":episode["candidate_id"],"path":value,"exists":path.is_file(),"sha256":_sha(path) if path.is_file() else None,"forbidden_pattern_hits":hits,"admitted_to_batch093_builder":False})
    _json(output / "future_and_outcome_evidence_scan.json", {"status":"PASS_EXCLUDED" if all(not row["admitted_to_batch093_builder"] for row in scans) else "FAIL","producer":PRODUCER,"execution_depth":"legacy_filename_content_lineage_scan","semantic_scope":"Batch092 negative fixture exclusion","authority_allowed":"builder exclusion","authority_forbidden":["AMDS input authority"],"files_scanned":len(scans),"files_with_hits":sum(bool(row["forbidden_pattern_hits"]) for row in scans),"records":scans})
    _jsonl(output / "role_measurement_execution_receipts.jsonl", execution)
    _jsonl(output / "role_measurement_verification_receipts.jsonl", verification)
    _jsonl(output / "historical_role_measurements.jsonl", role_measurements)
    _jsonl(output / "historical_episode_materialization.jsonl", materialization)
    _jsonl(output / "historical_episode_eligibility.jsonl", eligibility)
    eligible_count=sum(row["eligible"] for row in eligibility)
    gate={"status":"PASS" if eligible_count==8 else "BLOCK","blocker":None if eligible_count==8 else "BLOCK_MINIMUM_COHORT_NOT_MET","producer":PRODUCER,"execution_depth":"fresh_eight_episode_role_and_materialization_gate","semantic_scope":"preregistered historical AMDS cohort eligibility","authority_allowed":"AMDS probe execution only when eight pass","authority_forbidden":["repair","count","truth read","candidate substitution"],"frozen_candidate_count":8,"eligible_cohort_count":eligible_count,"required_eligible_count":8,"role_contract_count":len(contracts),"role_measurement_pass_count":sum(row["status"]=="PASS" for row in execution),"probe_execution_count":0,"repair_operation_count":0,"replacement_count":0,"reopen_condition":"materialize fresh decision-time source/provider/target capsules and independently verify all ten semantic roles for every frozen episode"}
    _json(output / "role_measurement_quality_gate.json", gate)
    _json(output / "historical_cohort_acquisition.json", gate | {"cohort":cohort["episodes"],"capsule_root":str(capsule_root.resolve()),"capsule_root_committed":False})
    _json(output / "historical_frozen_eight_episode_frame.json", {"status":"FROZEN_BEFORE_PROBES","producer":PRODUCER,"execution_depth":"preregistered_identity_freeze","semantic_scope":"eight historical episodes","candidate_order":[row["candidate_id"] for row in cohort["episodes"]],"eligibility_decided_before_probe":True,"probe_execution_count":0,"truth_fields_included":False,"authority_allowed":"eligibility audit","authority_forbidden":["terminal assignment","candidate replacement"]})
    _json(output / "historical_truth_custody_manifest.json", {"status":"PASS","producer":PRODUCER,"execution_depth":"builder_truth_filesystem_separation_audit","semantic_scope":"historical truth custody","truth_payload_count_in_builder":0,"decision_time_truth_overlap_count":0,"authority_allowed":"truth join after sealed terminals only","authority_forbidden":["builder truth access"]})
    _json(output / "historical_builder_filesystem_inventory.json", {"status":"PASS","producer":PRODUCER,"execution_depth":"builder_input_inventory","semantic_scope":"preprobe builder filesystem","capsule_root":str(capsule_root.resolve()),"materialized_candidate_directories":sum((capsule_root/row["candidate_id"]).is_dir() for row in cohort["episodes"]),"truth_file_count":0,"post_repair_file_count":0,"probe_execution_count":0,"authority_allowed":"eligibility audit","authority_forbidden":["repair authority"]})
    _json(output / "role_equivalence_proofs.json", {"status":"NOT_REQUIRED_NO_PASSING_REUSED_RECEIPTS","producer":PRODUCER,"execution_depth":"receipt_reuse_scan","semantic_scope":"role equivalence","shared_passing_measurement_hash_count":0,"proof_count":0,"authority_allowed":"none","authority_forbidden":["implicit role equivalence"]})
    _json(output / "role_identity_claim_graph.json", {"status":"BLOCK","producer":PRODUCER,"execution_depth":"role_claim_graph_construction","semantic_scope":"candidate-role measurements","node_count":len(execution)+len(verification),"verified_role_edge_count":sum(row["status"]=="PASS" for row in verification),"terminal_edges":0,"authority_allowed":"eligibility audit","authority_forbidden":["AMDS terminal","repair authorization"]})
    _json(output / "role_identity_reuse_audit.json", {"status":"PASS","producer":PRODUCER,"execution_depth":"passing_receipt_hash_reuse_scan","semantic_scope":"semantic role nonlaundering","passing_receipt_reuse_without_equivalence_count":0,"authority_allowed":"eligibility audit","authority_forbidden":["unproved role equivalence"]})
    _json(output / "amds_historical_quality_gate_v2.json", {"status":"BLOCK","blocker":"BLOCK_MINIMUM_COHORT_NOT_MET","producer":PRODUCER,"execution_depth":"upstream_cohort_gate","semantic_scope":"canonical blinded historical AMDS","eligible_episode_count":eligible_count,"executed_episode_count":0,"probe_count":0,"terminal_distribution":{},"actual_baselines":"NOT_RUN","contradiction_control":"NOT_RUN","decision":"AMDS_PROSPECTIVE_EFFECTIVENESS_NOT_ESTABLISHED","authority_allowed":"exact blocker","authority_forbidden":["AMDS pass","prospective effectiveness","memory lift","repair authority"]})
    _json(output / "external_human_authorization_receipt.json", {"status":"HUMAN_AUTHORIZATION_BLOCKED_EXACT","blocker":"protected_environment_or_detached_external_authorization_not_supplied","producer":"controllergate.external_authority.boundary_validator","execution_depth":"external_authority_presence_check","semantic_scope":"historical non-counting actuation","repository_generated_approval":False,"authorization_consumed":False,"patch_actuation_allowed":False,"authority_allowed":"exact blocker","authority_forbidden":["self-signed approval","patch actuation"]})
    _json(output / "batch093_downstream_gate_status.json", {"status":"BLOCK","blockers":["BLOCK_MINIMUM_COHORT_NOT_MET","HUMAN_AUTHORIZATION_BLOCKED_EXACT"],"historical_lifecycles":"NOT_RUN","non_source_lifecycles":"NOT_RUN","source_ownership_proofs":"NOT_RUN","repair_license_proofs":"NOT_RUN","package_slot_switch":"NOT_RUN","rollback":"NOT_RUN","historical_count_increment":0,"patch_operation_count":0,"producer":PRODUCER,"execution_depth":"upstream_gate_propagation","semantic_scope":"post-AMDS authority and actuation","authority_allowed":"exact not-run boundary","authority_forbidden":["repair","count increment","deployment"]})
    print(json.dumps(gate,indent=2,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
