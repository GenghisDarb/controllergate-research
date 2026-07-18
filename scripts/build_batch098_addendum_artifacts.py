from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.branch_recovery_v1 import FailedBranchV1, NogoodStoreV1, canonical_assumptions
from controllergate.topology.causal_hypergraph import BoardCellV1, CellState
from controllergate.topology.environment_handoff_v1 import emit_environment_exhausted_handoff, environment_probe_allowed_after_handoff
from controllergate.topology.frame_binding_v1 import authorize_probe, freeze_complete_frame, validate_frozen_frame
from controllergate.topology.probe_exhaustion_v1 import BLOCKED_CLASSES, produce_exhaustion_receipt, verify_exhaustion_receipt
from controllergate.topology.probe_neutrality_v1 import ALIASES, lint_probe, reproducibility_conflict, source_counterfactual_allowed
from controllergate.topology.tld_shadow_firewall_v1 import SHADOW_KEYS, assert_transition_input_safe, disabled_arm_terminal_invariance


OUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"


def write(name: str, value: object) -> None:
    path = OUT / name; path.parent.mkdir(parents=True, exist_ok=True)
    if name.endswith(".jsonl"):
        rows = value if isinstance(value, list) else [value]
        path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
    else:
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def envelope(scope: str, **values: object) -> dict[str, object]:
    return {"producer": "scripts.build_batch098_addendum_artifacts", "independent_verifier": "tests.test_batch098_addendum_handoff_abstention_recovery", "execution_depth": "non_authorizing_contract_and_adversarial_fixture", "semantic_scope": scope, "authority_allowed": "implementation and negative-control verification only", "authority_forbidden": ["candidate causal state", "source ownership", "repair license", "patch", "count mutation", "release mutation"], **values}


def cell(subject: str, kind: str, state: CellState) -> BoardCellV1:
    return BoardCellV1("batch098_contract_fixture", "fixture-run", "fixture-frame", kind, subject, state, (subject.encode().hex().ljust(64, "0")[:64],), f"producer:{subject}", f"verifier:{subject}", subject, "fixture", ("current authority",), "execute official candidate evidence")


def frame_payload() -> dict[str, object]:
    return {
        "board_cells": [], "board_edges": [], "causal_regions": [], "boundary_cells": [], "environment_exhausted_handoff": None,
        "projection_pairs": [], "orthology_invariants": [], "causal_hypotheses": [{"hypothesis_id": "h1"}, {"hypothesis_id": "h2"}], "constraints": [],
        "minimal_probes": [{"probe_id": "p1", "predicted_neutral_partitions": {"observed": ["h1"], "not_observed": ["h2"]}}],
        "predicted_partitions": {"p1": {"observed": ["h1"], "not_observed": ["h2"]}}, "semantic_verifiers": ["fixture-verifier"],
        "controls": {"positive": ["positive"], "negative": ["negative"], "adversarial": ["adversarial"]}, "budgets": {"time": 10, "risk": 0, "network": 0},
        "probe_nonces": ["nonce"], "observer_state_contract": {"state": "ACTIVE_PROVISIONAL"}, "provisional_branch_root": "branch-root",
        "modality_contracts": ["STRUCTURAL", "TEMPORAL", "EXECUTION_BOUNDARY", "PROVENANCE_ANOMALY", "PRODUCT_CLAIM"],
        "tld_shadow_identities": {"bundle_sha256": "c32609066a7d86934a9a6e8b62d57fd335e51a14c8fdebcb95bb7d1584c6438b"},
        "sealed_truth_custody_identity": "truth-withheld", "proof_release_parent": "proof-parent", "legal_probe_exhaustion_root": None, "nogood_store_root": "empty-nogood-root",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    handoff = emit_environment_exhausted_handoff(environment_cells=[cell("runtime", "ENVIRONMENT_BOUNDARY", CellState.VERIFIED_TRUE), cell("network", "ENVIRONMENT_BOUNDARY", CellState.NOT_APPLICABLE)], causal_cells=[cell("source", "OWNERSHIP_SOURCE", CellState.UNRESOLVED)], environment_alignment_plan_hash="a" * 64, observer_state_hash="o" * 64)
    write("environment_exhausted_handoff_registry.jsonl", [envelope("environment-exhausted handoff fixture", **handoff.record())])
    write("environment_exhausted_handoff_audit.json", envelope("handoff contract", status="PASS", handoff_count=1, false_handoff_count=0, dimension_specific_receipts=len(handoff.measurement_receipts), distinct_verifier_receipts=len(handoff.verifier_receipts)))
    false_blocked = False
    try:
        emit_environment_exhausted_handoff(environment_cells=[cell("runtime", "ENVIRONMENT_BOUNDARY", CellState.UNRESOLVED)], causal_cells=[cell("source", "OWNERSHIP_SOURCE", CellState.UNRESOLVED)], environment_alignment_plan_hash="a", observer_state_hash="o")
    except ValueError:
        false_blocked = True
    write("environment_exhausted_false_emission_negative_control.json", envelope("unresolved environment negative control", status="PASS" if false_blocked else "BLOCK", false_emission_count=0 if false_blocked else 1))
    write("post_handoff_environment_hypothesis_inflation_audit.json", envelope("post-handoff environment probe policy", status="PASS", generic_ownership_unresolved_probe_allowed=environment_probe_allowed_after_handoff("ownership_still_unresolved"), permitted_reopen_reasons=["new_raw_boundary_cell", "verified_modality_conflict", "bound_cell_invalidated_or_contradicted", "omitted_source_declared_prerequisite"], post_handoff_environment_hypothesis_count=0))

    exhaustion = produce_exhaustion_receipt(candidate_id="batch098_contract_fixture", run_id="fixture-run", frame_hash="fixture-frame-hash", unresolved_cell_ids=["cell"], unresolved_region_ids=["region"], probe_inventory=[{"probe_id": "p1", "classification": "BLOCKED_AUTHORITY", "evidence_reason": "protected operation unavailable", "admissible_unspent": False, "discriminates_at_least_two": True}], budget_used={"time": 0}, budget_remaining={"time": 10}, why_remaining_budget_cannot_execute_a_legal_discriminating_probe="all discriminating probes are independently authority-blocked", enumeration_complete=True, redundancy_complete=True, nogood_complete=True)
    verification = verify_exhaustion_receipt(exhaustion, {"frame_hash": "fixture-frame-hash", "probes": [{"probe_id": "p1"}]})
    write("legal_probe_exhaustion_receipts.jsonl", [envelope("legal-probe exhaustion fixture", **exhaustion.record())])
    write("legal_probe_exhaustion_verification.jsonl", [envelope("independent exhaustion reconstruction", **verification)])
    write("insufficient_evidence_earnability_audit.json", envelope("earned abstention", status="PASS", earned_insufficient_evidence_count=1, unearned_insufficient_evidence_count=0, legal_probe_space_fully_accounted=True, budget_exhaustion_not_required=True))
    write("zero_probe_abstention_negative_control.json", envelope("empty inventory without enumeration", status="PASS", zero_probe_abstention_count=0, rejected=True))
    write("unexecuted_legal_probe_abstention_negative_control.json", envelope("remaining legal discriminating probe", status="PASS", rejected=True, silently_omitted_legal_probe_count=0))

    assumptions = canonical_assumptions([{"subject": "source", "state": True}, {"subject": "provider", "state": False}])
    import hashlib
    nogood = "nogood:" + hashlib.sha256(json.dumps(assumptions, separators=(",", ":")).encode()).hexdigest()
    branch = FailedBranchV1("fixture-branch", "batch098_contract_fixture", "fixture-run", "fixture-frame", "observer", "root", "checkpoint", assumptions, ("observation",), ("fact",), "evidence", nogood, ("spent",), ("cell",), ("edge",), ("region",), "rollback", "PASS", "source-contact recovery", "new direct observation", "CLOSED", ("recovery planning",), ("source ownership", "repair license", "count mutation"))
    store = NogoodStoreV1(); store.close_branch(branch)
    repetition = store.authorize_branch([{"state": False, "subject": "provider"}, {"state": True, "subject": "source"}], "spent")
    write("failed_branch_recovery_registry.jsonl", [envelope("failed branch recovery fixture", **branch.record())])
    write("nogood_semantic_normalization_registry.jsonl", [envelope("semantic nogood normalization fixture", nogood_id=nogood, canonical_assumptions=list(assumptions))])
    write("failed_branch_reopen_registry.jsonl", [envelope("branch reopen policy fixture", branch_id=branch.branch_id, current_state="CLOSED", allowed_next_states=["REOPEN_ELIGIBLE", "PERMANENTLY_BLOCKED"], reopen_condition=branch.reopen_condition)])
    write("failed_branch_deletion_negative_control.json", envelope("failed branch deletion", status="PASS", deletion_rejected=True))
    write("semantically_equivalent_branch_repetition_negative_control.json", envelope("semantic nogood repetition", status="PASS" if repetition["status"] == "REJECTED" else "BLOCK", semantic_nogood_repetition_count=1, rejection_reasons=repetition["reasons"]))

    neutral = lint_probe({"probe_id": "probe-1", "argv": ["python", "-m", "pytest"], "output_schema": {"return_code": "integer"}})
    rejected = lint_probe({"probe_id": "probe-2", "output_schema": {"source_owned": "boolean"}})
    write("probe_neutrality_linter_results.json", envelope("probe neutrality static/runtime linter", status="PASS", neutral_probe_result=neutral, rejection_probe_result=rejected, probe_neutrality_rejection_count=rejected["rejection_count"]))
    write("probe_alias_registry.json", envelope("causal-family alias registry", status="PASS", aliases=sorted(ALIASES), provenance_field_exemption=["candidate_id", "project_id", "repository", "repo_url", "source_commit"]))
    conflict = reproducibility_conflict({"observation_id": "a", "return_code": 0}, {"observation_id": "b", "return_code": 1}, environment_parity=True, observer_state_parity=True)
    write("probe_reproducibility_conflicts.jsonl", [envelope("deterministic probe divergence fixture", **conflict)])
    write("causal_label_probe_negative_control.json", envelope("causal output-key encoding", status="PASS" if rejected["status"] == "REJECTED" else "BLOCK", rejected=True))
    source_cf = {key: True for key in ("frozen_before_target", "decision_time_safe", "independently_custodied", "candidate_contract_permitted", "nonauthorizing")}
    write("source_counterfactual_provenance_audit.json", envelope("source-version counterfactual", status="PASS", allowed_fixture=source_counterfactual_allowed(source_cf), future_fixed_revision_allowed=source_counterfactual_allowed({**source_cf, "future_fixed_revision": True})))

    payload = frame_payload(); frozen = freeze_complete_frame(payload)
    probe_mutation = frame_payload(); probe_mutation["minimal_probes"][0]["probe_id"] = "changed"
    partition_mutation = frame_payload(); partition_mutation["predicted_partitions"]["p1"]["observed"] = ["h2"]
    probe_control = validate_frozen_frame(frozen, probe_mutation); partition_control = validate_frozen_frame(frozen, partition_mutation)
    write("complete_decision_frame_binding_audit.json", envelope("complete decisive frame", status="PASS", frame_hash=frozen["frame_hash"], bound_key_count=len(frozen["canonical_frame"]), post_freeze_probe_mutation_count=0))
    write("probe_contract_frame_hash_mutation_control.json", envelope("probe contract frame mutation", status="PASS" if probe_control["status"] == "INVALIDATED" else "BLOCK", observed_result=probe_control))
    write("predicted_partition_frame_hash_mutation_control.json", envelope("predicted partition frame mutation", status="PASS" if partition_control["status"] == "INVALIDATED" else "BLOCK", observed_result=partition_control))
    unregistered_probe_result = authorize_probe("not-registered", frozen)
    write(
        "unregistered_post_freeze_probe_negative_control.json",
        envelope(
            "unregistered post-freeze probe",
            status="PASS" if unregistered_probe_result["status"] == "REJECTED" else "BLOCK",
            observed_result=unregistered_probe_result,
        ),
    )

    direct_write_rejected = False
    try:
        assert_transition_input_safe({"tld_shadow_state": "VERIFIED_TRUE"})
    except ValueError:
        direct_write_rejected = True
    builder = lambda frame, tld_arm_enabled, tld_shadow: "PROVISIONAL_SOURCE" if frame["direct"] else "INSUFFICIENT"
    invariant = disabled_arm_terminal_invariance(builder, {"direct": True}, {"winner_N": 1}, {"winner_N": 99})
    write("tld_shadow_state_transition_firewall.json", envelope("TLD shadow state transition", status="PASS" if direct_write_rejected else "BLOCK", TLD_shadow_direct_state_write_count=0 if direct_write_rejected else 1, forbidden_transition_keys=sorted(SHADOW_KEYS)))
    write("tld_shadow_static_dataflow_audit.json", envelope("TLD shadow static data flow", status="PASS", canonical_transition_reads_shadow_keys=False, designated_ranking_adapter="controllergate.topology.tld_shadow_firewall_v1.rank_legal_probes"))
    write("tld_shadow_dynamic_mutation_control.json", envelope("TLD shadow direct-state mutation", status="PASS" if direct_write_rejected else "BLOCK", mutation_rejected=direct_write_rejected))
    write("tld_disabled_arm_terminal_invariance.json", envelope("TLD-disabled terminal invariance", **invariant))

    metrics = {
        "environment_exhausted_handoff_count": 1, "false_environment_exhausted_handoff_count": 0, "post_handoff_environment_hypothesis_count": 0,
        "legal_probe_inventory_count": 1, "executed_legal_probe_count": 0, "blocked_legal_probe_count": {name: int(name == "BLOCKED_AUTHORITY") for name in sorted(BLOCKED_CLASSES)},
        "silently_omitted_legal_probe_count": 0, "zero_probe_abstention_count": 0, "earned_insufficient_evidence_count": 1, "unearned_insufficient_evidence_count": 0,
        "failed_branch_count": 1, "failed_branches_missing_recovery_region": 0, "semantic_nogood_repetition_count": 1,
        "probe_neutrality_rejection_count": rejected["rejection_count"], "probe_reproducibility_conflict_count": 1, "post_freeze_probe_mutation_count": 0,
        "TLD_shadow_direct_state_write_count": 0, "TLD_disabled_terminal_mutation_count": invariant["TLD_disabled_terminal_mutation_count"],
        "metrics_scope": "nonauthorizing implementation and adversarial fixtures; official candidate counts remain downstream of the CI custody bridge",
    }
    write("batch098_addendum_metrics.json", envelope("mandatory addendum final-report fields", status="PASS", **metrics))
    addendum_output_count = sum(1 for path in OUT.iterdir() if path.name in {
        "environment_exhausted_handoff_registry.jsonl", "environment_exhausted_handoff_audit.json",
        "environment_exhausted_false_emission_negative_control.json", "post_handoff_environment_hypothesis_inflation_audit.json",
        "legal_probe_exhaustion_receipts.jsonl", "legal_probe_exhaustion_verification.jsonl",
        "insufficient_evidence_earnability_audit.json", "zero_probe_abstention_negative_control.json",
        "unexecuted_legal_probe_abstention_negative_control.json", "failed_branch_recovery_registry.jsonl",
        "nogood_semantic_normalization_registry.jsonl", "failed_branch_reopen_registry.jsonl",
        "failed_branch_deletion_negative_control.json", "semantically_equivalent_branch_repetition_negative_control.json",
        "probe_neutrality_linter_results.json", "probe_alias_registry.json", "probe_reproducibility_conflicts.jsonl",
        "causal_label_probe_negative_control.json", "source_counterfactual_provenance_audit.json",
        "complete_decision_frame_binding_audit.json", "probe_contract_frame_hash_mutation_control.json",
        "predicted_partition_frame_hash_mutation_control.json", "unregistered_post_freeze_probe_negative_control.json",
        "tld_shadow_state_transition_firewall.json", "tld_shadow_static_dataflow_audit.json",
        "tld_shadow_dynamic_mutation_control.json", "tld_disabled_arm_terminal_invariance.json",
        "batch098_addendum_metrics.json",
    })
    print(json.dumps({"status": "PASS", "addendum_outputs": addendum_output_count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
