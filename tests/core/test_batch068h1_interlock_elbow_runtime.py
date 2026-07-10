from __future__ import annotations

import hashlib
import json
from pathlib import Path

from controllergate.core.elbow_runtime import decide_elbow
from controllergate.core.elbow_verifier import verify_elbow
from controllergate.core.failure_family import FailureFamilyNode
from controllergate.core.failure_family_graph import FailureFamilyGraph
from controllergate.core.interlock_registry import HANDLERS, REQUIRED_INTERLOCKS, VERIFIERS, resolution_audit
from controllergate.core.interlock_runtime import evaluate_interlocks
from controllergate.core.interlock_transition_policy import transition_allowed
from controllergate.core.target_origin import verify_target_origin_mode

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition"


def load(name: str): return json.loads((OUT / name).read_text(encoding="utf-8"))


def facts():
    return {"candidate_id": "c", "decision_time_evidence": True, "artifact_custody_status": "PASS", "source_approved": True, "candidate_class": "approved", "seed_ready": True, "workspace_mutation_count": 0, "isolated_runtime": True, "provider_lock_status": "PARTIAL", "command_argv": ["python"], "test_tree_hash_match": True, "candidate_sha": "a"*40, "runner_target_mixed": False, "orthology_dimensions": {}, "ast_scope_authorized": True, "elbow_classification": "closed", "decision_time_only": True, "outcome_blind": True, "baseline_drift": False, "canonical_state_mutated": False, "output_contract_hash": "b"*64, "claim_boundary_status": "PASS", "duplicate_replay": "NOT_RUN", "repair_count_increment": False, "runtime_activation_allowed": False, "fixed_commit_used": False, "later_commit_used": False, "gold_patch_used": False, "future_test_used": False, "hidden_benchmark_state_used": False}


def node(fid, parent, depth, isolated=False, reproducible=False, provider=False, harness=False, source=False):
    return FailureFamilyNode(fid, parent, depth, "phase", ("e",), ("log",), ("c"*64,), "classification", 0.8, (), provider, harness, source, False, False, isolated, reproducible, False, ())


def test_all_interlock_handlers_and_verifiers_are_distinct() -> None:
    assert resolution_audit()["status"] == "PASS"
    assert len(REQUIRED_INTERLOCKS) == len(HANDLERS) == len(VERIFIERS) == 23
    assert len({fn.__name__ for fn in HANDLERS.values()}) == 23
    assert len({fn.__name__ for fn in VERIFIERS.values()}) == 23


def test_interlock_handler_verifier_pass_and_forbidden_evidence_block() -> None:
    evidence = facts(); digest = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
    assert evaluate_interlocks(["artifact_custody"], candidate_id="c", prior_state="safe", proposed_next_state="next", evidence=evidence, evidence_hashes=[digest])["status"] == "PASS"
    evidence["fixed_commit_used"] = True
    assert evaluate_interlocks(["artifact_custody"], candidate_id="c", prior_state="safe", proposed_next_state="next", evidence=evidence, evidence_hashes=[digest])["status"] == "BLOCK"


def test_forbidden_transitions_block() -> None:
    assert not transition_allowed("collection_blocked", "patch_generation", {"allowed_prior_states": ["*"], "allowed_next_states": ["*"]})
    assert not transition_allowed("duplicate_replay_missing", "count_gate", {"allowed_prior_states": ["*"], "allowed_next_states": ["*"]})


def test_failure_graph_supports_quaternary_and_deeper() -> None:
    graph = FailureFamilyGraph(); parent = None
    for depth in range(6):
        fid = f"f{depth}"; graph.add(node(fid, parent, depth), "d"*64); parent = fid
    assert graph.max_depth == 5


def test_failure_graph_rejects_invalid_ancestry() -> None:
    graph = FailureFamilyGraph(); graph.add(node("root", None, 0), "d"*64)
    try: graph.add(node("bad", "root", 3), "d"*64)
    except ValueError: pass
    else: raise AssertionError("invalid ancestry accepted")


def test_elbow_closes_without_logs() -> None:
    graph = FailureFamilyGraph(); graph.add(node("root", None, 0, True, True), "d"*64)
    decision = decide_elbow(graph, {}, environment_established=True, logs_available=False)
    assert decision.classification == "elbow_closed_evidence_insufficient"
    assert verify_elbow(decision, graph, {}, environment_established=True, logs_available=False)["status"] == "PASS"


def test_elbow_closes_on_environment_orthology() -> None:
    graph = FailureFamilyGraph(); graph.add(node("root", None, 0, True, True), "d"*64)
    assert decide_elbow(graph, {}, environment_established=False, logs_available=True).classification == "elbow_closed_environment_orthology"


def test_provider_and_harness_local_elbows() -> None:
    required = {name: True for name in ["one_causal_family_isolated", "same_boundary_reproduction", "confounders_controlled", "intervention_is_family_local", "decision_time_evidence_support", "all_interlocks_pass", "rollback_exists", "next_observation_discriminating"]}
    provider = FailureFamilyGraph(); provider.add(node("p", None, 0, True, True, provider=True), "d"*64)
    harness = FailureFamilyGraph(); harness.add(node("h", None, 0, True, True, harness=True), "d"*64)
    assert decide_elbow(provider, required, environment_established=True, logs_available=True).classification == "elbow_open_provider_local_recovery_authorized"
    assert decide_elbow(harness, required, environment_established=True, logs_available=True).classification == "elbow_open_harness_local_recovery_authorized"


def test_elbow_closes_ambiguous_families() -> None:
    graph = FailureFamilyGraph(); graph.add(node("a", None, 0, True, True), "d"*64); graph.add(node("b", None, 0, True, True), "d"*64)
    assert decide_elbow(graph, {}, environment_established=True, logs_available=True).classification == "elbow_closed_multi_family_ambiguous"


def test_target_origin_modes_and_mixed_rejection() -> None:
    source = verify_target_origin_mode("pinned_source_mode", {"origin": "/source/nbclient/__init__.py", "source_hash_match": True, "source_read_only": True, "git_directory_present": False})
    wheel = verify_target_origin_mode("pinned_wheel_mode", {"origin": "/venv/lib/python3.13/site-packages/nbclient/__init__.py", "wheel_hash_verified": True, "source_on_sys_path": False})
    assert source["status"] == wheel["status"] == "PASS"
    assert verify_target_origin_mode("mixed_mode", {})["status"] == "BLOCK"


def test_generated_provider_locks_are_separate_and_future_safe() -> None:
    decision = load("decision_time_provider_lock_batch068h1.json"); current = load("current_declared_provider_lock_preservation_batch068h1.json")
    assert decision["arm"] != current["arm"]
    assert decision["future_package_admission_count"] == 0
    assert current["classification"] == "diagnostic_only_not_decision_time_reproduction"


def test_environment_vector_and_origin_conflict() -> None:
    dimensions = load("nbclient_observed_environment_vector_batch068h1.json")["dimensions"]
    by_name = {item["dimension"]: item["status"] for item in dimensions}
    assert len(dimensions) == 16
    assert by_name["language_runtime_identity"] == "ESTABLISHED"
    assert by_name["target_origin_identity"] == "CONFLICTED"


def test_failed_branch_cannot_mutate_canonical_state() -> None:
    proof = load("canonical_state_nonmutation_proof_batch068h1.json")
    assert proof["canonical_state_mutation_count"] == 0
    assert proof["failed_branches_mutated_canonical_state"] is False


def test_semantic_runtime_is_fully_interlock_bound() -> None:
    binding = load("semantic_runtime_interlock_binding_batch068h1.json")
    assert binding["runtime_transition_count"] == binding["interlock_bound_transition_count"] == 13
    assert binding["unbound_runtime_transition_count"] == 0


def test_architectural_promotion_does_not_authorize_patch() -> None:
    promotion = load("v2_16_promotion_decision_batch068h1.json")
    final = load("batch068h1_final_decision.json")
    assert promotion["status"] == "PASS"
    assert promotion["candidate_success_controlled_promotion"] is False
    assert final["patch_generated"] is final["patch_applied"] is final["repair_count_increment"] is False


def test_unauthorized_replay_count_and_full_scoring_rejected() -> None:
    controls = load("interlock_negative_control_results_batch068h1.json")
    assert controls["replay_without_target_pass"] == "BLOCK"
    assert controls["count_without_duplicate_replay"] == "BLOCK"
    assert controls["full_scoring_request"] == "BLOCK"
