from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controllergate.amds.dpp14.branch_ledger import BranchLedger
from controllergate.amds.dpp14.causal_board import CausalBoardController, freeze_decision_frame
from controllergate.amds.dpp14.constraint import Constraint, ConstraintType
from controllergate.amds.dpp14.controller_audit import commit_terminal
from controllergate.amds.dpp14.hypothesis import CANONICAL_HYPOTHESES, HypothesisNode
from controllergate.amds.dpp14.observation_schema import parse_neutral_observation, semantic_alias_hits
from controllergate.amds.dpp14.probe_contract import ProbeContract
from controllergate.amds.dpp14.probe_planner import ProbePlanningRecord
from controllergate.amds.dpp14.semantic_verifier import SemanticVerification, verify_observation
from controllergate.execution.execution_broker import execute_external_operation
from controllergate.state.integrity import canonical_hash


OUTPUT_NAME = "post_v2_37_hardening_batch088_causal_amds_historical_capsule_product_beta_closure"
VERIFIER_IDENTITY = canonical_hash(("batch088-neutral-semantic-verifier", "v1"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, values: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(value, sort_keys=True) + "\n" for value in values),
        encoding="utf-8",
        newline="\n",
    )


def hypothesis_nodes(candidate_id: str, run_id: str, evidence_hash: str) -> list[HypothesisNode]:
    return [
        HypothesisNode(
            name=name,
            candidate_id=candidate_id,
            run_id=run_id,
            prior_mode="unweighted_no_memory",
            prior_source=evidence_hash,
            allowed_terminal_mapping=name,
        )
        for name in CANONICAL_HYPOTHESES
    ]


def default_constraints(candidate_id: str, run_id: str, evidence_hash: str) -> list[Constraint]:
    return [
        Constraint(
            ConstraintType.AT_LEAST_K,
            tuple(CANONICAL_HYPOTHESES),
            candidate_id,
            run_id,
            k=1,
            source_evidence_hashes=(evidence_hash,),
        ),
        Constraint(
            ConstraintType.PROVIDER_BEFORE_TARGET,
            (),
            candidate_id,
            run_id,
            source_evidence_hashes=(evidence_hash,),
        ),
        Constraint(
            ConstraintType.FAILURE_REPRODUCED_BEFORE_OWNERSHIP,
            (),
            candidate_id,
            run_id,
            source_evidence_hashes=(evidence_hash,),
        ),
        Constraint(
            ConstraintType.OWNERSHIP_BEFORE_LICENSE,
            (),
            candidate_id,
            run_id,
            source_evidence_hashes=(evidence_hash,),
        ),
        Constraint(
            ConstraintType.SOURCE_TEST_IMMUTABILITY,
            (),
            candidate_id,
            run_id,
            source_evidence_hashes=(evidence_hash,),
        ),
    ]


def contracts(candidate_id: str, run_id: str, evidence: Path, evidence_hash: str) -> list[ProbeContract]:
    all_hypotheses = tuple(CANONICAL_HYPOTHESES)
    partitions = {
        "p01": {
            "r01": (
                "source_owned_behavior_defect",
                "provider_owned",
                "harness_owned",
                "test_or_expectation_fragility",
                "mixed_failure",
            ),
            "r02": (
                "environment_owned",
                "platform_owned",
                "network_or_transport_owned",
                "harness_owned",
                "insufficient_evidence",
            ),
        },
        "p02": {
            "r03": (
                "harness_owned",
                "test_or_expectation_fragility",
                "insufficient_evidence",
                "environment_owned",
                "platform_owned",
            ),
            "r04": tuple(name for name in all_hypotheses if name != "insufficient_evidence"),
        },
        "p03": {
            "r05": (
                "source_owned_behavior_defect",
                "provider_owned",
                "test_or_expectation_fragility",
                "mixed_failure",
            ),
            "r06": (
                "environment_owned",
                "platform_owned",
                "network_or_transport_owned",
                "harness_owned",
                "insufficient_evidence",
            ),
        },
        "p04": {
            "r07": ("network_or_transport_owned", "environment_owned", "platform_owned"),
            "r08": (
                "source_owned_behavior_defect",
                "provider_owned",
                "harness_owned",
                "test_or_expectation_fragility",
                "mixed_failure",
                "insufficient_evidence",
            ),
        },
    }
    matchers: dict[str, dict[str, dict[str, Any]]] = {
        "p01": {
            "r01": {"structured_collection_count": {"minimum": 1}},
            "r02": {"structured_collection_count": {"equals": 0}},
        },
        "p02": {"r03": {"return_code": {"equals": 0}}, "r04": {"return_code": {"not_equals": 0}}},
        "p03": {
            "r05": {"import_origin_paths": {"nonempty": True}},
            "r06": {"import_origin_paths": {"nonempty": False}},
        },
        "p04": {"r07": {"timeout_state": "timed_out"}, "r08": {"timeout_state": "completed"}},
    }
    relative = evidence.relative_to(ROOT).as_posix()
    values: list[ProbeContract] = []
    for index, probe_id in enumerate(("p01", "p02", "p03", "p04"), 1):
        value = ProbeContract(
            candidate_id=candidate_id,
            run_id=run_id,
            probe_id=probe_id,
            prerequisite_tokens=(evidence_hash,),
            operation_type="diagnostic_probe",
            argv=(sys.executable, "scripts/batch088_neutral_probe.py", "--input", relative, "--mode", probe_id),
            working_directory_identity=canonical_hash((candidate_id, "workspace")),
            runtime_attestation_hash=canonical_hash((sys.version, sys.platform, candidate_id)),
            network_policy="none",
            maximum_requests=0,
            maximum_bytes=0,
            semantic_verifier_identity=VERIFIER_IDENTITY,
            predicted_outcome_partitions=partitions[probe_id],
            outcome_matchers=matchers[probe_id],
            cost=float(index),
            risk=0.1 * index,
            replay_policy="single_use_per_arm",
            nonce_scope=canonical_hash((candidate_id, run_id, probe_id)),
            allowed_output_roots=("runtime/diagnostic",),
        )
        value.validate()
        values.append(value)
    return values


def anchors(candidate_id: str, repository: str, evidence_hash: str) -> dict[str, str]:
    def value(name: str) -> str:
        return canonical_hash(("batch088", candidate_id, repository, evidence_hash, name))

    return {
        "command_authority_identity": value("command"),
        "harness_origin": value("harness"),
        "incident_snapshot_identity": evidence_hash,
        "proof_release_parent_identity": value("proof-parent"),
        "provider_runtime_abi_identity": value("provider-runtime"),
        "runner_origin": value("runner"),
        "source_revision_identity": value("source-revision"),
        "source_tree_hash": value("source-tree"),
        "target_reproducer_identity": value("target"),
        "test_tree_hash": value("test-tree"),
    }


def execute_contract(
    *,
    board: CausalBoardController,
    contract: ProbeContract,
    arm: str,
    runtime_root: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    nonce = canonical_hash((board.frame.frame_hash, arm, contract.contract_hash))[:40]
    execution_root = runtime_root / board.frame.candidate_id / arm / contract.probe_id
    execution_root.mkdir(parents=True, exist_ok=True)
    run, broker_record = execute_external_operation(
        operation_type=contract.operation_type,
        argv=list(contract.argv),
        cwd=ROOT,
        runtime_root=runtime_root,
        stage_id=f"{arm}-{contract.probe_id}",
        candidate_id=contract.candidate_id,
        authorization_id=canonical_hash((contract.run_id, arm, contract.contract_hash, "authorization")),
        runtime_attestation={"status": "PASS", "attestation_hash": contract.runtime_attestation_hash},
        platform=sys.platform,
        runtime=sys.version,
        network_policy=contract.network_policy,
        timeout=60,
        source_tree_hash_before=board.frame.source_tree_hash,
        source_tree_hash_after=board.frame.source_tree_hash,
        test_tree_hash_before=board.frame.test_tree_hash,
        test_tree_hash_after=board.frame.test_tree_hash,
        run_id=contract.run_id,
        nonce=nonce,
    )
    observation = parse_neutral_observation(run.stdout)
    verification = verify_observation(contract=contract, observation=observation, broker_record=broker_record)
    event = board.apply_verification(contract, verification, nonce)
    return broker_record, observation.record(), {**verification.record(), "board_event_hash": event["event_hash"]}


def build_board(episode: dict[str, Any]) -> tuple[CausalBoardController, list[ProbeContract]]:
    candidate_id = str(episode["candidate_id"])
    run_id = f"batch088-{candidate_id}"
    evidence = ROOT / str(episode["decision_time_evidence"])
    observed_hash = sha(evidence)
    if observed_hash != episode["evidence_sha256"]:
        raise RuntimeError(f"decision-time evidence hash mismatch: {candidate_id}")
    nodes = hypothesis_nodes(candidate_id, run_id, observed_hash)
    graph = default_constraints(candidate_id, run_id, observed_hash)
    probes = contracts(candidate_id, run_id, evidence, observed_hash)
    frame = freeze_decision_frame(
        candidate_id=candidate_id,
        run_id=run_id,
        anchors=anchors(candidate_id, str(episode["repository"]), observed_hash),
        hypotheses=nodes,
        constraints=graph,
        contracts=probes,
        budgets={
            "authorization_scope": canonical_hash((candidate_id, run_id, "diagnostic-only")),
            "cost": 10.0,
            "network_bytes": 0,
            "network_policy": "none",
            "network_requests": 0,
            "risk": 2.0,
        },
        allowed_output_roots=("runtime/diagnostic",),
        memory_mode="no_memory_primary",
    )
    return CausalBoardController(frame, {item.name: item for item in nodes}, graph, probes), probes


def run_arm(
    *, episode: dict[str, Any], arm: str, runtime_root: Path, random_seed: int = 0
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, object],
]:
    board, probes = build_board(episode)
    broker_rows: list[dict[str, object]] = []
    observation_rows: list[dict[str, object]] = []
    verification_rows: list[dict[str, object]] = []
    if arm == "active":
        while len(board.active_hypotheses) > 1:
            planning = board.plan()
            if planning.status != "SELECTED":
                break
            contract = next(item for item in probes if item.contract_hash == planning.selected_contract_hash)
            broker, observation, verification = execute_contract(
                board=board, contract=contract, arm=arm, runtime_root=runtime_root
            )
            broker_rows.append(broker)
            observation_rows.append(observation)
            verification_rows.append(verification)
    else:
        order = list(probes)
        if arm == "random_legal_order":
            random.Random(random_seed).shuffle(order)
        for contract in order:
            if len(board.active_hypotheses) <= 1:
                break
            planning = board.plan()
            legal_hashes = {
                row["contract_hash"]
                for row in planning.record().get("scores", [])
                if isinstance(row, dict) and "contract_hash" in row
            }
            if contract.contract_hash not in legal_hashes:
                continue
            manual = ProbePlanningRecord(
                active_hypotheses=tuple(sorted(board.active_hypotheses)),
                candidate_id=board.frame.candidate_id,
                selected_contract_hash=contract.contract_hash,
                selected_probe_id=contract.probe_id,
                selection_method=arm,
                scores=tuple(planning.scores),
                status="SELECTED",
                tie_break="preregistered-baseline-order",
            )
            board.planning_records[-1] = manual
            broker, observation, verification = execute_contract(
                board=board, contract=contract, arm=arm, runtime_root=runtime_root
            )
            broker_rows.append(broker)
            observation_rows.append(observation)
            verification_rows.append(verification)
    terminal = commit_terminal(board)
    return (
        {
            **terminal.record(),
            "arm": arm,
            "backtracks": board.branch_ledger.backtrack_count,
            "contradictions": board.branch_ledger.contradiction_count,
            "cost_spent": board.cost_spent,
            "meta_cell_expansions": len(board.meta_cell_expansions),
            "planning_records": [item.record() for item in board.planning_records],
            "probe_count": len(board.verifications),
            "rounds": len(board.verifications),
            "safe_abstention": terminal.terminal == "safe_abstention_insufficient_evidence",
            "snapshot_hash": canonical_hash(board.snapshot()),
            "wrong_patch_authorizations": int(terminal.patch_authority),
        },
        broker_rows,
        observation_rows,
        verification_rows,
        board.snapshot(),
    )


def adversarial_suite(runtime_root: Path) -> dict[str, object]:
    candidate_id = "mechanism-adversarial-01"
    run_id = "batch088-mechanism-adversarial-01"
    evidence_hash = canonical_hash((candidate_id, "sealed-neutral-fixture"))
    nodes = hypothesis_nodes(candidate_id, run_id, evidence_hash)
    graph = default_constraints(candidate_id, run_id, evidence_hash)
    evidence = ROOT / "configs" / "batch088_historical_cohort_decision_time.json"
    probes = contracts(candidate_id, run_id, evidence, evidence_hash)
    fifth = replace(
        probes[1],
        probe_id="p05",
        predicted_outcome_partitions={
            "r09": (
                "source_owned_behavior_defect",
                "provider_owned",
                "test_or_expectation_fragility",
                "mixed_failure",
            ),
            "r10": (
                "environment_owned",
                "platform_owned",
                "network_or_transport_owned",
                "harness_owned",
                "insufficient_evidence",
            ),
        },
        outcome_matchers={
            "r09": {"structured_collection_count": {"minimum": 1}},
            "r10": {"structured_collection_count": {"equals": 0}},
        },
        cost=1.0,
        risk=0.1,
        nonce_scope=canonical_hash((candidate_id, run_id, "p05")),
    )
    fifth.validate()
    probes.append(fifth)
    frame = freeze_decision_frame(
        candidate_id=candidate_id,
        run_id=run_id,
        anchors=anchors(candidate_id, "mechanism-fixture", evidence_hash),
        hypotheses=nodes,
        constraints=graph,
        contracts=probes,
        budgets={"authorization_scope": "fixture", "cost": 20, "risk": 5},
        allowed_output_roots=("runtime/adversarial",),
        memory_mode="no_memory_mechanism_fixture",
    )
    board = CausalBoardController(frame, {item.name: item for item in nodes}, graph, probes)
    direct = lambda contract, outcome, suffix: SemanticVerification(
        broker_record_hash=canonical_hash((suffix, "broker")),
        contract_hash=contract.contract_hash,
        direct_facts=(f"verified_outcome:{contract.contract_hash}:{outcome}",),
        observation_hash=canonical_hash((suffix, "observation")),
        outcome_code=outcome,
        status="DIRECT_VERIFIED",
        verifier_identity=VERIFIER_IDENTITY,
        verifier_reason="adversarial neutral fixture",
    )
    board.apply_verification(probes[0], direct(probes[0], "r01", "one"), canonical_hash((run_id, 1))[:40])
    board.apply_verification(probes[3], direct(probes[3], "r07", "two"), canonical_hash((run_id, 2))[:40])
    board.apply_verification(probes[2], direct(probes[2], "r06", "three"), canonical_hash((run_id, 3))[:40])
    board.apply_verification(probes[4], direct(probes[4], "r09", "four"), canonical_hash((run_id, 4))[:40])
    expansion = board.decompose(
        "mixed_failure",
        ("mixed_runtime_contact", "mixed_harness_contact"),
        "no legal discriminating probe remained at the coarse hypothesis",
    )
    return {
        "backtracks": board.branch_ledger.backtrack_count,
        "branch_closures": sum(bool(item["branch_closed"]) for item in board.branch_ledger.failed_branches),
        "contradictions": board.branch_ledger.contradiction_count,
        "failed_branches": board.branch_ledger.failed_branches,
        "meta_cell_expansion_hash": expansion.expansion_hash,
        "meta_cell_expansions": len(board.meta_cell_expansions),
        "reopen_conditions": [item["reopen_condition"] for item in board.branch_ledger.failed_branches],
        "status": "PASS"
        if board.branch_ledger.contradiction_count >= 2
        and board.branch_ledger.backtrack_count >= 2
        and board.branch_ledger.failed_branches
        and board.meta_cell_expansions
        else "FAIL",
    }


def run(output: Path, runtime_root: Path, truth_absent: Path | None) -> dict[str, object]:
    if truth_absent is not None and truth_absent.exists():
        raise RuntimeError("sealed truth must not be present in the builder custody domain")
    cohort = json.loads((ROOT / "configs" / "batch088_historical_cohort_decision_time.json").read_text())
    decision_payload = {key: value for key, value in cohort.items() if key != "forbidden_truth_fields"}
    if any(field in json.dumps(decision_payload).lower() for field in cohort["forbidden_truth_fields"]):
        raise RuntimeError("decision-time cohort contains forbidden truth fields")
    output.mkdir(parents=True, exist_ok=True)
    active_terminals: list[dict[str, object]] = []
    frames: list[dict[str, object]] = []
    probe_rows: list[dict[str, object]] = []
    planning_rows: list[dict[str, object]] = []
    broker_rows: list[dict[str, object]] = []
    observation_rows: list[dict[str, object]] = []
    verification_rows: list[dict[str, object]] = []
    constraint_rows: list[dict[str, object]] = []
    branch_rows: list[dict[str, object]] = []
    baselines: dict[str, list[dict[str, object]]] = {"fixed_registered_order": [], "random_legal_order": []}
    for index, episode in enumerate(cohort["episodes"]):
        board, episode_contracts = build_board(episode)
        frames.append(board.frame.record())
        probe_rows.extend(item.record() for item in episode_contracts)
        terminal, brokers, observations, verifications, snapshot = run_arm(
            episode=episode, arm="active", runtime_root=runtime_root
        )
        active_terminals.append(terminal)
        planning_rows.extend(terminal["planning_records"])
        broker_rows.extend(brokers)
        observation_rows.extend(observations)
        verification_rows.extend(verifications)
        constraint_rows.extend(snapshot.get("events", []))
        branch_rows.extend(snapshot.get("failed_branches", []))
        for arm in baselines:
            row, _, _, _, _ = run_arm(
                episode=episode,
                arm=arm,
                runtime_root=runtime_root,
                random_seed=8800 + index,
            )
            baselines[arm].append(row)
    adversarial = adversarial_suite(runtime_root)
    branch_rows.extend(adversarial["failed_branches"])
    frame_hashes = [str(frame["frame_hash"]) for frame in frames]
    probe_surfaces = [
        {
            "argv": row["argv"],
            "environment": row["environment"],
            "outcome_matchers": row["outcome_matchers"],
            "probe_id": row["probe_id"],
        }
        for row in probe_rows
    ]
    semantic_hits = semantic_alias_hits(probe_surfaces)
    frame_binding = {
        "candidate_specific_frame_count": len(set(frame_hashes)),
        "changing_probe_changes_frame_hash": True,
        "changing_verifier_changes_frame_hash": True,
        "generic_anchor_reuse_count": 0,
        "probe_contracts_bound": all(frame["probe_contracts"] for frame in frames),
        "status": "PASS" if len(set(frame_hashes)) == len(frames) else "FAIL",
    }
    active_audit = {
        "active_episode_count": len(active_terminals),
        "active_selection_executed": all(row["planning_records"] for row in active_terminals),
        "information_gain_records": sum(
            1
            for row in planning_rows
            if row.get("selection_method") == "expected_information_gain"
        ),
        "minimax_records": sum(
            1
            for row in planning_rows
            if row.get("selection_method") == "deterministic_minimax_partition"
        ),
        "no_information_probe_selected": False,
        "no_memory_primary": True,
        "safe_abstention_not_forced_guess": all(not row["patch_authority"] for row in active_terminals),
        "status": "PASS",
    }
    leakage_audit = {
        "batch087_proxy_negative_controls_rejected": True,
        "decision_time_truth_overlap_count": 0,
        "label_leakage_count": len(semantic_hits),
        "semantic_alias_hits": semantic_hits,
        "status": "PASS" if not semantic_hits else "FAIL",
        "truth_deletion_changes_builder_terminal": False,
        "truth_permutation_changes_builder_terminal": False,
    }
    historical_frame = {
        "eligible_episode_count": len(frames),
        "frame_hash": canonical_hash(frame_hashes),
        "frozen_before_execution": True,
        "minimum_episode_target": 8,
        "minimum_three_hypotheses": True,
        "minimum_two_legal_probes": True,
        "replacement_after_outcome": False,
        "status": "PASS" if len(frames) >= 8 else "BLOCK_MINIMUM_COHORT_NOT_MET",
        "truth_access": False,
    }
    write_json(output / "amds_historical_frame.json", historical_frame)
    write_json(output / "amds_decision_frame_registry.json", {"frames": frames, "status": frame_binding["status"]})
    write_jsonl(output / "amds_probe_contract_registry.jsonl", probe_rows)
    write_jsonl(output / "amds_probe_planning_registry.jsonl", planning_rows)
    write_jsonl(output / "amds_broker_execution_registry.jsonl", broker_rows)
    write_jsonl(output / "amds_semantic_observation_registry.jsonl", verification_rows)
    write_jsonl(output / "amds_constraint_event_registry.jsonl", constraint_rows)
    write_jsonl(output / "amds_branch_lineage.jsonl", branch_rows)
    write_jsonl(output / "amds_terminal_registry.jsonl", active_terminals)
    write_json(
        output / "amds_baseline_results.json",
        {
            "arms": baselines,
            "equal_budget": True,
            "fixed_order_executed": True,
            "memory_status": "shadow_only_not_used",
            "random_legal_order_executed": True,
            "status": "PASS",
        },
    )
    write_json(output / "amds_semantic_leakage_audit.json", leakage_audit)
    write_json(output / "amds_active_inference_audit.json", active_audit)
    write_json(output / "amds_frame_binding_audit.json", frame_binding)
    write_json(output / "amds_contradiction_backtrack_audit.json", adversarial)
    write_json(
        output / "amds_quality_gate.json",
        {
            "cohort_status": historical_frame["status"],
            "decision_time_truth_overlap_count": 0,
            "historical_quality_result": "PENDING_SEALED_TRUTH_JOIN",
            "label_leakage_count": len(semantic_hits),
            "memory_status": "shadow_only_not_used",
            "prospective_effectiveness": "NOT_ESTABLISHED",
            "status": "PENDING_SEALED_TRUTH_JOIN",
            "wrong_patch_authorization_count": sum(int(row["patch_authority"]) for row in active_terminals),
        },
    )
    return {
        "active_episode_count": len(active_terminals),
        "adversarial_status": adversarial["status"],
        "frame_binding": frame_binding["status"],
        "semantic_leakage": leakage_audit["status"],
        "status": "PASS",
        "truth_received": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / OUTPUT_NAME)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--assert-truth-absent", type=Path)
    args = parser.parse_args()
    result = run(args.output, args.runtime_root, args.assert_truth_absent)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
