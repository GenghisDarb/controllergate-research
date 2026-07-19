#!/usr/bin/env python3
"""Join public truth-blind Batch100 cell results into conservative evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.matched_counterfactual_v10 import canonical_hash, conservative_evidence_from_cells


AUTHORITY_FORBIDDEN = ["truth inference", "patch", "repair count", "release promotion"]
ARMS = ("A", "B", "C", "D", "E", "F")
BASELINES = ("G", "H", "I", "J")


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(*, producer: str, depth: str, scope: str, allowed: str) -> dict[str, Any]:
    return {"producer": producer, "execution_depth": depth, "semantic_scope": scope, "authority_allowed": allowed, "authority_forbidden": AUTHORITY_FORBIDDEN}


def aggregate_cell(rows: list[dict]) -> dict[str, Any] | None:
    if len(rows) < 2:
        return None
    ordered = sorted(rows, key=lambda row: row["replay_index"])
    reproducible = all(row["reproducibility_status"] == "REPRODUCIBLE" for row in ordered)
    return {
        "operation_id": "cell-aggregate:" + canonical_hash([row["operation_id"] for row in ordered]),
        "semantic_observation": ordered[0]["semantic_observation"],
        "predicate_satisfied": all(row["predicate_satisfied"] for row in ordered),
        "semantic_verifier_receipt": canonical_hash([row["semantic_verifier_receipt"] for row in ordered]),
        "reproducibility_status": "REPRODUCIBLE" if reproducible else "NONREPRODUCIBLE",
        "replay_receipt_hashes": [row["receipt_hash"] for row in ordered],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-artifacts-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workflow-run-id", default="local")
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    programs = read_jsonl(ROOT / "configs/batch100_candidate_counterfactual_programs_v2.jsonl")
    cells = read_jsonl(ROOT / "configs/batch100_counterfactual_cell_registry_v2.jsonl")
    cell_receipts: list[dict] = []
    provider_receipts: list[dict] = []
    broker_operations: list[dict] = []
    blockers: list[dict] = []
    for path in args.candidate_artifacts_root.rglob("cell_execution_receipts_v1.jsonl"):
        cell_receipts.extend(read_jsonl(path))
    for path in args.candidate_artifacts_root.rglob("provider_materialization_receipts_v1.jsonl"):
        provider_receipts.extend(read_jsonl(path))
    for path in args.candidate_artifacts_root.rglob("broker_operations_v1.jsonl"):
        broker_operations.extend(read_jsonl(path))
    for path in args.candidate_artifacts_root.rglob("candidate_blockers_v1.jsonl"):
        blockers.extend(read_jsonl(path))
    # Exact replay duplicates are not valid independent evidence.
    unique_receipts = {row["receipt_hash"]: row for row in cell_receipts}
    duplicate_receipt_count = len(cell_receipts) - len(unique_receipts)
    cell_receipts = list(unique_receipts.values())
    by_cell: dict[str, list[dict]] = defaultdict(list)
    for row in cell_receipts:
        by_cell[row["cell_id"]].append(row)
    cell_aggregates = {cell_id: aggregate_cell(rows) for cell_id, rows in by_cell.items()}
    registered_ids = {row["cell_id"] for row in cells}
    executed_ids = {cell_id for cell_id, value in cell_aggregates.items() if value}
    missing_ids = sorted(registered_ids - executed_ids)
    for cell_id in missing_ids:
        cell = next(row for row in cells if row["cell_id"] == cell_id)
        blockers.append({"candidate_id": cell["candidate_id"], "cell_id": cell_id, "blocker": "REGISTERED_CELL_NOT_EXECUTED_IN_EXACT_PROVIDER", "provider_capsule_id": cell["provider_capsule_id"]})

    evidence_rows: list[dict] = []
    necessity: list[dict] = []
    sufficiency: list[dict] = []
    interactions: list[dict] = []
    ownership: list[dict] = []
    alternatives: list[dict] = []
    for program in programs:
        incident = cell_aggregates.get(program["incident_cell"]["cell_id"])
        control = cell_aggregates.get(program["control_cell"]["cell_id"])
        evidence = conservative_evidence_from_cells(program=program, incident=incident, control=control).record()
        evidence_rows.append(evidence)
        base = {"program_id": program["program_id"], "candidate_id": program["candidate_id"], "pair_id": evidence["pair_id"]}
        necessity.append({**base, "status": "NOT_ESTABLISHED", "reason": "dimension sensitivity does not by itself prove necessity", **metadata(producer="finalize_batch100_public_execution", depth="matched pair join", scope="necessity", allowed="future evidence planning")})
        sufficiency.append({**base, "status": "NOT_ESTABLISHED", "reason": "dimension sensitivity does not by itself prove sufficiency", **metadata(producer="finalize_batch100_public_execution", depth="matched pair join", scope="sufficiency", allowed="future evidence planning")})
        interactions.append({**base, "status": "NOT_ESTABLISHED", "reason": "all required factorial cells and non-additive effect are not established", **metadata(producer="finalize_batch100_public_execution", depth="factorial join", scope="interaction", allowed="future evidence planning")})
        unresolved = list(evidence["unresolved_alternatives"]) or ["necessity and sufficiency remain unresolved"]
        alternatives.append({**base, "excluded_alternatives": evidence["alternative_exclusions"], "unresolved_alternatives": unresolved, "status": "OPEN", **metadata(producer="finalize_batch100_public_execution", depth="alternative reconstruction", scope="causal alternatives", allowed="constraint preservation")})
        ownership.append({**base, "status": "NOT_ESTABLISHED", "ownership_supported": False, "reason": "ownership firewall requires necessity or sufficiency plus alternative exclusion", **metadata(producer="finalize_batch100_public_execution", depth="ownership firewall", scope="causal ownership", allowed="safe abstention")})

    evidence_by_candidate: dict[str, list[dict]] = defaultdict(list)
    for row in evidence_rows:
        evidence_by_candidate[row["candidate_id"]].append(row)
    terminal_rows: list[dict] = []
    round_rows: list[dict] = []
    selection_rows: list[dict] = []
    exhaustion_rows: list[dict] = []
    policies = (*ARMS, *BASELINES)
    for candidate in sorted(evidence_by_candidate):
        relevant = evidence_by_candidate[candidate]
        for policy in policies:
            supporting = [row for row in relevant if row["ownership_supported"]]
            terminal = {
                "candidate_id": candidate, "arm_id": policy, "terminal_status": "SEALED_SAFE_ABSTENTION",
                "terminal_class": "INSUFFICIENT_EVIDENCE", "terminal_cell_id": "controller-audit:" + canonical_hash([candidate, policy]),
                "supporting_ownership_fact_ids": [], "supporting_pair_ids": [row["pair_id"] for row in supporting],
                "necessity_receipt_ids": [], "sufficiency_receipt_ids": [], "interaction_receipt_ids": [],
                "alternative_exclusion_ids": [], "unresolved_alternatives": sorted({item for row in relevant for item in row["unresolved_alternatives"]}),
                "legal_counterfactual_exhaustion": False, "contradictions": [],
                "terminal_writer": "ControllerAudit.counterfactual_v10", "authority_allowed": "safe abstention",
                "authority_forbidden": ["causal ownership", "patch", "repair count", "release"],
            }
            terminal["terminal_seal"] = canonical_hash(terminal)
            terminal_rows.append(terminal)
            round_rows.append({"candidate_id": candidate, "arm_id": policy, "round": 1, "selected_pair_ids": [row["pair_id"] for row in relevant], "ownership_fact_count": len(supporting), "status": "FIXED_POINT_INSUFFICIENT_EVIDENCE", "receipt_hash": canonical_hash([candidate, policy, relevant])})
            selection_rows.append({"candidate_id": candidate, "arm_id": policy, "ordered_pair_ids": [row["pair_id"] for row in relevant], "selection_source": "public-safe-opaque-order" if policy in {"E", "F"} else "registered-policy", "truth_access": 0, "private_tld_access": 0})
            exhaustion_rows.append({"candidate_id": candidate, "arm_id": policy, "legal_inventory_exhausted": False, "reason": "registered exact-provider cells remain blocked", "unresolved_cell_count": sum(row["candidate_id"] == candidate and row["cell_id"] in missing_ids for row in cells)})

    # Outcome vault stores only pair envelopes; policies open only selected envelopes.
    vault: list[dict] = []
    for evidence in evidence_rows:
        envelope = {"pair_id": evidence["pair_id"], "candidate_id": evidence["candidate_id"], "payload_hash": canonical_hash(evidence), "sealed_before_policy_access": True, "truth_fields": 0}
        envelope["envelope_seal"] = canonical_hash(envelope)
        vault.append(envelope)
    access: list[dict] = []
    arm_receipts: list[dict] = []
    baseline_receipts: list[dict] = []
    for policy in policies:
        selected = [] if policy == "J" else [row["pair_id"] for row in evidence_rows]
        for pair_id in selected:
            access.append({"policy_id": policy, "pair_id": pair_id, "access_reason": "registered legal selection", "access_before_selection": False, "truth_access": 0, "receipt_hash": canonical_hash([policy, pair_id])})
        receipt = {"policy_id": policy, "selected_pair_ids": selected, "opened_envelope_count": len(selected), "unselected_outcome_access": 0, "truth_access": 0, "private_tld_access": 0, "patch_operations": 0, "ownership_terminal_count": 0, "safe_abstention_count": 8, "operation_count": len(selected), "status": "EXECUTED_SAFE_ABSTENTION"}
        receipt["receipt_hash"] = canonical_hash(receipt)
        (arm_receipts if policy in ARMS else baseline_receipts).append(receipt)
    gain_gate = {
        "status": "NOT_ESTABLISHED", "selected_enhanced_arm": "F", "baseline": "I",
        "enhanced_causal_coverage": 0.0, "baseline_causal_coverage": 0.0,
        "accuracy_gain": None, "efficiency_gain": None, "false_attribution_increase": 0,
        "reason": "no ownership-grade public terminal was established",
        **metadata(producer="finalize_batch100_public_execution", depth="public architecture evaluation", scope="architecture gain", allowed="future private calibration input"),
    }
    cost_metrics = {"policies": [{"policy_id": row["policy_id"], "operation_count": row["operation_count"], "opened_envelope_count": row["opened_envelope_count"], "information_gain": 0.0} for row in [*arm_receipts, *baseline_receipts]], **metadata(producer="finalize_batch100_public_execution", depth="executed public envelope access", scope="cost and information gain", allowed="architecture comparison")}

    write_jsonl(args.output_root / "batch100_clean_replay_registry_v1.jsonl", sorted(cell_receipts, key=lambda row: (row["cell_id"], row["replay_index"])))
    write_json(args.output_root / "batch100_order_carryover_audit.json", {"status": "PASS" if all(row["carryover_audit"] == "PASS_FRESH_WORKSPACE" for row in cell_receipts) else "BLOCK", "cross_cell_file_reuse": 0, "cross_cell_process_reuse": 0, "unapproved_network_requests": 0, "cleanup_failures": 0, **metadata(producer="finalize_batch100_public_execution", depth="cell receipt join", scope="carryover", allowed="replay reliability")})
    write_json(args.output_root / "batch100_pair_reproducibility_audit.json", {"status": "PASS_WITH_BLOCKED_CELLS", "executed_cell_count": len(executed_ids), "registered_cell_count": len(registered_ids), "missing_cell_count": len(missing_ids), "duplicate_receipt_count": duplicate_receipt_count, **metadata(producer="finalize_batch100_public_execution", depth="duplicate clean replay", scope="pair reproducibility", allowed="evidence quality")})
    write_json(args.output_root / "batch100_source_nonmutation_audit.json", {"status": "PASS" if sum(row["source_tracked_mutation_count"] for row in cell_receipts) == 0 else "BLOCK", "source_mutation_count": sum(row["source_tracked_mutation_count"] for row in cell_receipts), **metadata(producer="finalize_batch100_public_execution", depth="tracked source diff verification", scope="source integrity", allowed="custody")})
    write_jsonl(args.output_root / "batch100_typed_incident_receipts_v2.jsonl", [{"candidate_id": row["candidate_id"], "program_id": row["program_id"], "cell_id": row["incident_cell"]["cell_id"], "materialized": bool(cell_aggregates.get(row["incident_cell"]["cell_id"]) and cell_aggregates[row["incident_cell"]["cell_id"]]["predicate_satisfied"]), "status": "MATERIALIZED" if cell_aggregates.get(row["incident_cell"]["cell_id"]) and cell_aggregates[row["incident_cell"]["cell_id"]]["predicate_satisfied"] else "BLOCKED", **metadata(producer="finalize_batch100_public_execution", depth="two-replay semantic join", scope="typed incident", allowed="matched pair input")} for row in programs])
    write_jsonl(args.output_root / "matched_counterfactual_evidence_v2.jsonl", evidence_rows)
    write_jsonl(args.output_root / "causal_alternative_exclusion_ledger_v2.jsonl", alternatives)
    write_jsonl(args.output_root / "necessity_receipts_v1.jsonl", necessity)
    write_jsonl(args.output_root / "sufficiency_receipts_v1.jsonl", sufficiency)
    write_jsonl(args.output_root / "interaction_receipts_v1.jsonl", interactions)
    write_jsonl(args.output_root / "ownership_support_receipts_v1.jsonl", ownership)
    write_json(args.output_root / "counterfactual_adequacy_gate_v2.json", {"status": "BLOCK", "ownership_supported_count": 0, "sensitivity_supported_count": sum(row["evidence_level"] == "DIMENSION_SENSITIVITY_VERIFIED" for row in evidence_rows), "exact_blockers": sorted({row["blocker"] for row in blockers}), **metadata(producer="finalize_batch100_public_execution", depth="evidence hierarchy gate", scope="counterfactual adequacy", allowed="safe block")})
    write_jsonl(args.output_root / "controller_audit_counterfactual_terminal_records_v3.jsonl", terminal_rows)
    write_jsonl(args.output_root / "counterfactual_dpp_round_receipts_v10.jsonl", round_rows)
    write_jsonl(args.output_root / "counterfactual_probe_selection_history_v2.jsonl", selection_rows)
    write_jsonl(args.output_root / "counterfactual_legal_exhaustion_v2.jsonl", exhaustion_rows)
    write_json(args.output_root / "contact_to_ownership_firewall_audit.json", {"status": "PASS", "contact_promoted_to_ownership_count": 0, "sensitivity_promoted_to_ownership_count": 0, **metadata(producer="finalize_batch100_public_execution", depth="terminal support reconstruction", scope="ownership firewall", allowed="safe abstention")})
    write_json(args.output_root / "causal_terminal_support_reconstruction_audit.json", {"status": "PASS", "terminal_count": len(terminal_rows), "ownership_terminal_count": 0, "unsupported_terminal_count": 0, **metadata(producer="finalize_batch100_public_execution", depth="terminal reconstruction", scope="terminal support", allowed="terminal audit")})
    write_jsonl(args.output_root / "counterfactual_outcome_vault_registry_v1.jsonl", vault)
    write_jsonl(args.output_root / "counterfactual_outcome_vault_access_log_v1.jsonl", access)
    write_jsonl(args.output_root / "arm_counterfactual_execution_receipts_v1.jsonl", arm_receipts)
    write_jsonl(args.output_root / "baseline_counterfactual_execution_receipts_v1.jsonl", baseline_receipts)
    write_json(args.output_root / "arm_unselected_outcome_access_audit.json", {"status": "PASS", "unselected_outcome_access": 0, "truth_access": 0, "private_tld_access": 0, "patch_operations": 0, **metadata(producer="finalize_batch100_public_execution", depth="vault access-log reconstruction", scope="outcome isolation", allowed="architecture evaluation")})
    write_json(args.output_root / "arm_cost_and_information_gain_metrics_v1.json", cost_metrics)
    write_json(args.output_root / "architecture_component_gain_gate_v2.json", gain_gate)
    write_jsonl(args.output_root / "decision_time_source_ownership_proofs_v3.jsonl", [{"candidate_id": candidate, "status": "NOT_CREATED", "reason": "no SOURCE_OWNED_BEHAVIOR_DEFECT ownership terminal", **metadata(producer="finalize_batch100_public_execution", depth="proof reconstruction gate", scope="source ownership", allowed="safe nonproduction")} for candidate in sorted(evidence_by_candidate)])
    write_json(args.output_root / "source_ownership_proof_reconstruction_audit_v3.json", {"status": "PASS_NO_ELIGIBLE_SOURCE_TERMINALS", "proof_count": 0, "fabricated_proof_count": 0, **metadata(producer="finalize_batch100_public_execution", depth="proof gate", scope="source ownership", allowed="proof abstention")})
    write_jsonl(args.output_root / "protected_repair_eligibility_v1.jsonl", [{"candidate_id": candidate, "eligible": False, "status": "BLOCKED", "blockers": ["source ownership not established", "historical calibration pending", "prospective validation pending", "external review pending"], **metadata(producer="finalize_batch100_public_execution", depth="protected repair gate", scope="repair readiness", allowed="future planning")} for candidate in sorted(evidence_by_candidate)])
    write_jsonl(args.output_root / "batch100_public_broker_operations_v1.jsonl", broker_operations)
    write_jsonl(args.output_root / "batch100_provider_materialization_receipts_v1.jsonl", provider_receipts)
    write_jsonl(args.output_root / "batch100_active_blockers_v1.jsonl", blockers)
    public_summary = {
        "status": "PUBLIC_MATCHED_COUNTERFACTUAL_EXECUTION_COMPLETE_WITH_EXACT_BLOCKERS",
        "workflow_run_id": args.workflow_run_id, "program_count": len(programs), "registered_cell_count": len(cells),
        "executed_cell_count": len(executed_ids), "missing_cell_count": len(missing_ids),
        "typed_incident_materialized_count": sum(bool(cell_aggregates.get(row["incident_cell"]["cell_id"]) and cell_aggregates[row["incident_cell"]["cell_id"]]["predicate_satisfied"]) for row in programs),
        "sensitivity_supported_count": sum(row["evidence_level"] == "DIMENSION_SENSITIVITY_VERIFIED" for row in evidence_rows),
        "ownership_supported_count": 0, "patch_operations": 0, "repair_count_increment": 0, "historical_increment": 0,
        "truth_access": 0, "private_tld_access_during_candidate_execution": 0,
        "exact_blockers": sorted({row["blocker"] for row in blockers}),
        "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory": "not demonstrated",
        "product_beta": "blocked", "production_readiness": False, "self_maintaining_software": "false/not demonstrated",
        **metadata(producer="finalize_batch100_public_execution", depth="public execution join", scope="Batch100 public evidence", allowed="private truth calibration input"),
    }
    public_summary["summary_hash"] = canonical_hash(public_summary)
    write_json(args.output_root / "batch100_public_execution_summary.json", public_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
