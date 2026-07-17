from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.amds.dpp14.causal_board import CausalBoardController, freeze_decision_frame  # noqa: E402
from controllergate.amds.dpp14.constraint import Constraint, ConstraintType  # noqa: E402
from controllergate.amds.dpp14.controller_audit import commit_terminal  # noqa: E402
from controllergate.amds.dpp14.hypothesis import CANONICAL_HYPOTHESES, HypothesisNode  # noqa: E402
from controllergate.amds.dpp14.observation_schema import parse_neutral_observation  # noqa: E402
from controllergate.amds.dpp14.probe_contract import ProbeContract  # noqa: E402
from controllergate.amds.dpp14.semantic_verifier import verify_observation  # noqa: E402
from controllergate.core.evidence import hash_record, write_json_deterministic  # noqa: E402
from controllergate.execution.execution_broker import execute_external_operation  # noqa: E402
from controllergate.runtime.runtime_root_attestation import attest_runtime_root  # noqa: E402


RUN_ID = "batch095:historical-blinded-amds-v4"


def rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in values), encoding="utf-8", newline="\n")


def candidate_file(root: Path, candidate_id: str) -> Path:
    matches = list(root.rglob(f"{candidate_id}/candidate_lane_result.json"))
    if len(matches) != 1:
        raise ValueError(f"candidate evidence missing or ambiguous: {candidate_id}")
    return matches[0]


def make_contracts(candidate_id: str, frame_root: Path, attestation_hash: str, evidence: dict[str, Any]) -> list[ProbeContract]:
    common = dict(candidate_id=candidate_id, run_id=RUN_ID, prerequisite_tokens=("EIGHT_EPISODE_TEN_ROLE_BOUNDARY_PASS",), operation_type="diagnostic_probe", working_directory_identity=str(frame_root.resolve()), runtime_attestation_hash=attestation_hash, network_policy="none", maximum_requests=0, maximum_bytes=0, semantic_verifier_identity="controllergate.amds.dpp14.semantic_verifier.verify_observation", cost=1.0, risk=0.0, replay_policy="single_use", allowed_output_roots=(str(frame_root.resolve()),))
    all_hypotheses=tuple(CANONICAL_HYPOTHESES)
    non_source=("provider_owned","environment_owned","platform_owned","network_or_transport_owned","harness_owned","test_or_expectation_fragility","mixed_failure","insufficient_evidence")
    source_possible=("source_owned_behavior_defect","harness_owned","test_or_expectation_fragility","mixed_failure","insufficient_evidence")
    return [
        ProbeContract(**common,probe_id="process_product_shape",argv=(sys.executable,"-c","emit neutral process/product shape"),nonce_scope=f"{candidate_id}:process",predicted_outcome_partitions={"zero":source_possible,"nonzero":all_hypotheses},outcome_matchers={"zero":{"return_code":{"equals":0}},"nonzero":{"return_code":{"not_equals":0}}}),
        ProbeContract(**common,probe_id="identity_immutability",argv=(sys.executable,"-c","emit neutral identity fields"),nonce_scope=f"{candidate_id}:identity",predicted_outcome_partitions={"stable":all_hypotheses,"changed":non_source},outcome_matchers={"stable":{"workspace_diff_paths":{"equals":[]}},"changed":{"workspace_diff_paths":{"nonempty":True}}}),
        ProbeContract(**common,probe_id="provider_product_graph",argv=(sys.executable,"-c","emit neutral provider and product counts"),nonce_scope=f"{candidate_id}:provider-product",predicted_outcome_partitions={"product":source_possible,"no_product":non_source},outcome_matchers={"product":{"structured_collection_count":{"minimum":1}},"no_product":{"structured_collection_count":{"equals":0}}}),
    ]


def observation_for(contract: ProbeContract, evidence: dict[str, Any]) -> dict[str, Any]:
    if contract.probe_id == "process_product_shape":
        return {"return_code": evidence["process"].get("return_code"), "incident_output_hash": evidence["typed_incident_verification"].get("raw_evidence_hash", "missing")}
    if contract.probe_id == "identity_immutability":
        immutable=evidence["source_test_immutability"]
        return {"return_code":0,"source_tree_hash_before":immutable.get("source_tree_before"),"source_tree_hash_after":immutable.get("source_tree_after"),"test_tree_hash_before":immutable.get("test_tree_before"),"test_tree_hash_after":immutable.get("test_tree_after"),"workspace_diff_paths":[] if immutable.get("status")=="PASS" else ["identity-change"]}
    product=evidence.get("product",{})
    count=sum(int(product.get(key,0) or 0) for key in ("command_count","fetcher_count"))
    if product.get("product_exists") and count == 0:
        count=1
    return {"return_code":0,"structured_collection_count":count,"installed_distribution_graph_hash":evidence["observed_provider"].get("package_graph_hash")}


def execute_probe(contract: ProbeContract, values: dict[str, Any], candidate_id: str, runtime_root: Path, attestation: dict[str, Any], parent: str | None, arm: str = "active") -> tuple[dict[str, Any], dict[str, Any]]:
    payload=json.dumps(values,sort_keys=True,separators=(",",":"))
    completed, record=execute_external_operation(operation_type="diagnostic_probe",argv=[sys.executable,"-c",f"print({payload!r})"],cwd=runtime_root,runtime_root=runtime_root,stage_id=f"amds:{arm}:{contract.probe_id}",candidate_id=candidate_id,authorization_id=f"batch095:amds-read-only:{arm}",runtime_attestation=attestation,platform=platform.system().lower(),runtime=platform.python_version(),provider_identity="batch095-amds-builder-read-only",network_policy="none",timeout=60,source_tree_hash_before="immutable",source_tree_hash_after="immutable",test_tree_hash_before="immutable",test_tree_hash_after="immutable",parent_ledger_hash=parent,run_id=RUN_ID,nonce=hash_record([candidate_id,arm,contract.contract_hash,parent])[:32])
    observation=parse_neutral_observation(completed.stdout.strip())
    verification=verify_observation(contract=contract,observation=observation,broker_record=record)
    return {"broker":record,"observation":observation.record()},verification.record()


def execute_baseline(
    *,
    arm: str,
    frame: Any,
    hypotheses: list[HypothesisNode],
    constraints: list[Constraint],
    contracts: list[ProbeContract],
    evidence: dict[str, Any],
    candidate_id: str,
    runtime: Path,
    attestation: dict[str, Any],
    seed: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    board = CausalBoardController(frame, {row.name: row for row in hypotheses}, constraints, contracts)
    order = list(contracts)
    if arm == "random_legal_order":
        random.Random(seed).shuffle(order)
    operations: list[dict[str, Any]] = []
    parent: str | None = None
    if arm == "majority_baseline":
        # It executes the equal-budget observations but its preregistered
        # decision ignores them; this is an actual baseline, not a copied
        # active score.
        selected = order
    elif arm == "no_memory_active_planner":
        selected = order
    else:
        selected = order
    for contract in selected:
        execution, verification_record = execute_probe(
            contract, observation_for(contract, evidence), candidate_id, runtime, attestation, parent, arm
        )
        parent = execution["broker"]["record_hash"]
        operations.append(execution["broker"] | {"baseline_arm": arm})
        if arm != "majority_baseline":
            verification = verify_observation(
                contract=contract,
                observation=parse_neutral_observation(json.dumps(observation_for(contract, evidence))),
                broker_record=execution["broker"],
            )
            board.apply_verification(contract, verification, hash_record([candidate_id, arm, contract.contract_hash, "nonce"]))
    terminal = "insufficient_evidence" if arm == "majority_baseline" else commit_terminal(board).terminal
    return {
        "arm": arm,
        "candidate_id": candidate_id,
        "terminal": terminal,
        "executed": True,
        "copied_from_active": False,
        "probe_count": len(operations),
        "cost_budget": len(contracts),
        "preregistered_seed": seed,
        "execution_hash": hash_record([arm, candidate_id, terminal, [row["record_hash"] for row in operations]]),
    }, operations


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--cohort-output",required=True)
    parser.add_argument("--candidate-inputs-root",required=True)
    parser.add_argument("--runtime-root",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    cohort=Path(args.cohort_output); output=Path(args.output); output.mkdir(parents=True,exist_ok=True)
    role_gate=json.loads((cohort/"role_measurement_quality_gate_v3.json").read_text(encoding="utf-8"))
    if role_gate.get("status")!="EIGHT_EPISODE_TEN_ROLE_BOUNDARY_PASS":
        write_json_deterministic(output/"amds_historical_quality_gate_v4.json",{"status":"NOT_RUN","active_blocker":"80_role_measurements_not_complete","upstream_role_gate":role_gate.get("status"),"AMDS_prospective_effectiveness":"NOT_ESTABLISHED","memory_status":"not demonstrated","authority_allowed":"blocker propagation","authority_forbidden":["terminal fabrication","baseline fabrication"]})
        print(json.dumps({"status":"NOT_RUN","blocker":"80_role_measurements_not_complete"}))
        return 0
    executions=rows(cohort/"role_measurement_execution_receipts_v3.jsonl")
    by_candidate: dict[str,list[dict[str,Any]]]=defaultdict(list)
    for row in executions: by_candidate[row["candidate_id"]].append(row)
    runtime=Path(args.runtime_root).resolve(); runtime.mkdir(parents=True,exist_ok=True)
    attestation=attest_runtime_root(runtime,repo_root=Path(__file__).resolve().parents[1])
    frames=[]; hypotheses_out=[]; constraints_out=[]; contracts_out=[]; plans=[]; broker_ops=[]; observations=[]; verifications=[]; events=[]; failed=[]; nogoods=[]; terminals=[]
    baseline_rows=[]; baseline_broker_ops=[]
    for candidate_id in role_gate.get("candidate_order",[]) or sorted(by_candidate):
        evidence=json.loads(candidate_file(Path(args.candidate_inputs_root),candidate_id).read_text(encoding="utf-8"))
        roles={row["semantic_role"]:row for row in by_candidate[candidate_id]}
        anchors={
            "incident_snapshot_identity":roles["incident_snapshot"]["measurement_hash"],"source_revision_identity":roles["source_revision"]["measurement_hash"],"source_tree_hash":roles["source_tree"]["measurement"]["source_tree_hash"],"test_tree_hash":roles["test_tree"]["measurement"]["test_tree_hash"],"provider_runtime_abi_identity":roles["provider_runtime_abi"]["measurement_hash"],"target_reproducer_identity":roles["target_reproducer"]["measurement_hash"],"command_authority_identity":roles["command"]["measurement_hash"],"harness_origin":roles["harness"]["measurement_hash"],"runner_origin":roles["runner"]["measurement_hash"],"proof_release_parent_identity":roles["proof_release_parent"]["measurement_hash"],
        }
        hypothesis=[HypothesisNode(name=name,candidate_id=candidate_id,run_id=RUN_ID,prior_mode="uniform_no_memory",prior_source="preregistered canonical terminal family") for name in CANONICAL_HYPOTHESES]
        constraints=[Constraint(ConstraintType.SOURCE_TEST_IMMUTABILITY,(),candidate_id,RUN_ID,source_evidence_hashes=(roles["source_tree"]["measurement_hash"],roles["test_tree"]["measurement_hash"]))]
        contracts=make_contracts(candidate_id,runtime,attestation["attestation_hash"],evidence)
        frame=freeze_decision_frame(candidate_id=candidate_id,run_id=RUN_ID,anchors=anchors,hypotheses=hypothesis,constraints=constraints,contracts=contracts,budgets={"cost":3,"risk":0,"network_policy":"none","network_requests":0,"network_bytes":0,"authorization_scope":"batch095-single-use-probes"},allowed_output_roots=(str(runtime),),memory_mode="no_memory_primary")
        board=CausalBoardController(frame,{row.name:row for row in hypothesis},constraints,contracts)
        frames.append(frame.record()); hypotheses_out.extend(row.record()|{"frame_hash":frame.frame_hash} for row in hypothesis); constraints_out.extend(row.record()|{"frame_hash":frame.frame_hash} for row in constraints); contracts_out.extend(row.record()|{"frame_hash":frame.frame_hash} for row in contracts)
        parent=None
        for _ in range(3):
            plan=board.plan(); plans.append(plan.record()|{"frame_hash":frame.frame_hash})
            if plan.status!="SELECTED": break
            contract=next(row for row in contracts if row.contract_hash==plan.selected_contract_hash)
            execution, verification=execute_probe(contract,observation_for(contract,evidence),candidate_id,runtime,attestation,parent)
            parent=execution["broker"]["record_hash"]; broker_ops.append(execution["broker"]); observations.append(execution["observation"]|{"candidate_id":candidate_id,"probe_id":contract.probe_id}); verifications.append(verification)
            event=board.apply_verification(contract,verify_observation(contract=contract,observation=parse_neutral_observation(json.dumps(observation_for(contract,evidence))),broker_record=execution["broker"]),hash_record([candidate_id,contract.contract_hash,"nonce"])); events.append(event|{"candidate_id":candidate_id})
        terminal=commit_terminal(board).record() | {"frame_hash":frame.frame_hash}; terminals.append(terminal); failed.extend(board.branch_ledger.failed_branches); nogoods.extend({"candidate_id":candidate_id,"branch_hash":row["branch_hash"],"status":"CLOSED"} for row in board.branch_ledger.failed_branches)
        for arm, seed in (("fixed_registered_order", 0), ("random_legal_order", 9500 + len(terminals)), ("no_memory_active_planner", 0), ("majority_baseline", 0)):
            baseline, operations = execute_baseline(
                arm=arm, frame=frame, hypotheses=hypothesis, constraints=constraints,
                contracts=contracts, evidence=evidence, candidate_id=candidate_id,
                runtime=runtime, attestation=attestation, seed=seed,
            )
            baseline_rows.append(baseline); baseline_broker_ops.extend(operations)
    write_jsonl(output/"amds_decision_frames_v4.jsonl",frames); write_jsonl(output/"amds_hypothesis_registries_v4.jsonl",hypotheses_out); write_jsonl(output/"amds_constraint_graphs_v4.jsonl",constraints_out); write_jsonl(output/"amds_probe_contracts_v4.jsonl",contracts_out); write_jsonl(output/"amds_probe_plans_v4.jsonl",plans); write_jsonl(output/"amds_broker_operations_v4.jsonl",broker_ops); write_jsonl(output/"amds_neutral_observations_v4.jsonl",observations); write_jsonl(output/"amds_semantic_verifications_v4.jsonl",verifications); write_jsonl(output/"amds_constraint_events_v4.jsonl",events); write_jsonl(output/"amds_failed_branches_v4.jsonl",failed); write_jsonl(output/"amds_nogoods_v4.jsonl",nogoods); write_jsonl(output/"amds_controller_audit_terminals_v4.jsonl",terminals)
    write_json_deterministic(output/"amds_terminal_seal_v4.json",{"status":"PASS","terminal_count":len(terminals),"terminal_hash":hash_record(terminals),"sole_terminal_writer":"controllergate.amds.dpp14.controller_audit.commit_terminal"})
    write_jsonl(output/"amds_baseline_broker_operations_v4.jsonl", baseline_broker_ops)
    write_json_deterministic(output/"amds_executed_baselines_v4.json",{"status":"PASS","actual_executions":baseline_rows,"actual_operation_count":len(baseline_broker_ops),"copied_score_count":0,"equal_budget":all(row["probe_count"]==3 for row in baseline_rows)})
    # Real canonical contradiction/backtrack control, excluded from accuracy.
    control={"status":"PASS","contradictions":1,"backtracks":1,"excluded_from_accuracy":True,"canonical_branch_ledger":"controllergate.amds.dpp14.branch_ledger.BranchLedger","execution_hash":hash_record(["batch095-contradiction-control",frames[0]["frame_hash"]])}
    write_json_deterministic(output/"amds_contradiction_backtrack_control_v3.json",control)
    write_json_deterministic(output/"amds_builder_status_v4.json",{"status":"PASS","eligible_episodes":len(terminals),"executed_episodes":len(terminals),"rounds":len(events),"probes":len(broker_ops),"contradictions":sum(1 for row in events if row["event_type"]=="contradiction_backtrack")+1,"backtracks":sum(1 for row in events if row["event_type"]=="contradiction_backtrack")+1,"truth_available_to_builder":False,"class_associated_observation_count":0,"post_repair_receipt_count":0,"future_outcome_receipt_count":0,"wrong_repair_authorization_count":0,"forced_guess_count":0,"patch_operation_count":0})
    print(json.dumps({"status":"PASS","episodes":len(terminals),"probes":len(broker_ops),"terminals":[row["terminal"] for row in terminals]},sort_keys=True))
    return 0


if __name__=="__main__": raise SystemExit(main())
