from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from controllergate.amds.dpp14.causal_board import freeze_decision_frame
from controllergate.amds.dpp14.observation_schema import parse_neutral_observation
from controllergate.amds.dpp14.probe_planner import select_probe
from scripts.run_batch088_amds_builder import build_board


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch088_causal_amds_historical_capsule_product_beta_closure"


def cohort() -> dict:
    return json.loads((ROOT / "configs/batch088_historical_cohort_decision_time.json").read_text(encoding="utf-8"))


def test_candidate_specific_frames_bind_complete_probe_contracts():
    first, first_contracts = build_board(cohort()["episodes"][0])
    second, _ = build_board(cohort()["episodes"][1])
    assert first.frame.frame_hash != second.frame.frame_hash
    assert len(first.frame.probe_contracts) == len(first_contracts) == 4
    changed = replace(first_contracts[0], cost=first_contracts[0].cost + 1)
    changed_frame = freeze_decision_frame(
        candidate_id=first.frame.candidate_id,
        run_id=first.frame.run_id,
        anchors={key: getattr(first.frame, key) for key in (
            "command_authority_identity", "harness_origin", "incident_snapshot_identity",
            "proof_release_parent_identity", "provider_runtime_abi_identity", "runner_origin",
            "source_revision_identity", "source_tree_hash", "target_reproducer_identity", "test_tree_hash",
        )},
        hypotheses=list(first.hypotheses.values()),
        constraints=first.constraints,
        contracts=[changed, *first_contracts[1:]],
        budgets={"authorization_scope": "test", "cost": 10, "risk": 2},
        allowed_output_roots=("runtime/test",),
        memory_mode="no_memory_test",
    )
    assert changed_frame.frame_hash != first.frame.frame_hash


def test_semantic_aliases_and_unregistered_fields_are_rejected():
    with pytest.raises(ValueError, match="unregistered neutral observation fields"):
        parse_neutral_observation('{"return_code": 0, "source_contact": true}')
    board, contracts = build_board(cohort()["episodes"][0])
    with pytest.raises(ValueError, match="semantic alias leakage"):
        replace(contracts[0], probe_id="provider_failure").validate()


def test_minimax_planner_is_active_and_stable_without_likelihoods():
    board, contracts = build_board(cohort()["episodes"][0])
    one = select_probe(active_hypotheses=board.active_hypotheses, contracts=contracts, spent_contract_hashes=set())
    two = select_probe(active_hypotheses=board.active_hypotheses, contracts=list(reversed(contracts)), spent_contract_hashes=set())
    assert one.status == "SELECTED"
    assert one.selection_method == "deterministic_minimax_partition"
    assert one.selected_contract_hash == two.selected_contract_hash


def test_no_information_probe_is_not_selected_and_no_forced_source_fallback():
    board, contracts = build_board(cohort()["episodes"][0])
    no_info = replace(
        contracts[0],
        predicted_outcome_partitions={"r01": tuple(board.active_hypotheses), "r02": tuple(board.active_hypotheses)},
    )
    record = select_probe(active_hypotheses=board.active_hypotheses, contracts=[no_info], spent_contract_hashes=set())
    assert record.status == "NO_LEGAL_DISCRIMINATING_PROBE"
    terminal = json.loads((OUT / "amds_quality_gate.json").read_text(encoding="utf-8"))
    assert terminal["wrong_patch_authorization_count"] == 0


def test_adversarial_contradiction_backtrack_and_meta_cell_are_executed():
    value = json.loads((OUT / "amds_contradiction_backtrack_audit.json").read_text(encoding="utf-8"))
    assert value["status"] == "PASS"
    assert value["contradictions"] >= 2
    assert value["backtracks"] >= 2
    assert value["meta_cell_expansions"] >= 1
    assert all(row["branch_closed"] and row["reopen_condition"] for row in value["failed_branches"])


def test_truth_is_separate_and_quality_does_not_overclaim():
    quality = json.loads((OUT / "amds_quality_gate.json").read_text(encoding="utf-8"))
    assert quality["decision_time_truth_overlap_count"] == 0
    assert quality["truth_received_after_terminal_commit"] is True
    assert quality["historical_quality_result"] == "BLOCK_HISTORICAL_CAUSAL_QUALITY_CRITERIA_NOT_MET"
    assert quality["prospective_effectiveness"] == "NOT_ESTABLISHED"


def test_release_block_and_claim_counts_are_exact():
    release = json.loads((OUT / "batch088_product_beta_rc_decision.json").read_text(encoding="utf-8"))
    claims = json.loads((OUT / "batch088_claim_boundary.json").read_text(encoding="utf-8"))
    assert release["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT"
    assert release["package_version"] == "0.2.0b2.dev0"
    assert claims["issue_derived_repair_count"] == 6
    assert claims["native_external_repair_count"] == 4
    assert claims["historical_replay_count_increment"] == 0
    assert claims["full_scoring"] == "NOT_RUN/disallowed"


def test_minesweeper_is_salvage_only_not_a_runtime_dependency():
    registry = json.loads((ROOT / "configs/amds_minesweeper_salvage_registry.json").read_text(encoding="utf-8"))
    assert registry["production_dependency"] is False
    source_audit = json.loads((OUT / "amds_minesweeper_source_audit.json").read_text(encoding="utf-8"))
    assert source_audit["forbidden_source_code_copied"] is False
    assert source_audit["package_imported"] is False


def test_tld_is_evidence_bound_shadow_only():
    projection = json.loads((OUT / "tld_three_projection_execution.json").read_text(encoding="utf-8"))
    curvature = json.loads((OUT / "tld_curvature_elbow_audit.json").read_text(encoding="utf-8"))
    assert projection["status"] == "PASS_SHADOW_ONLY"
    assert projection["repair_authority"] is False
    assert curvature["status"] == "NOT_RUN_NO_REGISTERED_REAL_TRACE"
    assert curvature["winner_N"] is None
