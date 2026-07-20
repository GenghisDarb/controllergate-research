"""Execute one preregistered truth-blind Batch103 planner arm against sealed outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.reactome_planner_v1 import plan_intervention


STATIC_OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization"
REACTOME_ARMS = set("BCDEF")


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _predicate_true(envelope: dict[str, Any]) -> bool:
    return bool(envelope["outcomes"]) and all(row["predicate_result"] for row in envelope["outcomes"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=list("ABCDEFGHIJ"), required=True)
    parser.add_argument("--outcome-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)

    plans = [
        row
        for row in read_jsonl(STATIC_OUT / "reactome_planner_pre_outcome_plans_v1.jsonl")
        if row["arm"] == args.arm
    ]
    contracts = {
        row["contract_id"]: row
        for row in read_jsonl(STATIC_OUT / "reactome_planner_arm_contracts_v1.jsonl")
        if row["arm"] == args.arm
    }
    interventions = {
        row["intervention_id"]: row
        for row in read_jsonl(STATIC_OUT / "batch103_candidate_intervention_registry_v1.jsonl")
    }
    cells = {
        row["cell_id"]: row
        for row in read_jsonl(ROOT / "configs/batch102_counterfactual_cell_registry_v4.jsonl")
    }
    programs = {
        row["program_id"]: row
        for row in read_jsonl(ROOT / "configs/batch102_candidate_counterfactual_programs_v4.jsonl")
    }
    envelopes = {
        row["cell_id"]: row
        for row in read_jsonl(args.outcome_root / "batch103_outcome_envelopes_v1.jsonl")
    }
    seal = json.loads(
        (args.outcome_root / "batch103_outcome_envelope_seal_receipt_v1.json").read_text(encoding="utf-8")
    )
    if not seal["sealed_before_arm_execution"] or seal["truth_access"] != 0:
        raise RuntimeError("outcome envelopes were not safely sealed")

    completeness = json.loads(
        (STATIC_OUT / "reactome_mapping_completeness_v2.json").read_text(encoding="utf-8")
    )
    rpir_parent = completeness["source_reaction_sha256"]
    selections: list[dict[str, Any]] = []
    accesses: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []
    terminals: list[dict[str, Any]] = []
    for plan in plans:
        contract = contracts[plan["contract_id"]]
        ordered = list(plan["ordered_intervention_ids"])
        opened: list[dict[str, Any]] = []
        unavailable: list[str] = []
        evidence_level = "PRESENCE_VERIFIED"
        first_sensitivity_step: int | None = None
        for step, expected_selection in enumerate(ordered, 1):
            if step > int(plan["budget"]):
                break
            remaining = ordered[step - 1 :]
            actions = []
            for rank, intervention_id in enumerate(remaining):
                action = dict(interventions[intervention_id])
                action["cost"] = 1
                action["expected_information_gain"] = float(len(remaining) - rank)
                actions.append(action)
            relations = []
            if args.arm in REACTOME_ARMS:
                relations.append(
                    {
                        "source_hash": rpir_parent,
                        "reaction": f"software-maintenance-analogue:{plan['program_id']}",
                        "blocked": bool(unavailable),
                        "missing_prerequisites": tuple(sorted(unavailable)),
                        "alternative_pathways": tuple(remaining[1:]),
                    }
                )
            decision = plan_intervention(
                candidate=plan["candidate_id"],
                maintenance_state={
                    "opened_outcome_count": len(opened),
                    "unavailable_selection_count": len(unavailable),
                    "evidence_level": evidence_level,
                },
                public_rpir_relations=relations,
                legal_interventions=actions,
                budget=int(plan["budget"]) - step + 1,
            )
            if decision.selected_intervention != expected_selection:
                raise RuntimeError("runtime selection departed from the preregistered plan")
            selection = {
                "selection_id": f"batch103-selection:{args.arm}:{plan['program_id']}:{step}",
                "arm": args.arm,
                "program_id": plan["program_id"],
                "candidate_id": plan["candidate_id"],
                "step": step,
                "pre_outcome_plan_hash": plan["pre_outcome_plan_hash"],
                "contract_hash": contract["contract_hash"],
                **decision.record(),
                "selected_before_outcome_access": True,
            }
            selection["selection_receipt_hash"] = canonical_hash(selection)
            selections.append(selection)

            envelope = envelopes.get(expected_selection)
            access = {
                "access_id": f"batch103-vault-access:{args.arm}:{plan['program_id']}:{step}",
                "selection_id": selection["selection_id"],
                "arm": args.arm,
                "program_id": plan["program_id"],
                "selected_cell_id": expected_selection,
                "selected_before_access": True,
                "unselected_outcome_access_count": 0,
                "all_arms_broadcast": False,
                "truth_access": 0,
                "private_tld_access": 0,
                "status": "OPENED_SELECTED_OUTCOME" if envelope else "SELECTED_OUTCOME_UNAVAILABLE",
                "envelope_id": envelope["envelope_id"] if envelope else None,
                "envelope_hash": envelope["envelope_hash"] if envelope else None,
            }
            access["access_receipt_hash"] = canonical_hash(access)
            accesses.append(access)
            if envelope is None:
                unavailable.append(expected_selection)
                continue
            opened.append(envelope)
            opened_ids = {row["cell_id"] for row in opened}
            program_cells = [cells[cell_id] for cell_id in opened_ids]
            incident = any(
                row["cell_role"] == "incident"
                and envelopes[row["cell_id"]]["semantic_reproducibility"]
                and _predicate_true(envelopes[row["cell_id"]])
                for row in program_cells
            )
            control = any(
                row["cell_role"] == "control"
                and envelopes[row["cell_id"]]["semantic_reproducibility"]
                and _predicate_true(envelopes[row["cell_id"]])
                for row in program_cells
            )
            if incident and control:
                evidence_level = "DIMENSION_SENSITIVITY_VERIFIED"
                first_sensitivity_step = step
                break
            if incident:
                evidence_level = "CONTACT_VERIFIED"

        program = programs[plan["program_id"]]
        opened_ids = {row["cell_id"] for row in opened}
        typed_incident = any(
            cells[cell_id]["cell_role"] == "incident"
            and envelopes[cell_id]["semantic_reproducibility"]
            and _predicate_true(envelopes[cell_id])
            for cell_id in opened_ids
        )
        valid_pair = first_sensitivity_step is not None
        required_factorial = {
            program["incident_cell"]["cell_id"],
            program["control_cell"]["cell_id"],
            *program.get("negative_controls", []),
        }
        factorial_complete = len(required_factorial) >= 4 and required_factorial.issubset(opened_ids)
        terminal = (
            "DIMENSION_SENSITIVITY_VERIFIED"
            if valid_pair
            else "SAFE_ABSTENTION" if args.arm == "J" else "INSUFFICIENT_EVIDENCE"
        )
        execution = {
            "execution_id": f"batch103-arm-execution:{args.arm}:{plan['program_id']}",
            "arm": args.arm,
            "program_id": plan["program_id"],
            "candidate_id": plan["candidate_id"],
            "pre_outcome_plan_hash": plan["pre_outcome_plan_hash"],
            "contract_hash": contract["contract_hash"],
            "opened_envelope_ids": [row["envelope_id"] for row in opened],
            "legal_operations_consumed": len(opened) + len(unavailable),
            "unnecessary_operations": 0,
            "repeated_failed_branch_count": 0,
            "typed_incident_materialized": typed_incident,
            "blocked_cells_reduced": len(opened),
            "valid_pair_count": int(valid_pair),
            "complete_factorial_count": int(factorial_complete),
            "time_to_first_sensitivity": first_sensitivity_step,
            "time_to_necessity_or_sufficiency": None,
            "time_to_ownership_grade_evidence": None,
            "false_attribution": "NOT_EVALUABLE_PUBLIC",
            "unsafe_authority": 0,
            "truth_leakage": 0,
            "private_data_leakage": 0,
            "terminal": terminal,
            "authority_allowed": "truth-blind evidence-level terminal at executed depth",
            "authority_forbidden": ["ownership", "patch", "repair count", "release"],
        }
        execution["execution_receipt_hash"] = canonical_hash(execution)
        executions.append(execution)
        terminal_row = {
            "terminal_id": f"batch103-planner-terminal:{args.arm}:{plan['program_id']}",
            "arm": args.arm,
            "program_id": plan["program_id"],
            "candidate_id": plan["candidate_id"],
            "terminal": terminal,
            "evidence_level": evidence_level,
            "execution_receipt_hash": execution["execution_receipt_hash"],
            "writer": "ReactomePlannerDecisionV1",
            "truth_access": 0,
            "authority_allowed": "nonauthorizing planner recommendation",
            "authority_forbidden": ["causal ownership", "patch", "repair count", "release"],
        }
        terminal_row["terminal_hash"] = canonical_hash(terminal_row)
        terminals.append(terminal_row)

    write_jsonl(args.output_root / "reactome_planner_selection_history_v1.jsonl", selections)
    write_jsonl(args.output_root / "reactome_planner_execution_receipts_v1.jsonl", executions)
    write_jsonl(args.output_root / "reactome_planner_outcome_vault_access_v1.jsonl", accesses)
    write_jsonl(args.output_root / "reactome_planner_truth_blind_terminals_v1.jsonl", terminals)
    summary = {
        "status": "PASS_TRUTH_BLIND_ARM_EXECUTION",
        "arm": args.arm,
        "program_count": len(executions),
        "selection_count": len(selections),
        "opened_outcome_count": sum(row["status"] == "OPENED_SELECTED_OUTCOME" for row in accesses),
        "unselected_outcome_access_count": 0,
        "truth_access": 0,
        "private_tld_access": 0,
        "unsafe_authority": 0,
    }
    summary["summary_hash"] = canonical_hash(summary)
    write_json(args.output_root / f"reactome_planner_arm_{args.arm}_summary_v1.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
