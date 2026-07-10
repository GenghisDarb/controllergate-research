from __future__ import annotations

from collections.abc import Callable
from typing import Any

from controllergate.core.evidence import hash_record
from .interlock_types import InterlockInput, InterlockOutput, InterlockVerification
from .interlock_transition_policy import transition_allowed


def _base_fact(inp: InterlockInput, policy: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required = tuple(policy.get("required_evidence_classes") or ())
    forbidden = tuple(policy.get("forbidden_evidence_classes") or ())
    for key in required:
        if key not in inp.evidence:
            errors.append(f"required_evidence_missing:{key}")
    for key in forbidden:
        if inp.evidence.get(key):
            errors.append(f"forbidden_evidence_present:{key}")
    if not inp.evidence_hashes or any(len(value) != 64 for value in inp.evidence_hashes):
        errors.append("evidence_hash_invalid")
    if not transition_allowed(inp.prior_state, inp.proposed_next_state, policy):
        errors.append("forbidden_transition")
    return not errors, errors


def _specific_fact(interlock_id: str, evidence: dict[str, Any]) -> bool:
    checks: dict[str, Callable[[dict[str, Any]], bool]] = {
        "artifact_custody": lambda e: e.get("artifact_custody_status") == "PASS",
        "source_approval": lambda e: e.get("source_approved") is True,
        "candidate_seed_classification": lambda e: bool(e.get("candidate_class")),
        "seed_readiness": lambda e: e.get("seed_ready") is True,
        "workspace_purity": lambda e: e.get("workspace_mutation_count", 0) == 0,
        "candidate_isolated_runtime": lambda e: e.get("isolated_runtime") is True,
        "provider_capsule": lambda e: e.get("provider_lock_status") in {"PASS", "PARTIAL", "NOT_RUN"},
        "command_translation": lambda e: isinstance(e.get("command_argv"), list) and bool(e.get("command_argv")),
        "harness_origin": lambda e: e.get("test_tree_hash_match") is not False,
        "version_origin": lambda e: bool(e.get("candidate_sha")),
        "runner_target_split": lambda e: e.get("runner_target_mixed") is not True,
        "cross_environment_orthology": lambda e: isinstance(e.get("orthology_dimensions"), dict),
        "ast_topology": lambda e: e.get("ast_scope_authorized") is not False,
        "elbow_topology_authorization": lambda e: bool(e.get("elbow_classification")),
        "cognitive_state_prompt_lock": lambda e: e.get("decision_time_only") is True,
        "reward_signal": lambda e: e.get("outcome_blind") is True,
        "baseline_drift_precheck": lambda e: e.get("baseline_drift") in {False, None},
        "failed_branch_closure": lambda e: e.get("canonical_state_mutated") is not True,
        "step_to_output_contract": lambda e: bool(e.get("output_contract_hash")),
        "public_summary_guard": lambda e: e.get("claim_boundary_status") == "PASS",
        "duplicate_clean_replay": lambda e: e.get("duplicate_replay") in {"PASS", "NOT_RUN"},
        "count_gate": lambda e: e.get("repair_count_increment") is not True,
        "runtime_activation": lambda e: e.get("runtime_activation_allowed") is False,
    }
    return checks[interlock_id](evidence)


def make_independent_verifier(interlock_id: str, policy: dict[str, Any]):
    def verifier(inp: InterlockInput, output: InterlockOutput) -> InterlockVerification:
        base_ok, errors = _base_fact(inp, policy)
        fact = _specific_fact(interlock_id, inp.evidence)
        expected = "PASS" if base_ok and fact else "BLOCK"
        if output.interlock_id != interlock_id:
            errors.append("interlock_identity_mismatch")
        if output.decision != expected:
            errors.append("handler_verifier_disagreement")
        if output.protected_fact != hash_record({"interlock_id": interlock_id, "evidence": inp.evidence}):
            errors.append("protected_fact_hash_mismatch")
        return InterlockVerification(interlock_id, f"verify_{interlock_id}", "PASS" if not errors else "FAIL", base_ok and fact, tuple(errors))

    verifier.__name__ = f"verify_{interlock_id}"
    return verifier
