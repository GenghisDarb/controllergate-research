"""Freeze matched Batch103 arm and legal-intervention plans before outcomes."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization"
FREEZE_PARENT = "7b66ec50d0afc4b9e672e53f91c255e154d7d0e9"
COMMON_BUDGET = {
    "legal_operations": 8,
    "memory_mb": 4096,
    "processes": 16,
    "timeout_seconds": 1800,
}

ARM_POLICIES = {
    "A": ("TREATMENT", "canonical AMDS without Reactome", ["canonical_amds"]),
    "B": ("TREATMENT", "AMDS plus structural RPIR graph", ["canonical_amds", "structural_rpir_graph"]),
    "C": ("TREATMENT", "AMDS plus source-grounded Reactome translations", ["canonical_amds", "structural_rpir_graph", "source_grounded_translation"]),
    "D": ("TREATMENT", "AMDS plus reaction-specific Reactome shadow operations", ["canonical_amds", "structural_rpir_graph", "source_grounded_translation", "reaction_specific_shadow"]),
    "E": ("TREATMENT", "arm D plus corrected 5-14-6-196 operational order", ["canonical_amds", "structural_rpir_graph", "source_grounded_translation", "reaction_specific_shadow", "canonical_stack_v3"]),
    "F": ("TREATMENT", "arm E plus public-safe TLD opaque ordering", ["canonical_amds", "structural_rpir_graph", "source_grounded_translation", "reaction_specific_shadow", "canonical_stack_v3", "public_safe_tld_opaque_ordering"]),
    "G": ("BASELINE", "fixed legal order", ["fixed_legal_order"]),
    "H": ("BASELINE", "frozen random legal order", ["frozen_random_legal_order"]),
    "I": ("BASELINE", "no-memory active minimax", ["no_memory_active_minimax"]),
    "J": ("BASELINE", "zero-operation abstention baseline", ["zero_operation_abstention"]),
}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _role_rank(role: str) -> int:
    return {"incident": 0, "control": 1, "negative": 2, "exclusion": 3}.get(role, 4)


def order_for_arm(
    arm: str,
    candidate: str,
    cells: list[dict[str, Any]],
    tld_orders: dict[str, list[str]],
) -> list[str]:
    if arm == "J":
        return []
    if arm in {"A", "G"}:
        ordered = list(cells)
    elif arm == "B":
        ordered = sorted(cells, key=lambda row: (_role_rank(row["cell_role"]), row.get("provider_capsule_id", ""), row["cell_id"]))
    elif arm == "C":
        ordered = sorted(cells, key=lambda row: (_role_rank(row["cell_role"]), -len(row.get("factor_values", {})), row["cell_id"]))
    elif arm == "D":
        ordered = sorted(cells, key=lambda row: (row.get("service_identity") is None, _role_rank(row["cell_role"]), row["cell_id"]))
    elif arm == "E":
        ordered = sorted(cells, key=lambda row: (_role_rank(row["cell_role"]), row.get("platform") != "linux", row["cell_id"]))
    elif arm == "F":
        by_id = {row["cell_id"]: row for row in cells}
        tld = [by_id[cell_id] for cell_id in tld_orders.get(candidate, []) if cell_id in by_id]
        seen = {row["cell_id"] for row in tld}
        ordered = tld + sorted((row for row in cells if row["cell_id"] not in seen), key=lambda row: row["cell_id"])
    elif arm == "H":
        ordered = sorted(cells, key=lambda row: canonical_hash([candidate, "frozen-random-v1", row["cell_id"]]))
    elif arm == "I":
        ordered = sorted(cells, key=lambda row: (-len(row.get("factor_values", {})), row["cell_role"] == "incident", row["cell_id"]))
    else:
        raise ValueError(f"unknown arm {arm}")
    return [row["cell_id"] for row in ordered[: COMMON_BUDGET["legal_operations"]]]


def main() -> int:
    programs = read_jsonl(ROOT / "configs/batch102_candidate_counterfactual_programs_v4.jsonl")
    cells = read_jsonl(ROOT / "configs/batch102_counterfactual_cell_registry_v4.jsonl")
    tld = read_jsonl(ROOT / "configs/batch100_opaque_tld_ordering_registry_v1.jsonl")
    if len(programs) != 9 or len(cells) != 70:
        raise RuntimeError("locked Batch102 program/cell inventory changed")
    program_by_id = {row["program_id"]: row for row in programs}
    by_program: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        by_program[cell["program_id"]].append(cell)
    tld_orders = {
        row["candidate_id"]: row["ordered_opaque_probe_ids"]
        for row in tld
        if row["arm_id"] == "F"
    }
    intervention_rows = []
    for cell in cells:
        program = program_by_id[cell["program_id"]]
        # The v4 registry preserves native factor assignments for the original
        # Batch100 cells.  Cells added by the Batch102 closure are already
        # atomic registered interventions, so their locked cell name is the
        # factor assignment rather than an invented reconstruction.
        factor_values = cell.get("factor_values") or {"registered_cell_name": cell["cell_name"]}
        provider_capsule_ids = (
            [cell["provider_capsule_id"]]
            if cell.get("provider_capsule_id")
            else list(program["provider_capsule_ids"])
        )
        service_identity = cell.get("service_identity")
        if "service_identity" not in cell:
            service_identity = program.get("service_identity", {}).get(cell["cell_id"])
        row = {
            "intervention_id": cell["cell_id"],
            "candidate_id": cell["candidate_id"],
            "program_id": cell["program_id"],
            "cell_role": cell["cell_role"],
            "factor_values": factor_values,
            "platform": cell.get("platform", "contract-defined"),
            "command_hash": cell["command_hash"],
            "environment_hash": cell["environment_hash"],
            "fixture_hash": cell["fixture_hash"],
            "provider_capsule_ids": provider_capsule_ids,
            "required_source_commit": cell["required_source_commit"],
            "required_secondary_source_commit": cell["required_secondary_source_commit"],
            "service_identity": service_identity,
            "legal": True,
            "patch_operations": 0,
            "truth_access": 0,
            "private_tld_access": 0,
            "authority_allowed": "fresh truth-blind observation if exact source/provider preflight passes",
            "authority_forbidden": ["invented dependency", "invented fixture", "illegal probe", "patch", "repair count", "release"],
        }
        row["intervention_hash"] = canonical_hash(row)
        intervention_rows.append(row)
    write_jsonl(OUT / "batch103_candidate_intervention_registry_v1.jsonl", intervention_rows)

    evidence_hash = sha256_file(OUT / "batch102_official_ingest/reconciliation/batch102_official_semantic_reconciliation.json")
    provider_hash = sha256_file(OUT / "batch102_official_ingest/extracted_public_artifact/batch102_provider_capsule_registry_v4.jsonl")
    source_hash = sha256_file(OUT / "batch102_official_ingest/extracted_public_artifact/batch102_source_capsule_registry_v2.jsonl")
    contracts = []
    plans = []
    vaults = []
    for program in programs:
        program_cells = by_program[program["program_id"]]
        inventory = [row for row in intervention_rows if row["program_id"] == program["program_id"]]
        inventory_hash = canonical_hash([row["intervention_hash"] for row in inventory])
        availability_hash = canonical_hash([source_hash, provider_hash, program["program_id"]])
        for arm, (arm_type, policy, components) in ARM_POLICIES.items():
            contract = {
                "contract_id": f"batch103-arm:{arm}:{program['program_id']}",
                "arm": arm,
                "arm_type": arm_type,
                "candidate_id": program["candidate_id"],
                "program_id": program["program_id"],
                "policy": policy,
                "planner_components": components,
                "candidate_evidence_hash": evidence_hash,
                "legal_intervention_inventory_hash": inventory_hash,
                "source_provider_availability_hash": availability_hash,
                "resource_budget": COMMON_BUDGET,
                "truth_blind": True,
                "repair_prohibition": True,
                "selected_outcome_only": True,
                "all_arms_receive_every_outcome": False,
                "arms_may_differ_only_by": "planner_components",
                "freeze_parent_commit": FREEZE_PARENT,
                "authority_allowed": "select from the frozen legal inventory and write a truth-blind abstention/support terminal at executed depth",
                "authority_forbidden": ["truth", "private TLD passages", "illegal probe", "invented dependency", "invented fixture", "patch", "repair count", "release"],
            }
            contract["contract_hash"] = canonical_hash(contract)
            contracts.append(contract)
            ordered = order_for_arm(arm, program["candidate_id"], program_cells, tld_orders)
            plan = {
                "plan_id": f"batch103-pre-outcome-plan:{arm}:{program['program_id']}",
                "contract_id": contract["contract_id"],
                "contract_hash": contract["contract_hash"],
                "arm": arm,
                "candidate_id": program["candidate_id"],
                "program_id": program["program_id"],
                "ordered_intervention_ids": ordered,
                "selected_intervention_id": ordered[0] if ordered else None,
                "legal_intervention_inventory_hash": inventory_hash,
                "budget": COMMON_BUDGET["legal_operations"],
                "created_before_outcomes": True,
                "outcome_field_count": 0,
                "truth_access": 0,
                "private_tld_passage_count": 0,
                "outcome_access_policy": "selected intervention only, after selection",
                "authority_forbidden": ["plan mutation after outcome access", "unselected outcome", "patch", "repair count", "release"],
            }
            plan["pre_outcome_plan_hash"] = canonical_hash(plan)
            plans.append(plan)
        for intervention in inventory:
            vault = {
                "vault_id": f"batch103-vault:{intervention['intervention_id']}",
                "candidate_id": program["candidate_id"],
                "program_id": program["program_id"],
                "intervention_id": intervention["intervention_id"],
                "pre_outcome_status": "UNMATERIALIZED_PRE_OUTCOME",
                "access_rule": "one arm may open only its already-selected intervention outcome",
                "outcome_present": False,
                "truth_present": False,
            }
            vault["vault_contract_hash"] = canonical_hash(vault)
            vaults.append(vault)
    write_jsonl(OUT / "reactome_planner_arm_contracts_v1.jsonl", contracts)
    write_jsonl(OUT / "reactome_planner_pre_outcome_plans_v1.jsonl", plans)
    write_json(
        OUT / "reactome_planner_outcome_vault_registry_v1.json",
        {
            "status": "PASS_PRE_OUTCOME_FREEZE",
            "vault_count": len(vaults),
            "vaults": vaults,
            "outcomes_present": 0,
            "truth_present": 0,
            "unselected_outcome_access_allowed": False,
        },
    )
    receipt = {
        "status": "PASS_BATCH103_PRE_OUTCOME_CONTRACT_FREEZE",
        "freeze_parent_commit": FREEZE_PARENT,
        "program_count": len(programs),
        "candidate_intervention_count": len(intervention_rows),
        "arm_count": len(ARM_POLICIES),
        "arm_contract_count": len(contracts),
        "pre_outcome_plan_count": len(plans),
        "vault_count": len(vaults),
        "outcomes_opened": 0,
        "truth_access": 0,
        "patch_operations": 0,
        "repair_increment": 0,
        "historical_increment": 0,
        "authority_forbidden": ["outcome tuning", "plan mutation after outcome", "patch", "repair count", "release"],
    }
    receipt["freeze_receipt_hash"] = canonical_hash(receipt)
    write_json(OUT / "batch103_planner_contract_freeze_receipt_v1.json", receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
