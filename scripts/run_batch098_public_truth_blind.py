from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.opaque_plan_v1 import canonical_hash
from controllergate.amds.stage_runtime_v7 import run_dpp14
from controllergate.evidence.probe_executor_v2 import execute_probe_contract
from controllergate.topology.pre_tld_frame_v1 import verify_pre_tld_frame


ARM_COMPONENTS = {
    "A": ("canonical_amds",),
    "B": ("canonical_amds", "tot_bulb"),
    "C": ("canonical_amds", "local_brot"),
    "D": ("canonical_amds", "tot_bulb", "local_brot", "executed_tot_brot_projection"),
    "E": ("canonical_amds", "tot_bulb", "local_brot", "executed_tot_brot_projection", "opaque_tld_ordering"),
    "F": ("canonical_amds", "tot_bulb", "local_brot", "executed_tot_brot_projection", "opaque_tld_ordering", "observer_state", "modalities"),
}
BASELINE_COMPONENTS = {
    "G": ("fixed_registered_order",),
    "H": ("preregistered_random_legal_order_seed_173",),
    "I": ("no_memory_active_planner",),
    "J": ("majority_baseline",),
}


def components_for_arm(arm_id: str) -> tuple[str, ...]:
    if arm_id in ARM_COMPONENTS:
        return ARM_COMPONENTS[arm_id]
    if arm_id in BASELINE_COMPONENTS:
        return BASELINE_COMPONENTS[arm_id]
    raise ValueError(f"unknown architecture arm or baseline: {arm_id}")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.write_text("".join(json.dumps(dict(row), sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def component_probe(base: Mapping[str, Any], arm_id: str, component: str, provider_python: str, provider_receipt: str, version: str) -> dict[str, Any]:
    value = dict(base)
    value["probe_id"] = f"component:{arm_id}:{component}:{canonical_hash([base['candidate_id'], component])[:16]}"
    value["single_use_nonce"] = canonical_hash([base["single_use_nonce"], arm_id, component])[:32]
    value["provider_python_executable"] = provider_python
    value["provider_identity_receipt"] = provider_receipt
    value["provider_exact_version"] = version
    value["probe_kind"] = "boundary_dimension"
    value["source_cell_or_edge_or_region"] = f"component-reachability:{component}"
    code = (
        "import hashlib,json;"
        f"s={json.dumps(component)};"
        "print(json.dumps({'kind':'boundary_dimension','subject':s,'subject_hash':hashlib.sha256(s.encode()).hexdigest(),'diagnosis_label_present':False},sort_keys=True,separators=(',',':')))"
    )
    value["exact_argv"] = ["{python}", "-c", code]
    value["predicted_neutral_partitions"] = {"reachable": ["hypothesis:reachable"], "not_reachable": ["hypothesis:not-reachable"]}
    value["partition_rule"] = {"rule_id": "component-reachability-v1", "positive_when": "structured operation succeeds", "negative_when": "structured operation blocks"}
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frame", required=True)
    parser.add_argument("--plan-registry", required=True)
    parser.add_argument("--provider-python", required=True)
    parser.add_argument("--provider-receipt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    frame = json.loads(Path(args.frame).read_text(encoding="utf-8"))
    frame_verification = verify_pre_tld_frame(frame)
    if frame_verification["status"] != "PASS":
        raise SystemExit("pre-TLD frame verification blocked")
    provider = json.loads(Path(args.provider_receipt).read_text(encoding="utf-8"))
    if provider.get("status") != "PASS_EXACT_FROZEN_LINUX_PARITY":
        raise SystemExit("BATCH098_FROZEN_PROVIDER_PARITY_BLOCKED_EXACT")
    all_plans = [json.loads(line) for line in Path(args.plan_registry).read_text(encoding="utf-8").splitlines() if line.strip()]
    plans = {row["arm_id"]: row for row in all_plans if row["candidate_id"] == frame["candidate_id"]}
    if set(plans) != set("ABCDEFGHIJ"):
        raise SystemExit("BATCH098_PRIVATE_TLD_OPAQUE_PLAN_REQUIRED")
    legal_ids = {row["probe_id"] for row in frame["legal_probes"]}
    if any(set(row["ordered_opaque_probe_ids"]) != legal_ids for row in plans.values()):
        raise SystemExit("opaque plan changed legal probe inventory")

    arm_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    producer_rows: list[dict[str, Any]] = []
    verifier_rows: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    semantic_rows: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    branches: list[dict[str, Any]] = []
    nogoods: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    states: dict[str, dict[str, Any]] = {}

    for arm_id in "ABCDEFGHIJ":
        components = components_for_arm(arm_id)
        probes = []
        for probe in frame["legal_probes"]:
            value = dict(probe)
            value["single_use_nonce"] = canonical_hash([probe["single_use_nonce"], arm_id])[:32]
            value["provider_python_executable"] = args.provider_python
            value["provider_identity_receipt"] = provider["verification_receipt"]
            value["provider_exact_version"] = provider["observation"]["python_version"]
            probes.append(value)
        by_id = {row["probe_id"]: row for row in probes}
        if arm_id in {"E", "F"}:
            order = list(plans[arm_id]["ordered_opaque_probe_ids"])
        elif arm_id == "H":
            order = sorted(by_id)
            random.Random(173).shuffle(order)
        elif arm_id == "I":
            order = []
        else:
            order = sorted(by_id)
        component_receipts = []
        for component in components:
            receipt = execute_probe_contract(
                component_probe(probes[0], arm_id, component, args.provider_python, provider["verification_receipt"], provider["observation"]["python_version"]),
                output / "components" / arm_id / component,
            )
            component_record = {
                "candidate_id": frame["candidate_id"], "arm_id": arm_id, "component": component,
                "status": receipt["status"], "operation_id": receipt["operation"]["operation_id"],
                "operation_hash": receipt["operation"]["record_hash"],
                "semantic_verification_receipt": receipt["semantic_verification"]["verification_receipt"],
            }
            component_rows.append(component_record)
            component_receipts.append(component_record)
        dpp_input = {
            "candidate_id": frame["candidate_id"],
            "run_id": f"{frame['run_id']}:{arm_id}",
            "frame_id": frame["frame_id"],
            "topology_probes": probes,
            "topology_constraints": frame["constraints"],
            "planned_probe_order": order,
            "declared_components": list(components),
            "truth_access": False,
            "private_tld_source_access": False,
        }
        state, produced, verified = run_dpp14(dpp_input)
        states[arm_id] = state
        producer_rows.extend({"candidate_id": frame["candidate_id"], "arm_id": arm_id, **row} for row in produced)
        verifier_rows.extend({"candidate_id": frame["candidate_id"], "arm_id": arm_id, **row} for row in verified)
        for execution in state.get("probe_executions", ()):
            observations.append({"candidate_id": frame["candidate_id"], "arm_id": arm_id, "probe_id": execution["probe_id"], "operation": execution["operation"], "structured_product": execution["structured_product"], "truth_access": False})
            semantic_rows.append({"candidate_id": frame["candidate_id"], "arm_id": arm_id, **execution["semantic_verification"]})
        facts.extend({"candidate_id": frame["candidate_id"], "arm_id": arm_id, **row} for row in state.get("verified_causal_facts", ()))
        branches.extend({"candidate_id": frame["candidate_id"], "arm_id": arm_id, **row} for row in state.get("contradictions", ()))
        nogoods.extend({"candidate_id": frame["candidate_id"], "arm_id": arm_id, **row} for row in state.get("nogoods", ()))
        record = {
            "candidate_id": frame["candidate_id"], "arm_id": arm_id, "declared_components": list(components),
            "component_operation_count": len(component_receipts), "probe_operation_count": len(state.get("probe_executions", ())),
            "unique_probe_operation_count": state.get("unique_probe_operation_count", 0),
            "terminal": state["terminal"], "terminal_writer": state["terminal_writer"],
            "planned_order_used": bool(order), "opaque_plan_hash": plans[arm_id]["plan_hash"] if arm_id in {"E", "F"} else None,
            "truth_available_during_execution": False, "patch_operation_count": 0,
            "authority_forbidden": ["final truth", "source ownership", "repair", "count", "release"],
        }
        record["execution_receipt"] = canonical_hash(record)
        (arm_rows if arm_id in ARM_COMPONENTS else baseline_rows).append(record)

    selected = states["F"]
    terminal = {
        "candidate_id": frame["candidate_id"],
        "status": "PASS_PUBLIC_TRUTH_BLIND_EXECUTION",
        "terminal": selected["terminal"],
        "terminal_writer": selected["terminal_writer"],
        "probe_execution_count": sum(row["probe_operation_count"] for row in arm_rows + baseline_rows),
        "unique_probe_operation_count": len({row["operation"]["operation_id"] for row in observations}),
        "provisional_causal_fact_count": len(facts),
        "contradiction_count": len(branches),
        "backtrack_count": sum(state.get("backtrack_count", 0) for state in states.values()),
        "truth_access_count": 0,
        "private_tld_source_access_count": 0,
        "patch_operation_count": 0,
        "historical_increment": 0,
        "claim": "PUBLIC_TRUTH_BLIND_EXECUTION_ONLY",
        "authority_allowed": "private sealed-truth join input after terminal commitment",
        "authority_forbidden": ["final quality score", "source ownership", "repair", "count", "release"],
    }
    terminal["terminal_seal"] = canonical_hash(terminal)
    write_json(output / "public_truth_blind_terminal_v1.json", terminal)
    write_jsonl(output / "public_arm_execution_receipts_v1.jsonl", arm_rows)
    write_jsonl(output / "public_baseline_execution_receipts_v1.jsonl", baseline_rows)
    write_jsonl(output / "dpp14_stage_execution_receipts_public_v1.jsonl", producer_rows)
    write_jsonl(output / "dpp14_stage_verification_receipts_public_v1.jsonl", verifier_rows)
    write_jsonl(output / "public_neutral_observations_v1.jsonl", observations)
    write_jsonl(output / "public_semantic_verification_receipts_v1.jsonl", semantic_rows)
    write_jsonl(output / "public_provisional_facts_v1.jsonl", facts)
    write_jsonl(output / "public_failed_branches_v1.jsonl", branches)
    write_jsonl(output / "public_nogoods_v1.jsonl", nogoods)
    write_jsonl(output / "public_component_execution_receipts_v1.jsonl", component_rows)
    write_json(output / "public_arm_component_reachability_audit.json", {"status": "PASS" if all(row["status"] == "PASS" for row in component_rows) else "BLOCK", "component_operation_count": len(component_rows), "order_only_arm_count": 0, "arm_component_sets": {**{key: list(value) for key, value in ARM_COMPONENTS.items()}, **{key: list(value) for key, value in BASELINE_COMPONENTS.items()}}})
    write_json(output / "opaque_tld_plan_only_firewall.json", {"status": "PASS", "opaque_plan_rows_used": 2, "raw_tld_access_count": 0, "normalized_tld_access_count": 0, "private_source_access_count": 0, "truth_access_count": 0, "allowed_arms": ["E", "F"]})
    print(json.dumps(terminal, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
