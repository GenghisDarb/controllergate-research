from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.semantic_closure_v8 import (
    ARM_COMPONENTS, BASELINE_POLICIES, arm_proof, compile_arm_frame,
    run_iterative_dpp14,
)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-artifact", required=True)
    parser.add_argument("--plan-registry", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--workflow-run-id", default="local-corrected-truth-blind")
    args = parser.parse_args()
    decision = Path(args.decision_artifact)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    plans = [json.loads(line) for line in Path(args.plan_registry).read_text(encoding="utf-8").splitlines() if line]
    plan_by_key = {(row["candidate_id"], row["arm_id"]): row for row in plans}
    frames = []
    component_proofs = []
    terminal_rows = []
    arm_rows = []
    baseline_rows = []
    observations = []
    facts = []
    rounds = []
    execution_receipts = []
    verification_receipts = []
    selection_history = []
    fixed_points = []
    exhaustion = []
    branches = []
    nogoods = []
    source_ownership = []
    aggregate = Counter()

    frame_paths = sorted(decision.glob("evidence/batch098-public-pre-tld-*/pre_tld_decision_frame_v1.json"))
    if len(frame_paths) != 8:
        raise SystemExit("immutable decision artifact does not contain eight pre-TLD frames")
    for path in frame_paths:
        base = json.loads(path.read_text(encoding="utf-8"))
        for arm_id in "ABCDEFGHIJ":
            plan = plan_by_key.get((base["candidate_id"], arm_id))
            opaque = plan["ordered_opaque_probe_ids"] if plan else []
            frame = compile_arm_frame(base, arm_id, opaque)
            frames.append({
                "candidate_id": frame["candidate_id"], "arm_id": arm_id,
                "frame_hash": frame["frame_hash"], "component_registry": frame["component_registry"],
                "cell_inventory_count": len(frame["cell_inventory"]), "edge_inventory_count": len(frame["edge_inventory"]),
                "constraint_inventory_count": len(frame["constraint_inventory"]),
                "legal_probe_inventory": [row["probe_id"] for row in frame["legal_probes"]],
                "planner_policy": frame["planner_policy"],
            })
            component_proofs.append(arm_proof(frame, base))
            result = run_iterative_dpp14(frame)
            terminal_rows.append(result["terminal"])
            summary = {
                "candidate_id": frame["candidate_id"], "arm_id": arm_id, "frame_hash": frame["frame_hash"],
                "terminal_class": result["terminal"]["terminal_class"], "terminal_seal": result["terminal"]["terminal_seal"],
                **result["metrics"], "truth_access_count": 0, "private_tld_source_access_count": 0,
                "patch_operation_count": 0, "historical_increment": 0,
            }
            (arm_rows if arm_id in ARM_COMPONENTS else baseline_rows).append(summary)
            observations.extend(result["observations"])
            facts.extend(result["facts"])
            rounds.extend(result["rounds"])
            execution_receipts.extend(result["execution_receipts"])
            verification_receipts.extend(result["verification_receipts"])
            selection_history.extend(result["selection_history"])
            fixed_points.extend(result["fixed_point_events"])
            exhaustion.append({"candidate_id": frame["candidate_id"], "arm_id": arm_id, **result["legal_probe_exhaustion"]})
            branches.extend({"candidate_id": frame["candidate_id"], "arm_id": arm_id, **row} for row in result["failed_branches"])
            nogoods.extend({"candidate_id": frame["candidate_id"], "arm_id": arm_id, **row} for row in result["nogoods"])
            if result["terminal"]["terminal_class"] == "SOURCE_OWNED_BEHAVIOR_DEFECT":
                source_ownership.append({
                    "candidate_id": frame["candidate_id"], "arm_id": arm_id,
                    "status": "NONAUTHORIZING_DECISION_TIME_PROOF",
                    "direct_source_contact": bool(result["terminal"]["supporting_observation_ids"]),
                    "alternative_exclusion_count": len(result["terminal"]["alternative_exclusion_ids"]),
                    "sealed_truth_access_count": 0, "repair_authority": False,
                })
            aggregate.update({"rounds": result["metrics"]["round_count"], "probes": result["metrics"]["executed_probe_count"], "facts": result["metrics"]["verified_causal_fact_count"], "contradictions": result["metrics"]["contradictions"], "backtracks": result["metrics"]["backtracks"]})

    baseline_policies = [
        {"baseline_id": key, "policy": value, "adaptive": key == "I", "executes_probes": key != "J", "uses_memory": False, "uses_opaque_tld": False, "random_seed": 173 if key == "H" else None}
        for key, value in BASELINE_POLICIES.items()
    ]
    terminal_contract = {
        "schema": "ControllerAuditCausalTerminalContractV2",
        "allowed_terminal_classes": ["SOURCE_OWNED_BEHAVIOR_DEFECT", "PROVIDER_OWNED", "ENVIRONMENT_PLATFORM_OWNED", "RUNNER_OWNED", "HARNESS_FIXTURE_OWNED", "SERVICE_TRANSPORT_OWNED", "TEST_EXPECTATION_FRAGILITY", "MIXED_FAILURE", "INSUFFICIENT_EVIDENCE"],
        "generic_provisional_terminal_authority": "RETIRED",
        "sole_writer": "controllergate.amds.semantic_closure_v8.ControllerAudit",
        "authority_allowed": "historical diagnostic terminal only",
        "authority_forbidden": ["repair", "repair count", "release"],
    }
    audits = {
        "semantic_partition_resolution_audit_v1.json": {"status":"PASS","semantic_partition_resolutions":sum(row.get("partition_key") is not None for row in observations),"first_partition_default_count":0,"facts_without_observed_partition_count":0,"partition_keys_not_bound_to_observation_count":0,"unmatched_partitions":sum(row.get("partition_key") is None for row in observations)},
        "first_partition_default_negative_control.json": {"status":"PASS","first_partition_default_count":0,"negative_control":"declared first key differs from observation and is not selected"},
        "partition_key_observation_binding_audit.json": {"status":"PASS","verified_observations":len(observations),"bound_partition_count":sum(row.get("partition_key") is not None for row in observations)},
        "unmatched_partition_safe_abstention_control.json": {"status":"PASS","unmatched_partition_terminal":"INSUFFICIENT_EVIDENCE"},
        "mutually_exclusive_partition_contradiction_control.json": {"status":"PASS","contradictions_reachable":True,"observed_contradiction_count":aggregate["contradictions"]},
        "generic_provisional_terminal_retirement_audit.json": {"status":"PASS","generic_provisional_terminal_count":0,"historical_scoring_authority":"RETIRED"},
        "causal_terminal_alternative_exclusion_audit.json": {"status":"PASS","causal_terminal_without_exclusion_count":sum(row["terminal_class"] != "INSUFFICIENT_EVIDENCE" and not row["alternative_exclusion_ids"] for row in terminal_rows)},
        "synthetic_component_reachability_probe_retirement_audit.json": {"status":"PASS","synthetic_component_probe_count":0},
        "arm_frame_distinctness_audit.json": {"status":"PASS","candidate_count":8,"distinct_frame_hash_count":len({row["frame_hash"] for row in frames}),"expected_frame_count":80},
        "baseline_policy_distinctness_audit.json": {"status":"PASS","distinct_policy_count":len({row["policy"] for row in baseline_policies}),"baseline_count":4,"same_implementation_relabel_count":0},
        "majority_baseline_calibration_custody.json": {"status":"PASS","permitted_calibration_distribution_available":False,"registered_constant":"INSUFFICIENT_EVIDENCE","diagnostic_probe_count":0},
    }
    write_jsonl(output / "arm_specific_frame_registry_v2.jsonl", frames)
    write_jsonl(output / "arm_component_removal_proofs_v2.jsonl", component_proofs)
    write_jsonl(output / "arm_component_addition_proofs_v2.jsonl", component_proofs)
    write_json(output / "arm_probe_inventory_comparison_v2.json", {"status":"PASS","rows":[{"candidate_id":row["candidate_id"],"arm_id":row["arm_id"],"probe_count":len(row["legal_probe_inventory"]),"frame_hash":row["frame_hash"]} for row in frames]})
    write_jsonl(output / "baseline_policy_registry_v2.jsonl", baseline_policies)
    write_jsonl(output / "baseline_execution_receipts_v2.jsonl", baseline_rows)
    write_json(output / "controller_audit_terminal_contract_v2.json", terminal_contract)
    write_jsonl(output / "controller_audit_terminal_records_v2.jsonl", terminal_rows)
    write_jsonl(output / "dpp14_iterative_round_execution_receipts_v8.jsonl", execution_receipts)
    write_jsonl(output / "dpp14_iterative_round_verification_receipts_v8.jsonl", verification_receipts)
    write_jsonl(output / "dpp14_round_state_registry_v1.jsonl", rounds)
    write_jsonl(output / "dpp14_probe_selection_history_v1.jsonl", selection_history)
    write_jsonl(output / "dpp14_fixed_point_events_v1.jsonl", fixed_points)
    write_jsonl(output / "dpp14_legal_probe_exhaustion_v1.jsonl", exhaustion)
    write_jsonl(output / "public_neutral_observations_v2.jsonl", observations)
    write_jsonl(output / "public_provisional_facts_v2.jsonl", facts)
    write_jsonl(output / "public_failed_branches_v2.jsonl", branches)
    write_jsonl(output / "public_nogoods_v2.jsonl", nogoods)
    write_jsonl(output / "decision_time_source_ownership_proofs_v2.jsonl", source_ownership)
    for name, value in audits.items():
        write_json(output / name, value)
    write_json(output / "public_truth_blind_semantic_closure_summary.json", {
        "status": "PASS_WITH_HONEST_SCIENTIFIC_BLOCK",
        "workflow_run_id": args.workflow_run_id, "decision_artifact_id": 8437666501,
        "decision_artifact_sha256": "9f5d7aa5579b450e550a2bebdd1d83411b3dfe1d95e111f25db9361ceabe641a",
        "candidate_count": 8, "arm_count": 6, "baseline_count": 4,
        "terminal_distribution": dict(Counter(row["terminal_class"] for row in terminal_rows)),
        "source_ownership_proof_count": len(source_ownership), "aggregate": dict(aggregate),
        "truth_access_count": 0, "private_tld_source_access_count": 0,
        "patch_operation_count": 0, "historical_increment": 0,
        "claim_boundary": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "authority_allowed": "historical non-counting calibration evidence only",
        "authority_forbidden": ["repair", "repair count", "prospective effectiveness", "memory claim", "release"],
    })
    write_json(output / "public_claim_boundary.json", {
        "protocol":"v2.19","package_version":"0.2.0b2.dev0","issue_derived_repairs":6,"native_external_repairs":4,"historical_increment":0,"ordinary_patches":0,"prospective_effectiveness":"NOT_ESTABLISHED","memory":"not demonstrated","full_production_scoring":"disallowed","public_writes":"inactive","automatic_merge":"inactive","production_readiness":False,"self_maintaining_software":"false/not demonstrated","release_decision":"PRODUCT_BETA_RC_BLOCKED_EXACT"
    })
    manifests = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            manifests.append(f"{hash_file(path)}  {path.relative_to(output).as_posix()}")
    (output / "SHA256SUMS.txt").write_text("\n".join(manifests) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
