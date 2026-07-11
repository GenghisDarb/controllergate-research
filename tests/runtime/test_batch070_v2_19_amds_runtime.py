from __future__ import annotations

import json
from pathlib import Path

from controllergate.amds.authorization import consume_probe_authorization, issue_probe_authorization
from controllergate.amds.constraints import ALLOWED_CONSTRAINT_TYPES, constraint_semantics_registry
from controllergate.amds.generic_board import build_board_from_evidence
from controllergate.amds.propagation import propagate_constraints
from controllergate.amds.runtime_adapter import run_amds_active_loop
from controllergate.amds.semantic_verification import verify_semantic_claim
from controllergate.protocols.v2_19_authorized_amds_active_maintenance import RUNTIME_BINDINGS, runtime_capabilities
from controllergate.runtime.maintenance_dispatcher import dispatch_candidate_manifest


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/post_v2_37_hardening_batch070_v2_19_amds_fifth_repair_sprint"


def manifest() -> dict:
    return {
        "candidate_id": "candidate-test", "candidate_sha": "a" * 40,
        "repo_url": "https://github.com/example/project", "native_target_paths": ["tests/test_target.py"],
        "source_identity_status": "PASS", "source_custody": "verified_commit_metadata",
        "provider_feasibility_class": "bounded_python_provider_surface_static", "cargo_required": False,
        "command_argv": [], "command_conflicts": ["two_authoritative_sources"],
    }


def board() -> dict:
    return build_board_from_evidence({"candidate_id": "candidate-test", "candidate_sha": "a" * 40, "contacts": {}, "activation_gates": {}})


def test_v2_19_generic_bindings_resolve_without_batch_targets() -> None:
    capabilities = runtime_capabilities()
    assert capabilities["status"] == "PASS"
    assert len(RUNTIME_BINDINGS) == 22
    assert capabilities["batch_specific_current_bindings"] == []
    assert not any("batch068h" in target for target in RUNTIME_BINDINGS.values())


def test_candidate_manifest_execution_and_checkpoint_resume(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.json"
    first = dispatch_candidate_manifest(manifest=manifest(), checkpoint_path=checkpoint, event_ledger_path=tmp_path / "events.jsonl", authorization_store=tmp_path / "nonces.json")
    second = dispatch_candidate_manifest(manifest=manifest(), checkpoint_path=checkpoint, event_ledger_path=tmp_path / "events.jsonl", authorization_store=tmp_path / "nonces.json")
    assert first["status"] == second["status"] == "MANUAL_REVIEW"
    assert first["blocker"] == second["blocker"] == "command_source_conflict_manual_review"
    assert len(first["completed_phases"]) == len(second["completed_phases"]) == 9
    assert second["executed_phases"] == ["recover_authoritative_command"]
    saved = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert saved["context_state"]["provider_closure"]["status"] == "PASS"
    assert saved["context_state"]["rollback"]["status"] == "PASS"
    assert saved["context_state"]["routing_memory_update"]["repair_patch_bytes_stored"] is False


def test_single_use_probe_authorization_and_spent_nonce_rejection(tmp_path: Path) -> None:
    value = issue_probe_authorization(candidate_id="candidate-test", candidate_sha="a" * 40, board_hash=board()["board_hash"], probe_id="p1", allowed_executor="metadata_inspection", network_policy={"network_mode": "none"}, mutation_policy="none", resource_budget={"max_seconds": 1}, nonce="fixed")
    args = dict(store_path=tmp_path / "nonces.json", candidate_id="candidate-test", candidate_sha="a" * 40, board_hash=board()["board_hash"], probe_id="p1", executor="metadata_inspection")
    assert consume_probe_authorization(value, **args)["status"] == "PASS"
    assert consume_probe_authorization(value, **args)["blocker"] == "amds_probe_nonce_already_spent"


def test_backtracking_and_boundary_constraint_semantics() -> None:
    value = board(); result = propagate_constraints(value)
    assert result["backtracking_components"] >= 1
    assert result["ambiguities"]
    assert set(constraint_semantics_registry()) == ALLOWED_CONSTRAINT_TYPES
    assert result["boundary_blocks"]
    assert next(cell for cell in result["cells"] if cell["cell_id"] == "action:source_patch")["state"] == "BLOCKED"


def test_semantic_verifier_recomputes_claim() -> None:
    result = verify_semantic_claim({}, {"semantic_claim": "safe"}, lambda: {"status": "PASS", "semantic_claim": "safe", "evidence_hash": "b" * 64})
    assert result["status"] == "PASS"
    mismatch = verify_semantic_claim({}, {"semantic_claim": "safe"}, lambda: {"status": "PASS", "semantic_claim": "unsafe", "evidence_hash": "b" * 64})
    assert mismatch["status"] == "BLOCK"


def test_persistent_posterior_dynamic_reranking_and_information_gain(tmp_path: Path) -> None:
    value = board()
    probes = [{
        "probe_id": "p1", "probe_type": "issue_timestamp_probe", "deterministic_necessity": True,
        "targeted_hypotheses": ["source_owned", "environment_owned", "test_or_interpreter_owned"],
        "likelihood_outcomes": {"safe": {"probability": 1.0, "posterior": {"source_owned": 0.6, "environment_owned": 0.2, "test_or_interpreter_owned": 0.2}}},
        "allowed_executor": "issue_timestamp_probe", "network_policy": {"network_mode": "none"},
    }]
    observation = {"status": "PASS", "operation_status": "PASS", "observation": "ISSUE_TIMESTAMP_OBSERVED", "evidence_hash": "c" * 64, "mutation_count": 0, "semantic_claim": "safe", "hypothesis_likelihoods": {"source_owned": 0.6, "environment_owned": 0.2, "test_or_interpreter_owned": 0.2}}
    result = run_amds_active_loop(value, probes, lambda _: lambda: observation, budget=1, candidate_sha="a" * 40, authorization_store=tmp_path / "nonces.json", semantic_verifier_factory=lambda _p, _o: lambda: {"status": "PASS", "semantic_claim": "safe", "evidence_hash": "d" * 64})
    assert result["probes_executed"] == 1
    assert len(result["persistent_hypothesis_state"]["events"]) == 1
    assert result["registry_versions"][0]["probes"][0]["expected_information_gain_nats"] != "NOT_ESTABLISHED"
    assert result["rerank_events"][0]["outranking_basis"]


def test_portfolio_freeze_limits_excludes_prior_patches_and_continues() -> None:
    portfolio = json.loads((OUT / "batch070_candidate_portfolio_frozen.json").read_text(encoding="utf-8"))
    execution = json.loads((OUT / "batch070_candidate_execution_results.json").read_text(encoding="utf-8"))["results"]
    assert portfolio["frozen_before_execution"] is True
    assert len(portfolio["candidates"]) == len(execution) == 3
    assert all(not item["prior_patch_exists"] and not item["retired"] for item in portfolio["candidates"])
    assert all(item["terminal_prepatch"] and item["patch_generated"] is False and item["count_gate"] == "NOT_RUN" for item in execution)


def test_shadow_pilot_isolated_matched_and_claim_bounded() -> None:
    pilot = json.loads((OUT / "amds_prospective_shadow_pilot_batch070.json").read_text(encoding="utf-8"))
    assert len(pilot["arms"]) == 4
    assert pilot["same_starting_evidence"] and pilot["matched_probe_budget"] and pilot["matched_compute_budget"]
    assert pilot["seeded_random_reproducible"]
    assert all(not item["source_mutation"] and not item["future_evidence_used"] for item in pilot["results"])
    assert pilot["AMDS_PROSPECTIVE_EFFECTIVENESS"] == "NOT_ESTABLISHED"


def test_v2_18_preserved_v2_19_promoted_and_batch071_handoff_complete() -> None:
    assert (ROOT / "configs/controllergate_v2_18_evidence_derived_topology_historical_provider.yaml").is_file()
    promotion = json.loads((OUT / "v2_19_promotion_decision_batch070.json").read_text(encoding="utf-8"))
    handoff = json.loads((OUT / "batch071_cold_start_handoff.json").read_text(encoding="utf-8"))
    assert promotion["status"] == "PASS" and promotion["protocol_after"] == "v2.19"
    assert handoff["status"] == "PASS" and handoff["primary_objective"]
