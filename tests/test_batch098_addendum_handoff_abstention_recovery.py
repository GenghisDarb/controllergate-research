from __future__ import annotations

import pytest

from controllergate.amds.branch_recovery_v1 import FailedBranchV1, NogoodStoreV1, canonical_assumptions, semantic_nogood_id
from controllergate.topology.causal_hypergraph import BoardCellV1, CellState
from controllergate.topology.environment_handoff_v1 import emit_environment_exhausted_handoff, environment_probe_allowed_after_handoff, validate_handoff
from controllergate.topology.frame_binding_v1 import authorize_probe, freeze_complete_frame, validate_frozen_frame
from controllergate.topology.probe_exhaustion_v1 import produce_exhaustion_receipt, verify_exhaustion_receipt
from controllergate.topology.probe_neutrality_v1 import lint_probe, reproducibility_conflict, source_counterfactual_allowed
from controllergate.topology.tld_shadow_firewall_v1 import assert_transition_input_safe, direct_fact_parent_rule, disabled_arm_terminal_invariance


def cell(subject: str, cell_class: str, state: CellState) -> BoardCellV1:
    return BoardCellV1("candidate", "run", "frame", cell_class, subject, state, ("a" * 64,), f"producer:{subject}", f"verifier:{subject}", subject, "provisional", ("repair",), "reopen")


def handoff():
    return emit_environment_exhausted_handoff(
        environment_cells=[cell("runtime", "ENVIRONMENT_BOUNDARY", CellState.VERIFIED_TRUE), cell("network", "ENVIRONMENT_BOUNDARY", CellState.NOT_APPLICABLE)],
        causal_cells=[cell("source", "OWNERSHIP_SOURCE", CellState.UNRESOLVED)],
        environment_alignment_plan_hash="p" * 64,
        observer_state_hash="o" * 64,
    )


def complete_frame() -> dict:
    return {
        "board_cells": [], "board_edges": [], "causal_regions": [], "boundary_cells": [], "environment_exhausted_handoff": None,
        "projection_pairs": [], "orthology_invariants": [], "causal_hypotheses": [{"hypothesis_id": "h1"}, {"hypothesis_id": "h2"}],
        "constraints": [], "minimal_probes": [{"probe_id": "p1", "predicted_neutral_partitions": {"a": ["h1"], "b": ["h2"]}}],
        "predicted_partitions": {"p1": {"a": ["h1"], "b": ["h2"]}}, "semantic_verifiers": ["v1"],
        "controls": {"positive": ["c1"], "negative": ["c2"], "adversarial": ["c3"]}, "budgets": {"time": 10},
        "probe_nonces": ["n1"], "observer_state_contract": {"id": "observer"}, "provisional_branch_root": "branch",
        "modality_contracts": ["runtime"], "tld_shadow_identities": {"bundle": "source"}, "sealed_truth_custody_identity": "sealed",
        "proof_release_parent": "proof", "legal_probe_exhaustion_root": None, "nogood_store_root": "empty",
    }


def test_environment_exhausted_emitted_when_boundary_complete_and_ownership_open() -> None:
    record = handoff()
    assert record.handoff_hash.startswith("environment-handoff:")
    assert "source ownership" in record.authority_forbidden


def test_unresolved_environment_cell_blocks_handoff() -> None:
    with pytest.raises(ValueError, match="unresolved"):
        emit_environment_exhausted_handoff(environment_cells=[cell("runtime", "ENVIRONMENT_BOUNDARY", CellState.UNRESOLVED)], causal_cells=[cell("source", "OWNERSHIP_SOURCE", CellState.UNRESOLVED)], environment_alignment_plan_hash="p", observer_state_hash="o")


def test_new_environment_identity_invalidates_handoff_and_limits_new_probes() -> None:
    record = handoff()
    current = {"frame_hash": record.frame_hash, "environment_alignment_plan_hash": "changed", "observer_state_hash": record.observer_state_hash, "boundary_cell_ids": list(record.boundary_cell_ids), "measurement_receipts": list(record.measurement_receipts), "verifier_receipts": list(record.verifier_receipts)}
    assert validate_handoff(record, current)["status"] == "INVALIDATED"
    assert environment_probe_allowed_after_handoff("new_raw_boundary_cell")
    assert not environment_probe_allowed_after_handoff("ownership_still_unresolved")


def test_empty_probe_list_without_enumeration_cannot_earn_abstention() -> None:
    with pytest.raises(ValueError, match="enumeration"):
        produce_exhaustion_receipt(candidate_id="c", run_id="r", frame_hash="f", unresolved_cell_ids=[], unresolved_region_ids=[], probe_inventory=[], budget_used={}, budget_remaining={}, why_remaining_budget_cannot_execute_a_legal_discriminating_probe="none", enumeration_complete=False, redundancy_complete=True, nogood_complete=True)


def test_zero_executable_probes_with_complete_blockers_can_earn_abstention() -> None:
    receipt = produce_exhaustion_receipt(candidate_id="c", run_id="r", frame_hash="f", unresolved_cell_ids=["cell"], unresolved_region_ids=[], probe_inventory=[{"probe_id": "p", "classification": "BLOCKED_AUTHORITY", "evidence_reason": "protected operation unavailable", "admissible_unspent": False, "discriminates_at_least_two": True}], budget_used={"time": 0}, budget_remaining={"time": 10}, why_remaining_budget_cannot_execute_a_legal_discriminating_probe="every discriminating probe is independently authority-blocked", enumeration_complete=True, redundancy_complete=True, nogood_complete=True)
    assert verify_exhaustion_receipt(receipt, {"frame_hash": "f", "probes": [{"probe_id": "p"}]})["earned_insufficient_evidence"]


def test_remaining_discriminating_probe_rejects_abstention() -> None:
    with pytest.raises(ValueError, match="remains"):
        produce_exhaustion_receipt(candidate_id="c", run_id="r", frame_hash="f", unresolved_cell_ids=["cell"], unresolved_region_ids=[], probe_inventory=[{"probe_id": "p", "classification": "BLOCKED_RESOURCE", "evidence_reason": "budget", "admissible_unspent": True, "discriminates_at_least_two": True}], budget_used={}, budget_remaining={"time": 10}, why_remaining_budget_cannot_execute_a_legal_discriminating_probe="incorrect", enumeration_complete=True, redundancy_complete=True, nogood_complete=True)


def failed_branch(recovery: str = "region") -> FailedBranchV1:
    assumptions = canonical_assumptions([{"subject": "source", "state": True}, {"subject": "provider", "state": False}])
    nogood = "nogood:" + __import__("hashlib").sha256(__import__("json").dumps(assumptions, separators=(",", ":")).encode()).hexdigest()
    return FailedBranchV1("branch", "candidate", "run", "frame", "observer", "parent", "checkpoint", assumptions, ("observation",), ("fact",), "evidence", nogood, ("nonce",), ("cell",), ("edge",), ("region",), "rollback", "PASS", recovery, "new direct evidence", "CLOSED", ("recovery planning",), ("source ownership", "repair license", "count mutation"))


def test_failed_branch_requires_recovery_region() -> None:
    with pytest.raises(ValueError, match="recovery_region"):
        failed_branch("")


def test_semantically_equivalent_nogood_and_spent_nonce_are_rejected() -> None:
    store = NogoodStoreV1(); store.close_branch(failed_branch())
    equivalent = [{"state": False, "subject": "provider"}, {"state": True, "subject": "source"}]
    result = store.authorize_branch(equivalent, "nonce")
    assert result["status"] == "REJECTED"
    assert "semantic_nogood_repetition" in result["reasons"] and "spent_nonce_reuse" in result["reasons"]
    with pytest.raises(ValueError, match="deletion forbidden"):
        store.delete("branch")


def test_probe_neutrality_rejects_causal_family_output_key() -> None:
    assert lint_probe({"probe_id": "neutral", "output_schema": {"source_owned": {"type": "boolean"}}})["status"] == "REJECTED"


def test_deterministic_probe_divergence_creates_conflict() -> None:
    result = reproducibility_conflict({"observation_id": "one", "return_code": 0}, {"observation_id": "two", "return_code": 1}, environment_parity=True, observer_state_parity=True)
    assert result["status"] == "PROBE_REPRODUCIBILITY_CONFLICT" and result["terminal_selected"] is False


def test_source_counterfactual_requires_frozen_safe_custody() -> None:
    allowed = {key: True for key in ("frozen_before_target", "decision_time_safe", "independently_custodied", "candidate_contract_permitted", "nonauthorizing")}
    assert source_counterfactual_allowed(allowed)
    assert not source_counterfactual_allowed({**allowed, "future_fixed_revision": True})


def test_probe_or_partition_mutation_invalidates_complete_frame() -> None:
    payload = complete_frame(); frozen = freeze_complete_frame(payload)
    mutated = complete_frame(); mutated["minimal_probes"][0]["predicted_neutral_partitions"]["a"] = ["h2"]
    assert validate_frozen_frame(frozen, mutated)["status"] == "INVALIDATED"
    assert authorize_probe("unregistered", frozen)["status"] == "REJECTED"


def test_tld_shadow_cannot_write_cell_state_and_disabled_arm_is_invariant() -> None:
    with pytest.raises(ValueError, match="TLD shadow"):
        assert_transition_input_safe({"shadow_hint": "set true"})
    builder = lambda frame, tld_arm_enabled, tld_shadow: "SOURCE" if frame["direct"] else "INSUFFICIENT"
    result = disabled_arm_terminal_invariance(builder, {"direct": True}, {"winner_N": 1}, {"winner_N": 9})
    assert result["status"] == "PASS" and result["TLD_disabled_terminal_mutation_count"] == 0


def test_direct_local_fact_single_observation_plus_verifier_is_allowed() -> None:
    assert direct_fact_parent_rule(claim_scope="local_deterministic", executed_observation_count=1, independent_verifier_count=1, independent_parent_count=1)["status"] == "PASS"
    assert direct_fact_parent_rule(claim_scope="statistical_transfer", executed_observation_count=1, independent_verifier_count=1, independent_parent_count=1)["status"] == "BLOCK"
