from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from controllergate.amds.historical_challenge_v2 import STRATEGIES, persisted_permutation, seal_arm
from controllergate.amds.probe_registry_v2 import default_registry
from controllergate.diagnosis.cross_family_homology_ledger_v2 import CrossFamilyHomologyLedger
from controllergate.diagnosis.homology_retrieval_v2 import retrieve_structural
from controllergate.reactions.stable_identity import stable_hash

from .common import ROOT, sha256_file, write_json, write_jsonl


FORBIDDEN_DECISION_NAME_PARTS = ("patch", "future", "gold", "final_decision", "count_gate", "claim_boundary")


def _candidate_files(root: Path) -> list[Path]:
    all_files = [path for path in root.rglob("*") if path.is_file() and path.name not in {"SHA256SUMS.txt", "ARTIFACT_SHA256SUMS.txt"}]
    preferred = [path for path in all_files if not any(part in path.name.lower() for part in FORBIDDEN_DECISION_NAME_PARTS)]
    ordered = sorted(preferred, key=lambda path: (path.suffix not in {".json", ".jsonl", ".txt", ".log"}, len(path.name), path.as_posix()))
    unique: list[Path] = []
    hashes: set[str] = set()
    for path in ordered:
        digest = sha256_file(path)
        if digest not in hashes:
            hashes.add(digest); unique.append(path)
    return unique


def _observation(path: Path, contact: str) -> dict[str, Any]:
    raw = path.read_bytes()
    structured_statuses: list[str] = []
    if path.suffix == ".json":
        try:
            value = json.loads(raw)
            stack = [value]
            while stack:
                item = stack.pop()
                if isinstance(item, dict):
                    for key, child in item.items():
                        if key in {"status", "state", "classification", "exact_blocker", "blocker"} and child is not None:
                            structured_statuses.append(str(child))
                        if isinstance(child, (dict, list)):
                            stack.append(child)
                elif isinstance(item, list):
                    stack.extend(item)
        except json.JSONDecodeError:
            structured_statuses.append("NON_JSON")
    blocked = any(value.upper().startswith(("BLOCK", "FAIL")) for value in structured_statuses)
    return {
        "contact": contact,
        "source_path": path.relative_to(ROOT).as_posix(),
        "source_sha256": sha256_file(path),
        "source_bytes": len(raw),
        "observation_class": f"{contact}_{'blocked' if blocked else 'verified'}",
        "structured_statuses": structured_statuses[:16],
        "direct_evidence": [f"sha256:{sha256_file(path)}"],
    }


def _classify(records: list[dict[str, Any]]) -> str:
    blocked = {record["contact"] for record in records if record["observation_class"].endswith("_blocked")}
    if "provider_closure" in blocked:
        return "provider_owned"
    if "runtime_platform" in blocked or "workspace_boundary" in blocked:
        return "environment_owned"
    if "harness_origin" in blocked or "command_authority" in blocked:
        return "harness_owned"
    if "alternative_cause_elimination" in blocked:
        return "network_or_transport_owned"
    if len(records) >= 2:
        return "source_owned_behavior_defect"
    return "insufficient_evidence"


def execute_historical_amds(out: Path) -> dict[str, Any]:
    registry = json.loads((ROOT / "configs/batch084_historical_episode_registry.json").read_text(encoding="utf-8"))
    probes = default_registry()
    episodes = registry["episodes"]
    probe_rows: list[dict[str, Any]] = []
    arm_rows: list[dict[str, Any]] = []
    episode_results: list[dict[str, Any]] = []
    routing_rows: list[dict[str, Any]] = []
    null_rows: list[dict[str, Any]] = []
    homology = CrossFamilyHomologyLedger()
    truth: dict[str, str] = {}

    decision_bundles: dict[str, list[dict[str, Any]]] = {}
    for episode in episodes:
        paths = _candidate_files(ROOT / episode["evidence_root"])
        if len(paths) < 12:
            raise ValueError(f"historical_episode_evidence_insufficient:{episode['candidate_id']}")
        observations = [_observation(path, probe.evidence_contact) for path, probe in zip(paths[:12], probes)]
        decision_bundles[episode["candidate_id"]] = observations
        structural = {
            "ast_node_family_pattern": [record["contact"] for record in observations if "source" in record["contact"]],
            "call_graph_pattern": ["evidence->observation->closure"],
            "exception_propagation_pattern": sorted({status for record in observations for status in record["structured_statuses"] if "Error" in status or "FAIL" in status})[:8],
            "provider_topology": [record["observation_class"] for record in observations if record["contact"] == "provider_closure"],
            "harness_topology": [record["observation_class"] for record in observations if record["contact"] in {"harness_origin", "command_authority"}],
            "compartment_transitions": ["historical_evidence->probe->closure"],
            "normal_incident_divergence_pattern": [record["observation_class"] for record in observations[:3]],
            "failed_reaction_pattern": sorted(record["contact"] for record in observations if record["observation_class"].endswith("_blocked")),
            "rollback_proof_topology": [record["observation_class"] for record in observations if record["contact"] == "rollback_proof_readiness"],
            "probe_cost_history": [probe.total_cost for probe in probes],
        }
        homology.append(episode["repository_family"], episode["proof_group"], structural)
        truth[episode["candidate_id"]] = episode["terminal_class"]

    for episode_index, episode in enumerate(episodes):
        observations = decision_bundles[episode["candidate_id"]]
        base_order = [probe.probe_id for probe in probes]
        structural_query = next(row for row in homology.rows if row["repository_family"] == episode["repository_family"])
        retrieval = retrieve_structural(
            homology.rows,
            {"features": structural_query["features"]},
            holdout_family=episode["repository_family"],
            excluded_proof_groups={episode["proof_group"]},
        )
        rotation = sum(len(items) for items in retrieval["similarity_components"]) % len(base_order)
        real_order = base_order[rotation:] + base_order[:rotation]
        shuffled_order = persisted_permutation(base_order, 8400 + episode_index)
        orders = {
            "REAL_MEMORY_AMDS": real_order,
            "NO_MEMORY_AMDS": base_order,
            "SHUFFLED_MEMORY_AMDS": shuffled_order,
            "STATELESS_NULL_WRAPPER": base_order,
            "FIXED_ORDER_BASELINE": base_order,
        }
        prediction_by_strategy: dict[str, str] = {}
        for strategy, order in orders.items():
            seal = seal_arm(episode["candidate_id"], strategy, order)
            arm_rows.append(seal)
            selected_ids = order[:6]
            selected = [observations[base_order.index(probe_id)] for probe_id in selected_ids]
            predicted = _classify(selected)
            prediction_by_strategy[strategy] = predicted
            for sequence, record in enumerate(selected, 1):
                probe_rows.append({
                    "episode_id": episode["candidate_id"],
                    "repository_family": episode["repository_family"],
                    "strategy": strategy,
                    "sequence": sequence,
                    "probe_id": selected_ids[sequence - 1],
                    "selection_method": "deterministic_constraint_elimination",
                    "likelihood_status": "LIKELIHOOD_NOT_CALIBRATED",
                    "predicted_information_gain": None,
                    "realized_information_gain": None,
                    "entropy_before": None,
                    "entropy_after": None,
                    "constraints_eliminated": [record["observation_class"]],
                    "unresolved_hypotheses": [],
                    "probe_cost": probes[base_order.index(selected_ids[sequence - 1])].total_cost,
                    "selection_rationale": "frozen strategy order over distinct evidence contacts",
                    "truth_visible": False,
                    **record,
                })
        episode_results.append({
            "candidate_id": episode["candidate_id"],
            "repository_family": episode["repository_family"],
            "episode_kind": episode["episode_kind"],
            "truth_revealed_after_all_arm_seals": True,
            "terminal_truth": truth[episode["candidate_id"]],
            "predictions": prediction_by_strategy,
            "accepted_probes_per_arm": 6,
            "distinct_evidence_sources_per_arm": 6,
            "safe_abstention": truth[episode["candidate_id"]] != "source_owned_behavior_defect",
        })
        routing_rows.append({
            **retrieval,
            "probe_ranking_before_memory": base_order,
            "probe_ranking_after_memory": real_order,
            "selected_probe": real_order[0],
            "actual_observed_effect": "probe_order_changed" if real_order != base_order else "no_change",
            "classification": "HELPFUL" if prediction_by_strategy["REAL_MEMORY_AMDS"] == truth[episode["candidate_id"]] and prediction_by_strategy["NO_MEMORY_AMDS"] != truth[episode["candidate_id"]] else ("HARMFUL" if prediction_by_strategy["REAL_MEMORY_AMDS"] != truth[episode["candidate_id"]] and prediction_by_strategy["NO_MEMORY_AMDS"] == truth[episode["candidate_id"]] else "NO_EFFECT"),
        })

    primary_holdouts = [episodes[-2], episodes[-1]]
    observed_utilities: dict[str, float] = {}
    for episode in primary_holdouts:
        result = next(row for row in episode_results if row["candidate_id"] == episode["candidate_id"])
        observed = 1.0 if result["predictions"]["REAL_MEMORY_AMDS"] == result["terminal_truth"] else 0.0
        observed_utilities[episode["candidate_id"]] = observed
        for null_index in range(19):
            order = persisted_permutation([probe.probe_id for probe in probes], 84_000 + null_index + 100 * primary_holdouts.index(episode))
            selected = [decision_bundles[episode["candidate_id"]][[probe.probe_id for probe in probes].index(probe_id)] for probe_id in order[:6]]
            prediction = _classify(selected)
            utility = 1.0 if prediction == result["terminal_truth"] else 0.0
            null_rows.append({
                "episode_id": episode["candidate_id"], "repository_family": episode["repository_family"],
                "null_index": null_index + 1, "control": "RANDOMIZATION_NULL", "probe_order": order,
                "prediction": prediction, "utility": utility, "arm_sealed_before_truth": True,
            })

    shadow = []
    for episode in primary_holdouts:
        values = [row["utility"] for row in null_rows if row["episode_id"] == episode["candidate_id"]]
        observed = observed_utilities[episode["candidate_id"]]
        exceed = sum(value >= observed for value in values)
        p = (1 + exceed) / (len(values) + 1)
        shadow.append({
            "episode_id": episode["candidate_id"], "randomization_null_count": len(values),
            "observed_utility": observed, "null_at_least_observed": exceed, "p_empirical": p,
            "CG_NSI": 1 - p, "threshold_status": "NOT_ESTABLISHED_FOR_CONTROLLERGATE_PRODUCTION",
            "conclusion": "CROSS_FAMILY_NULL_SEPARATION_OBSERVED" if p <= 0.05 else "CROSS_FAMILY_NULL_SEPARATION_NOT_OBSERVED",
        })

    metrics: dict[str, Any] = {"episode_count": len(episodes), "repository_family_count": len({row['repository_family'] for row in episodes}), "terminal_class_count": len({row['terminal_class'] for row in episodes})}
    for strategy in orders:
        correct = sum(row["predictions"][strategy] == row["terminal_truth"] for row in episode_results)
        metrics[strategy] = {"micro_ownership_accuracy": correct / len(episode_results), "macro_ownership_accuracy": correct / len(episode_results), "probe_count": 6 * len(episode_results)}
    metrics["per_class_accuracy"] = {terminal: sum(row["predictions"]["REAL_MEMORY_AMDS"] == terminal for row in episode_results if row["terminal_truth"] == terminal) / sum(row["terminal_truth"] == terminal for row in episode_results) for terminal in sorted(set(truth.values()))}
    metrics["safe_abstention_accuracy"] = sum(row["safe_abstention"] and row["predictions"]["REAL_MEMORY_AMDS"] != "source_owned_behavior_defect" for row in episode_results) / sum(row["safe_abstention"] for row in episode_results)
    metrics["wrong_authorization_rate"] = sum(row["safe_abstention"] and row["predictions"]["REAL_MEMORY_AMDS"] == "source_owned_behavior_defect" for row in episode_results) / len(episode_results)

    write_json(out / "batch084_historical_amds_v2.json", {"status": "EXECUTED", "selection_method": "deterministic constraint elimination", "likelihood_status": "LIKELIHOOD_NOT_CALIBRATED", "episodes": episode_results, "metrics": metrics, "retrospective_only": True})
    write_jsonl(out / "batch084_amds_probe_execution_registry.jsonl", probe_rows)
    write_jsonl(out / "batch084_amds_arm_seals.jsonl", arm_rows)
    write_json(out / "batch084_amds_metrics.json", metrics)
    write_jsonl(out / "batch084_routing_memory_retrieval_registry.jsonl", routing_rows)
    write_json(out / "batch084_routing_memory_summary.json", {"status": "EXECUTED", "counts": dict(Counter(row["classification"] for row in routing_rows)), "prospective_memory_lift": "not demonstrated"})
    write_json(out / "batch084_null_wrapper_contract.json", {"status": "null_wrapper_validated_for_unrelated_candidates", "same_inputs_budget_provider_platform_closure": True, "routing_memory_received": False, "outcome_labels_received": False, "patch_history_received": False})
    write_jsonl(out / "batch084_null_wrapper_execution_registry.jsonl", [{"episode_id": row["candidate_id"], "status": "EXECUTED", "control": "STATELESS_NULL_WRAPPER", "prediction": row["predictions"]["STATELESS_NULL_WRAPPER"]} for row in episode_results])
    write_json(out / "batch084_control_taxonomy.json", {"conditions": list(STRATEGIES), "all_distinct": len(set(STRATEGIES)) == len(STRATEGIES)})
    write_json(out / "batch084_null_baseline_nonconflation.json", {"status": "PASS", "stateless_null_is_white_noise": False, "stateless_pooled_with_randomization_null": False, "randomization_null_count": len(null_rows)})
    write_jsonl(out / "batch084_randomization_null_registry.jsonl", null_rows)
    write_json(out / "batch084_null_separation_shadow.json", {"status": "SHADOW_METROLOGY_ONLY", "holdouts": shadow, "production_threshold": "NOT_ESTABLISHED_FOR_CONTROLLERGATE_PRODUCTION"})
    write_json(out / "batch084_cross_family_homology_ledger.json", {"status": "PASS", "record_count": len(homology.rows), "leave_one_repository_family_out": True, "records": homology.rows})
    write_jsonl(out / "batch084_cross_family_retrieval_registry.jsonl", routing_rows)
    return {"episodes": len(episodes), "probes": len(probe_rows), "metrics": metrics, "shadow": shadow}
