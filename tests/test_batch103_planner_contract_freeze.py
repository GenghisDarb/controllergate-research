import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization"


def jsonl(name: str):
    return [json.loads(line) for line in (OUT / name).read_text().splitlines() if line.strip()]


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_all_matched_arm_contracts_are_frozen_with_equal_inputs():
    contracts = jsonl("reactome_planner_arm_contracts_v1.jsonl")
    assert len(contracts) == 90
    by_program = defaultdict(list)
    for row in contracts:
        by_program[row["program_id"]].append(row)
        unsigned = dict(row)
        recorded = unsigned.pop("contract_hash")
        assert recorded == canonical_hash(unsigned)
        assert row["truth_blind"] is True
        assert row["repair_prohibition"] is True
        assert row["selected_outcome_only"] is True
        assert row["all_arms_receive_every_outcome"] is False
    assert len(by_program) == 9
    for rows in by_program.values():
        assert {row["arm"] for row in rows} == set("ABCDEFGHIJ")
        assert len({json.dumps(row["resource_budget"], sort_keys=True) for row in rows}) == 1
        assert len({row["candidate_evidence_hash"] for row in rows}) == 1
        assert len({row["legal_intervention_inventory_hash"] for row in rows}) == 1
        assert len({row["source_provider_availability_hash"] for row in rows}) == 1


def test_all_70_candidate_interventions_are_legal_and_nonauthorizing():
    interventions = jsonl("batch103_candidate_intervention_registry_v1.jsonl")
    assert len(interventions) == 70
    assert len({row["intervention_id"] for row in interventions}) == 70
    assert all(row["legal"] is True for row in interventions)
    assert all(row["patch_operations"] == row["truth_access"] == row["private_tld_access"] == 0 for row in interventions)


def test_pre_outcome_plans_select_only_frozen_legal_inventory():
    interventions = {row["intervention_id"] for row in jsonl("batch103_candidate_intervention_registry_v1.jsonl")}
    plans = jsonl("reactome_planner_pre_outcome_plans_v1.jsonl")
    assert len(plans) == 90
    for plan in plans:
        unsigned = dict(plan)
        recorded = unsigned.pop("pre_outcome_plan_hash")
        assert recorded == canonical_hash(unsigned)
        assert plan["created_before_outcomes"] is True
        assert plan["outcome_field_count"] == 0
        assert plan["truth_access"] == 0
        assert set(plan["ordered_intervention_ids"]).issubset(interventions)
        assert len(plan["ordered_intervention_ids"]) <= plan["budget"] == 8
        if plan["arm"] == "J":
            assert plan["selected_intervention_id"] is None
        else:
            assert plan["selected_intervention_id"] == plan["ordered_intervention_ids"][0]


def test_vaults_have_no_outcomes_or_truth_before_execution():
    vault = json.loads((OUT / "reactome_planner_outcome_vault_registry_v1.json").read_text())
    assert vault["status"] == "PASS_PRE_OUTCOME_FREEZE"
    assert vault["vault_count"] == 70
    assert vault["outcomes_present"] == 0
    assert vault["truth_present"] == 0
    assert vault["unselected_outcome_access_allowed"] is False


def test_freeze_receipt_records_zero_outcome_access_and_actuation():
    receipt = json.loads((OUT / "batch103_planner_contract_freeze_receipt_v1.json").read_text())
    unsigned = dict(receipt)
    recorded = unsigned.pop("freeze_receipt_hash")
    assert recorded == canonical_hash(unsigned)
    assert receipt["status"] == "PASS_BATCH103_PRE_OUTCOME_CONTRACT_FREEZE"
    assert receipt["arm_contract_count"] == 90
    assert receipt["pre_outcome_plan_count"] == 90
    assert receipt["outcomes_opened"] == 0
    assert receipt["truth_access"] == 0
    assert receipt["patch_operations"] == 0
