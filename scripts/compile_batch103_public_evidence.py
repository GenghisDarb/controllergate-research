"""Compile gain, causal, terminal, and ownership evidence after isolated arm runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def collect_jsonl(root: Path, name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob(name)):
        rows.extend(read_jsonl(path))
    return rows


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _phase_gain(args: argparse.Namespace) -> None:
    executions = collect_jsonl(args.arm_artifacts_root, "reactome_planner_execution_receipts_v1.jsonl")
    selections = collect_jsonl(args.arm_artifacts_root, "reactome_planner_selection_history_v1.jsonl")
    accesses = collect_jsonl(args.arm_artifacts_root, "reactome_planner_outcome_vault_access_v1.jsonl")
    terminals = collect_jsonl(args.arm_artifacts_root, "reactome_planner_truth_blind_terminals_v1.jsonl")
    if len(executions) != 90 or {row["arm"] for row in executions} != set("ABCDEFGHIJ"):
        raise RuntimeError("all 90 isolated arm/program executions are required")
    if any(row["unselected_outcome_access_count"] for row in accesses):
        raise RuntimeError("unselected outcome access detected")
    write_jsonl(args.output_root / "reactome_planner_selection_history_v1.jsonl", selections)
    write_jsonl(args.output_root / "reactome_planner_execution_receipts_v1.jsonl", executions)
    write_jsonl(args.output_root / "reactome_planner_outcome_vault_access_v1.jsonl", accesses)
    write_jsonl(args.output_root / "reactome_planner_truth_blind_terminals_v1.jsonl", terminals)

    by_key = {(row["arm"], row["program_id"]): row for row in executions}
    candidate_gain: dict[str, dict[str, Any]] = {}
    improved_candidates: set[str] = set()
    for row in executions:
        if row["arm"] not in set("BCDEF"):
            continue
        baseline = by_key[("A", row["program_id"])]
        improvements = []
        for metric in (
            "typed_incident_materialized",
            "blocked_cells_reduced",
            "valid_pair_count",
            "complete_factorial_count",
        ):
            if int(row[metric]) > int(baseline[metric]):
                improvements.append(metric)
        if row["time_to_first_sensitivity"] is not None and (
            baseline["time_to_first_sensitivity"] is None
            or row["time_to_first_sensitivity"] < baseline["time_to_first_sensitivity"]
        ):
            improvements.append("time_to_first_sensitivity")
        if row["legal_operations_consumed"] < baseline["legal_operations_consumed"]:
            improvements.append("legal_operations_consumed")
        key = f"{row['candidate_id']}:{row['program_id']}:{row['arm']}"
        candidate_gain[key] = {
            "candidate_id": row["candidate_id"],
            "program_id": row["program_id"],
            "reactome_arm": row["arm"],
            "comparison_arm": "A",
            "improved_metrics": improvements,
            "unsafe_authority_delta": row["unsafe_authority"] - baseline["unsafe_authority"],
            "truth_leakage_delta": row["truth_leakage"] - baseline["truth_leakage"],
            "false_attribution": "PENDING_PRIVATE_TRUTH_JOIN",
        }
        if improvements:
            improved_candidates.add(row["candidate_id"])

    per_arm = {}
    for arm in "ABCDEFGHIJ":
        rows = [row for row in executions if row["arm"] == arm]
        per_arm[arm] = {
            "typed_incident_materialization_rate": sum(row["typed_incident_materialized"] for row in rows) / len(rows),
            "blocked_cell_reduction": sum(row["blocked_cells_reduced"] for row in rows),
            "valid_pair_count": sum(row["valid_pair_count"] for row in rows),
            "complete_factorial_count": sum(row["complete_factorial_count"] for row in rows),
            "legal_operations_consumed": sum(row["legal_operations_consumed"] for row in rows),
            "unnecessary_operations": sum(row["unnecessary_operations"] for row in rows),
            "repeated_failed_branch_count": sum(row["repeated_failed_branch_count"] for row in rows),
            "unsafe_authority": sum(row["unsafe_authority"] for row in rows),
            "truth_leakage": sum(row["truth_leakage"] for row in rows),
            "private_data_leakage": sum(row["private_data_leakage"] for row in rows),
            "false_attribution": "PENDING_PRIVATE_TRUTH_JOIN",
        }
    metrics = {
        "status": "PASS_PUBLIC_TRUTH_BLIND_METRICS",
        "arm_program_execution_count": len(executions),
        "selection_count": len(selections),
        "vault_access_count": len(accesses),
        "outcome_vault_violations": 0,
        "metrics_by_arm": per_arm,
        "gain_by_candidate": candidate_gain,
        "candidates_with_any_preregistered_public_metric_improvement": len(improved_candidates),
        "false_attribution_status": "PENDING_PRIVATE_TRUTH_JOIN",
    }
    metrics["metrics_hash"] = canonical_hash(metrics)
    gate = {
        "R4": "NOT_ESTABLISHED",
        "R5": "NOT_ESTABLISHED",
        "R6": "NOT_RUN",
        "public_metric_improvement_candidate_count": len(improved_candidates),
        "minimum_local_candidate_count": 2,
        "minimum_generalization_candidate_count": 3,
        "exact_blocker": "false attribution and accuracy require the post-artifact private truth join",
        "unsafe_authority": sum(row["unsafe_authority"] for row in executions),
        "truth_leakage": sum(row["truth_leakage"] for row in executions),
        "private_data_leakage": sum(row["private_data_leakage"] for row in executions),
        "prospective_effectiveness": "NOT_ESTABLISHED",
        "memory": "not demonstrated",
    }
    gate["gate_hash"] = canonical_hash(gate)
    write_json(args.output_root / "reactome_planner_gain_metrics_v1.json", metrics)
    write_json(args.output_root / "reactome_planner_gain_gate_v1.json", gate)


def _phase_causal(args: argparse.Namespace) -> None:
    receipts = read_jsonl(args.outcome_root / "batch103_fresh_execution_receipts_v1.jsonl")
    ledger = read_jsonl(args.outcome_root / "batch103_registered_cell_ledger_v1.jsonl")
    programs = read_jsonl(ROOT / "configs/batch102_candidate_counterfactual_programs_v4.jsonl")
    by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in receipts:
        by_cell[row["cell_id"]].append(row)
    accounting = {row["cell_id"]: row for row in ledger}

    pairs = []
    factorials = []
    sensitivity = []
    necessity = []
    sufficiency = []
    interaction = []
    alternatives = []
    ownership = []
    for program in programs:
        incident_id = program["incident_cell"]["cell_id"]
        control_id = program["control_cell"]["cell_id"]
        incident = by_cell.get(incident_id, [])
        control = by_cell.get(control_id, [])
        valid = (
            len(incident) >= 2
            and len(control) >= 2
            and accounting[incident_id]["semantic_reproducibility"]
            and accounting[control_id]["semantic_reproducibility"]
            and all(row["predicate_result"] for row in incident + control)
        )
        pair = {
            "pair_id": f"batch103-pair:{program['program_id']}",
            "program_id": program["program_id"],
            "candidate_id": program["candidate_id"],
            "incident_cell_id": incident_id,
            "control_cell_id": control_id,
            "status": "VALID_PAIR" if valid else "PAIR_NOT_VALID",
            "fresh_execution_receipt_ids": [row["execution_receipt_id"] for row in incident + control],
            "held_invariants_verified": valid,
            "truth_access": 0,
        }
        pair["pair_hash"] = canonical_hash(pair)
        pairs.append(pair)
        required = {
            incident_id,
            control_id,
            *program.get("negative_controls", []),
        }
        complete = len(required) >= 4 and all(
            accounting.get(cell_id, {}).get("status", "").startswith("EXECUTED")
            and accounting.get(cell_id, {}).get("semantic_reproducibility")
            for cell_id in required
        )
        factorials.append(
            {
                "factorial_id": f"batch103-factorial:{program['program_id']}",
                "program_id": program["program_id"],
                "required_cell_ids": sorted(required),
                "complete": complete,
                "truth_access": 0,
            }
        )
        sensitivity.append(
            {
                "receipt_id": f"batch103-sensitivity:{program['program_id']}",
                "program_id": program["program_id"],
                "candidate_id": program["candidate_id"],
                "supported": valid,
                "evidence_level": "DIMENSION_SENSITIVITY_VERIFIED" if valid else "CONTACT_VERIFIED" if incident else "PRESENCE_VERIFIED",
                "pair_id": pair["pair_id"],
                "truth_access": 0,
                "authority_forbidden": ["necessity", "sufficiency", "ownership", "patch", "repair count"],
            }
        )
        necessity.append(
            {
                "receipt_id": f"batch103-necessity:{program['program_id']}",
                "program_id": program["program_id"],
                "supported": False,
                "status": "NOT_ESTABLISHED",
                "exact_blocker": "factor-removal semantics and invariants are not independently complete",
                "fabricated": False,
            }
        )
        sufficiency.append(
            {
                "receipt_id": f"batch103-sufficiency:{program['program_id']}",
                "program_id": program["program_id"],
                "supported": False,
                "status": "NOT_ESTABLISHED",
                "exact_blocker": "factor-introduction semantics and invariants are not independently complete",
                "fabricated": False,
            }
        )
        interaction.append(
            {
                "receipt_id": f"batch103-interaction:{program['program_id']}",
                "program_id": program["program_id"],
                "supported": False,
                "status": "NOT_ESTABLISHED",
                "factorial_complete": complete,
                "exact_blocker": "non-additive estimand is not independently supported",
                "fabricated": False,
            }
        )
        alternatives.append(
            {
                "exclusion_id": f"batch103-alternative:{program['program_id']}",
                "program_id": program["program_id"],
                "supported": False,
                "status": "NOT_ESTABLISHED",
                "unresolved_alternatives": [
                    "source",
                    "provider",
                    "platform",
                    "runner",
                    "fixture",
                    "service",
                    "test expectation",
                    "mixed interaction",
                ],
                "fabricated": False,
            }
        )
        ownership.append(
            {
                "receipt_id": f"batch103-ownership:{program['program_id']}",
                "program_id": program["program_id"],
                "candidate_id": program["candidate_id"],
                "ownership_supported": False,
                "status": "NOT_ESTABLISHED",
                "exact_blocker": "necessity or sufficiency and alternative exclusion are not established",
                "truth_access": 0,
                "patch_operations": 0,
                "fabricated": False,
            }
        )
    write_jsonl(args.output_root / "batch103_pair_validity_receipts_v1.jsonl", pairs)
    write_jsonl(args.output_root / "batch103_factorial_completeness_receipts_v1.jsonl", factorials)
    write_jsonl(args.output_root / "batch103_sensitivity_receipts_v1.jsonl", sensitivity)
    write_jsonl(args.output_root / "batch103_necessity_receipts_v1.jsonl", necessity)
    write_jsonl(args.output_root / "batch103_sufficiency_receipts_v1.jsonl", sufficiency)
    write_jsonl(args.output_root / "batch103_interaction_receipts_v1.jsonl", interaction)
    write_jsonl(args.output_root / "batch103_alternative_exclusion_ledger_v1.jsonl", alternatives)
    write_jsonl(args.output_root / "batch103_ownership_support_receipts_v1.jsonl", ownership)
    summary = {
        "status": "PASS_CONSERVATIVE_CAUSAL_COMPILATION",
        "valid_pair_count": sum(row["status"] == "VALID_PAIR" for row in pairs),
        "complete_factorial_count": sum(row["complete"] for row in factorials),
        "sensitivity_supported_count": sum(row["supported"] for row in sensitivity),
        "necessity_supported_count": 0,
        "sufficiency_supported_count": 0,
        "interaction_supported_count": 0,
        "alternative_exclusion_supported_count": 0,
        "ownership_supported_count": 0,
        "truth_access": 0,
        "patch_operations": 0,
    }
    summary["summary_hash"] = canonical_hash(summary)
    write_json(args.output_root / "batch103_causal_evidence_summary_v1.json", summary)


def _phase_terminal(args: argparse.Namespace) -> None:
    planner = collect_jsonl(args.arm_artifacts_root, "reactome_planner_truth_blind_terminals_v1.jsonl")
    sensitivity = collect_jsonl(args.causal_root, "batch103_sensitivity_receipts_v1.jsonl")
    supported = {row["program_id"] for row in sensitivity if row["supported"]}
    if len(planner) != 90:
        raise RuntimeError("terminal join requires 90 isolated planner terminals")
    terminals = []
    for row in planner:
        terminal = row["terminal"]
        if terminal == "DIMENSION_SENSITIVITY_VERIFIED" and row["program_id"] not in supported:
            terminal = "INSUFFICIENT_EVIDENCE"
        value = {
            "terminal_id": row["terminal_id"].replace("planner-terminal", "controller-audit-terminal"),
            "arm": row["arm"],
            "program_id": row["program_id"],
            "candidate_id": row["candidate_id"],
            "terminal": terminal,
            "evidence_level": row["evidence_level"] if terminal != "INSUFFICIENT_EVIDENCE" else "CONTACT_VERIFIED",
            "planner_terminal_hash": row["terminal_hash"],
            "terminal_writer": "ControllerAudit",
            "ownership_facts": [],
            "truth_access": 0,
            "patch_operations": 0,
            "authority_allowed": "safe truth-blind terminal at independently verified evidence depth",
            "authority_forbidden": ["source ownership", "patch", "repair count", "release"],
        }
        value["terminal_hash"] = canonical_hash(value)
        terminals.append(value)
    write_jsonl(args.output_root / "batch103_controller_audit_terminal_records_v1.jsonl", terminals)
    distribution = Counter(row["terminal"] for row in terminals)
    state = {
        "status": "BLOCKED_EXACT",
        "terminal_count": len(terminals),
        "terminal_distribution": dict(sorted(distribution.items())),
        "positive_ownership_terminal_count": 0,
        "all_terminal_writers_controller_audit": True,
        "exact_blockers": [
            "necessity_not_established",
            "sufficiency_not_established",
            "alternative_exclusion_not_established",
            "ownership_not_established",
            "private_truth_join_pending",
        ],
        "ordinary_patch_count": 0,
        "repair_counts": {"issue_derived": 6, "native_external": 4, "historical": 0},
        "release": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "production_readiness": False,
        "self_maintaining": False,
    }
    state["state_hash"] = canonical_hash(state)
    write_json(args.output_root / "batch103_consolidated_state.json", state)
    write_json(
        args.output_root / "batch103_claim_boundary_v1.json",
        {
            "status": "PASS",
            "R0_R3_structural": True,
            "R4_causal_planning_gain": "NOT_ESTABLISHED_PENDING_PRIVATE_JOIN",
            "R5_generalization": "NOT_ESTABLISHED",
            "R6_prospective": "NOT_RUN",
            "biological_or_physical_proof_claimed": False,
            "ordinary_patches": 0,
            "repair_increment": 0,
            "historical_increment": 0,
        },
    )


def _phase_ownership(args: argparse.Namespace) -> None:
    ownership = collect_jsonl(args.causal_root, "batch103_ownership_support_receipts_v1.jsonl")
    terminals = collect_jsonl(args.terminal_root, "batch103_controller_audit_terminal_records_v1.jsonl")
    supported = [row for row in ownership if row["ownership_supported"]]
    registry = {
        "status": "NOT_ESTABLISHED" if not supported else "LIMITED",
        "proof_count": len(supported),
        "proofs": [],
        "terminal_count": len(terminals),
        "source_ownership_derived_from_truth": False,
        "exact_blocker": "necessity or sufficiency and alternative exclusion are not established",
        "authority_allowed": "reconstruct support only from public verified causal receipts",
        "authority_forbidden": ["truth-derived ownership", "patch", "repair count", "release"],
    }
    registry["registry_hash"] = canonical_hash(registry)
    write_json(args.output_root / "batch103_source_ownership_proof_registry_v1.json", registry)
    write_json(
        args.output_root / "batch103_source_ownership_reconstruction_audit_v1.json",
        {
            "status": "PASS_CONSERVATIVE_RECONSTRUCTION",
            "ownership_receipt_count": len(ownership),
            "supported_ownership_count": len(supported),
            "proof_count": 0,
            "truth_access": 0,
            "fabricated_ownership": 0,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["gain", "causal", "terminal", "ownership"], required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--arm-artifacts-root", type=Path)
    parser.add_argument("--outcome-root", type=Path)
    parser.add_argument("--causal-root", type=Path)
    parser.add_argument("--terminal-root", type=Path)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    {
        "gain": _phase_gain,
        "causal": _phase_causal,
        "terminal": _phase_terminal,
        "ownership": _phase_ownership,
    }[args.phase](args)
    print(json.dumps({"status": "PASS", "phase": args.phase}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
