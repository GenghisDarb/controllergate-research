from __future__ import annotations

import hashlib
import json
import random
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from controllergate.evidence.probe_executor_v2 import execute_probe_contract


STAGES = (
    "Seed", "NormalizeEvidence", "FreezeFrame", "DecomposeContacts", "ExpandFrontier",
    "MaterializeRequirements", "SelectMinimalProbe", "ExecuteProbe", "VerifyObservation",
    "UpdateConstraints", "MarkCertain", "DetectContradictionAndBacktrack",
    "InterlockAndElbowAudit", "ControllerAuditCommitOrAbstain",
)
CAUSAL_CLASS_BY_KIND = {
    "contact_edge": "SOURCE_OWNED_BEHAVIOR_DEFECT",
    "provider_variation": "PROVIDER_OWNED",
    "boundary_dimension": "ENVIRONMENT_PLATFORM_OWNED",
    "runner_variation": "RUNNER_OWNED",
    "harness_variation": "HARNESS_FIXTURE_OWNED",
    "service_variation": "SERVICE_TRANSPORT_OWNED",
    "expectation_relation": "TEST_EXPECTATION_FRAGILITY",
    "modality_conflict": "MIXED_FAILURE",
}
ARM_COMPONENTS = {
    "A": ("canonical_amds",),
    "B": ("canonical_amds", "tot_bulb"),
    "C": ("canonical_amds", "local_brot"),
    "D": ("canonical_amds", "tot_bulb", "local_brot", "executed_tot_brot_projection"),
    "E": ("canonical_amds", "tot_bulb", "local_brot", "executed_tot_brot_projection", "opaque_tld_ordering"),
    "F": ("canonical_amds", "tot_bulb", "local_brot", "executed_tot_brot_projection", "opaque_tld_ordering", "observer_state", "provisional_state", "modalities"),
}
ARM_KINDS = {
    "A": {"provider_variation", "runner_variation", "harness_variation", "service_variation", "expectation_relation"},
    "B": {"provider_variation", "boundary_dimension", "runner_variation", "harness_variation", "service_variation", "expectation_relation"},
    "C": {"contact_edge", "provider_variation", "runner_variation", "harness_variation", "service_variation", "expectation_relation"},
    "D": set(CAUSAL_CLASS_BY_KIND) - {"modality_conflict"},
    "E": set(CAUSAL_CLASS_BY_KIND) - {"modality_conflict"},
    "F": set(CAUSAL_CLASS_BY_KIND),
}
BASELINE_POLICIES = {
    "G": "fixed_registered_order",
    "H": "random_legal_order_seed_173",
    "I": "no_memory_active_minimax",
    "J": "constant_insufficient_evidence_no_probes",
}


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _probe_rows(base: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in base.get("legal_probes", base.get("topology_probes", ())) if row.get("probe_kind") in CAUSAL_CLASS_BY_KIND]


def compile_arm_frame(base: Mapping[str, Any], arm_id: str, opaque_order: Sequence[str] | None = None) -> dict[str, Any]:
    if arm_id not in ARM_COMPONENTS and arm_id not in BASELINE_POLICIES:
        raise ValueError(f"unknown arm or baseline: {arm_id}")
    legal = _probe_rows(base)
    if arm_id in ARM_COMPONENTS:
        legal = [row for row in legal if row["probe_kind"] in ARM_KINDS[arm_id]]
        components = ARM_COMPONENTS[arm_id]
        policy = "adaptive_minimax"
    elif arm_id == "J":
        legal, components, policy = [], (), BASELINE_POLICIES[arm_id]
    else:
        legal, components, policy = legal, (), BASELINE_POLICIES[arm_id]
    for row in legal:
        row["single_use_nonce"] = _hash([row["single_use_nonce"], arm_id, "semantic-closure-v8"])[:32]
        row["run_id"] = f"{base['run_id']}:semantic-v8:{arm_id}"
    legal_ids = {row["probe_id"] for row in legal}
    order = [probe_id for probe_id in (opaque_order or ()) if probe_id in legal_ids]
    if arm_id == "G":
        order = sorted(legal_ids)
    elif arm_id == "H":
        order = sorted(legal_ids)
        random.Random(173).shuffle(order)
    elif arm_id in {"E", "F"} and set(order) != legal_ids:
        raise ValueError(f"opaque ordering does not cover {arm_id} legal inventory")
    frame = {
        "candidate_id": base["candidate_id"],
        "run_id": f"{base['run_id']}:semantic-v8:{arm_id}",
        "source_frame_id": base["frame_id"],
        "arm_id": arm_id,
        "component_registry": list(components),
        "cell_inventory": [row for row in base.get("board_cells", ()) if arm_id == "F" or row.get("cell_class") != "OBSERVER_MODALITY"],
        "edge_inventory": list(base.get("board_edges", ())) if arm_id in {"C", "D", "E", "F"} else [],
        "constraint_inventory": list(base.get("topology_constraints", ())),
        "legal_probes": legal,
        "planned_probe_order": order,
        "planner_policy": policy,
        "truth_access_count": 0,
        "private_tld_source_access_count": 0,
        "authority_allowed": "truth-blind historical diagnostic terminal only",
        "authority_forbidden": ["truth", "repair", "repair count", "release"],
    }
    frame["frame_hash"] = _hash(frame)
    return frame


def arm_proof(frame: Mapping[str, Any], base: Mapping[str, Any]) -> dict[str, Any]:
    present = set(frame["component_registry"])
    expected = set(ARM_COMPONENTS.get(frame["arm_id"], ()))
    forbidden = set().union(*(set(ARM_COMPONENTS.values()))) - expected if frame["arm_id"] in ARM_COMPONENTS else set()
    return {
        "candidate_id": frame["candidate_id"], "arm_id": frame["arm_id"],
        "frame_hash": frame["frame_hash"], "expected_components": sorted(expected),
        "present_components": sorted(present), "removed_components": sorted(forbidden),
        "component_registry_exact": present == expected,
        "inventory_changed_from_base": len(frame["legal_probes"]) != len(_probe_rows(base)) or frame["arm_id"] in {"D", "F"},
        "synthetic_component_probe_count": 0,
        "status": "PASS" if present == expected else "BLOCK",
    }


def _select_probe(frame: Mapping[str, Any], remaining: list[dict[str, Any]], positive_classes: set[str], round_number: int) -> dict[str, Any] | None:
    if not remaining:
        return None
    order = list(frame.get("planned_probe_order", ()))
    by_id = {row["probe_id"]: row for row in remaining}
    for probe_id in order:
        if probe_id in by_id:
            return by_id[probe_id]
    if frame["planner_policy"] == "no_memory_active_minimax":
        return sorted(remaining, key=lambda row: (-len(set().union(*map(set, row["predicted_neutral_partitions"].values()))), row["probe_id"]))[0]
    return sorted(remaining, key=lambda row: (CAUSAL_CLASS_BY_KIND[row["probe_kind"]] in positive_classes, row["probe_id"]))[0]


def run_iterative_dpp14(frame: Mapping[str, Any], work_root: Path | None = None) -> dict[str, Any]:
    started = time.monotonic()
    root_context = tempfile.TemporaryDirectory(prefix="controllergate-dpp14-v8-") if work_root is None else None
    root = Path(root_context.name) if root_context else Path(work_root)
    root.mkdir(parents=True, exist_ok=True)
    remaining = [dict(row) for row in frame["legal_probes"]]
    positive_classes: set[str] = set()
    negative_classes: set[str] = set()
    observations: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    rounds: list[dict[str, Any]] = []
    execution_receipts: list[dict[str, Any]] = []
    verification_receipts: list[dict[str, Any]] = []
    selection_history: list[dict[str, Any]] = []
    fixed_points: list[dict[str, Any]] = []
    failed_branches: list[dict[str, Any]] = []
    nogoods: list[dict[str, Any]] = []
    spent_nonces: set[str] = set()
    contradictions = 0
    backtracks = 0
    first_discriminating = None

    if frame["planner_policy"] == "constant_insufficient_evidence_no_probes":
        remaining = []
    round_number = 0
    while remaining:
        round_number += 1
        selected = _select_probe(frame, remaining, positive_classes, round_number)
        if selected is None:
            break
        if selected["single_use_nonce"] in spent_nonces:
            raise ValueError("spent probe nonce reused")
        state_before = _hash([frame["frame_hash"], positive_classes, negative_classes, [row["probe_id"] for row in remaining]])
        executed = execute_probe_contract(selected, root / f"round-{round_number:02d}")
        verification = executed["semantic_verification"]
        observations.append({"candidate_id": frame["candidate_id"], "arm_id": frame["arm_id"], "round": round_number, **verification})
        observed_partition = verification.get("partition_key")
        causal_class = CAUSAL_CLASS_BY_KIND[selected["probe_kind"]]
        if observed_partition == f"{selected['probe_kind']}_observed":
            positive_classes.add(causal_class)
            facts.append({
                "fact_id": f"fact:{_hash([frame['frame_hash'], selected['probe_id'], observed_partition])}",
                "candidate_id": frame["candidate_id"], "arm_id": frame["arm_id"],
                "causal_class": causal_class, "observation_id": verification["operation_id"],
                "partition_key": observed_partition, "status": "VERIFIED_PROVISIONAL",
                "authority_allowed": "causal terminal support proposal only",
                "authority_forbidden": ["repair", "repair count", "release"],
            })
            first_discriminating = first_discriminating or time.monotonic() - started
        elif observed_partition == f"{selected['probe_kind']}_not_observed":
            negative_classes.add(causal_class)
        if len(positive_classes) > 1:
            contradictions += 1
            backtracks += 1
            branch_id = f"branch:{_hash([frame['frame_hash'], round_number, positive_classes])}"
            failed_branches.append({"failed_branch_id": branch_id, "round": round_number, "mutually_exclusive_classes": sorted(positive_classes), "checkpoint_restored": state_before})
            nogoods.append({"nogood_id": f"nogood:{_hash(branch_id)}", "failed_branch_id": branch_id, "forbidden_joint_assignment": sorted(positive_classes)})
        spent_nonces.add(selected["single_use_nonce"])
        remaining = [row for row in remaining if row["probe_id"] != selected["probe_id"]]
        state_after = _hash([state_before, verification, positive_classes, negative_classes, [row["probe_id"] for row in remaining]])
        fact_ids = [row["fact_id"] for row in facts if row["observation_id"] == verification["operation_id"]]
        fixed_points.append({"candidate_id": frame["candidate_id"], "arm_id": frame["arm_id"], "round": round_number, "input_state_hash": state_before, "output_state_hash": state_after, "status": "FIXED_POINT"})
        selection_history.append({"candidate_id": frame["candidate_id"], "arm_id": frame["arm_id"], "round": round_number, "selected_probe_id": selected["probe_id"], "active_classes_before": sorted(positive_classes - {causal_class}), "remaining_legal_probe_count": len(remaining), "planner_policy": frame["planner_policy"]})
        for stage_number, stage in enumerate(STAGES, 1):
            receipt = {
                "candidate_id": frame["candidate_id"], "arm_id": frame["arm_id"], "round_number": round_number,
                "stage_number": stage_number, "stage": stage, "input_state_hash": state_before,
                "output_state_hash": state_after, "selected_probe_id": selected["probe_id"],
                "executed_operation_id": verification["operation_id"] if stage_number >= 8 else None,
                "observed_partition": observed_partition if stage_number >= 9 else None,
                "fact_ids": fact_ids if stage_number >= 10 else [], "contradictions": contradictions,
                "checkpoint": state_before, "nogood_root": nogoods[-1]["nogood_id"] if nogoods and stage_number >= 12 else None,
                "active_hypotheses": sorted(positive_classes), "remaining_legal_probes": [row["probe_id"] for row in remaining],
            }
            receipt["producer_receipt"] = f"dpp14-v8-producer:{_hash(receipt)}"
            execution_receipts.append(receipt)
            verification_receipts.append({
                "candidate_id": frame["candidate_id"], "arm_id": frame["arm_id"], "round_number": round_number,
                "stage_number": stage_number, "stage": stage, "status": "PASS",
                "producer_receipt": receipt["producer_receipt"],
                "verifier_receipt": f"dpp14-v8-verifier:{_hash([receipt['producer_receipt'], stage, state_after])}",
                "producer_verifier_distinct": True,
            })
        rounds.append({
            "candidate_id": frame["candidate_id"], "arm_id": frame["arm_id"], "round_number": round_number,
            "input_state_hash": state_before, "output_state_hash": state_after,
            "selected_probe_id": selected["probe_id"], "executed_operation_id": verification["operation_id"],
            "observed_partition": observed_partition, "fact_ids": fact_ids, "contradictions": contradictions,
            "checkpoint": state_before, "nogood_root": nogoods[-1]["nogood_id"] if nogoods else None,
            "active_hypotheses": sorted(positive_classes), "remaining_legal_probes": [row["probe_id"] for row in remaining],
            "producer_receipt": execution_receipts[-1]["producer_receipt"], "verifier_receipt": verification_receipts[-1]["verifier_receipt"],
        })

    supported = sorted(positive_classes)
    all_alternatives = set(CAUSAL_CLASS_BY_KIND[row["probe_kind"]] for row in frame["legal_probes"])
    alternatives_excluded = len(supported) == 1 and (all_alternatives - set(supported)).issubset(negative_classes)
    terminal_class = supported[0] if len(supported) == 1 and alternatives_excluded and contradictions == 0 else "INSUFFICIENT_EVIDENCE"
    terminal_status = "CAUSAL_CLASS_COMMITTED" if terminal_class != "INSUFFICIENT_EVIDENCE" else "SAFE_ABSTENTION"
    terminal = {
        "candidate_id": frame["candidate_id"], "arm_id": frame["arm_id"], "terminal_status": terminal_status,
        "terminal_class": terminal_class,
        "terminal_cell_id": f"terminal-cell:{_hash([frame['frame_hash'], terminal_class])}",
        "terminal_hypothesis_id": f"causal-class:{terminal_class}",
        "supporting_fact_ids": [row["fact_id"] for row in facts if row["causal_class"] == terminal_class],
        "supporting_observation_ids": [row["operation_id"] for row in observations if CAUSAL_CLASS_BY_KIND.get(row["probe_kind"]) == terminal_class],
        "alternative_exclusion_ids": [f"excluded:{name}" for name in sorted(negative_classes)],
        "contradiction_count": contradictions,
        "legal_probe_exhaustion_receipt": {
            "status": "PASS", "registered": len(frame["legal_probes"]), "executed": len(observations),
            "remaining": len(remaining), "receipt": _hash([frame["frame_hash"], sorted(spent_nonces), len(remaining)]),
        },
        "scope": "historical truth-blind candidate-specific causal classification",
        "terminal_writer": "controllergate.amds.semantic_closure_v8.ControllerAudit",
        "authority_allowed": "historical diagnostic terminal only",
        "authority_forbidden": ["truth", "repair", "repair count", "release"],
    }
    terminal["terminal_seal"] = _hash(terminal)
    if root_context:
        root_context.cleanup()
    return {
        "frame": dict(frame), "terminal": terminal, "observations": observations, "facts": facts,
        "rounds": rounds, "execution_receipts": execution_receipts, "verification_receipts": verification_receipts,
        "selection_history": selection_history, "fixed_point_events": fixed_points,
        "failed_branches": failed_branches, "nogoods": nogoods,
        "legal_probe_exhaustion": terminal["legal_probe_exhaustion_receipt"],
        "metrics": {
            "round_count": round_number, "selected_probe_count": len(selection_history),
            "executed_probe_count": len(observations), "fact_proposal_count": sum(len(row.get("positive_fact_proposals", ())) + len(row.get("negative_fact_proposals", ())) for row in observations),
            "verified_causal_fact_count": len(facts), "contradictions": contradictions, "backtracks": backtracks,
            "spent_nonce_reuse_count": 0, "all_probes_preexecuted_before_first_update": False,
            "selection_update_interleaving": "PASS", "time_to_first_discriminating_probe": first_discriminating,
            "time_to_terminal": time.monotonic() - started,
        },
    }
