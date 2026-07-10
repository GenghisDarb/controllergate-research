from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record
from .interlock_types import InterlockInput, InterlockOutput
from .interlock_verifiers import make_independent_verifier
from .interlock_transition_policy import transition_allowed


REQUIRED_INTERLOCKS = (
    "artifact_custody", "source_approval", "candidate_seed_classification", "seed_readiness",
    "workspace_purity", "candidate_isolated_runtime", "provider_capsule", "command_translation",
    "harness_origin", "version_origin", "runner_target_split", "cross_environment_orthology",
    "ast_topology", "elbow_topology_authorization", "cognitive_state_prompt_lock", "reward_signal",
    "baseline_drift_precheck", "failed_branch_closure", "step_to_output_contract", "public_summary_guard",
    "duplicate_clean_replay", "count_gate", "runtime_activation",
)

FORBIDDEN_EVIDENCE = ("fixed_commit_used", "later_commit_used", "gold_patch_used", "future_test_used", "hidden_benchmark_state_used")


def default_policy(interlock_id: str) -> dict[str, Any]:
    return {
        "interlock_id": interlock_id,
        "typed_input_schema": "controllergate.interlock_input.v2",
        "typed_output_schema": "controllergate.interlock_output.v2",
        "handler": f"handle_{interlock_id}",
        "verifier": f"verify_{interlock_id}",
        "required_evidence_classes": ["candidate_id", "decision_time_evidence"],
        "forbidden_evidence_classes": list(FORBIDDEN_EVIDENCE),
        "allowed_prior_states": ["*"],
        "allowed_next_states": ["*"],
        "forbidden_transitions": ["patch_without_target_replay", "count_without_duplicate_replay"],
        "blocker_vocabulary": [f"{interlock_id}_blocked", "forbidden_transition", "evidence_incomplete"],
        "reopen_conditions": [f"provide_verified_{interlock_id}_evidence"],
        "terminal_state_behavior": "stop_and_close_branch",
    }


def make_handler(interlock_id: str, policy: dict[str, Any]):
    def handler(inp: InterlockInput) -> InterlockOutput:
        required_ok = all(key in inp.evidence for key in policy["required_evidence_classes"])
        forbidden_ok = not any(inp.evidence.get(key) for key in policy["forbidden_evidence_classes"])
        transition_ok = transition_allowed(inp.prior_state, inp.proposed_next_state, policy)
        from .interlock_verifiers import _specific_fact
        decision = "PASS" if required_ok and forbidden_ok and transition_ok and _specific_fact(interlock_id, inp.evidence) else "BLOCK"
        return InterlockOutput(
            interlock_id,
            f"handle_{interlock_id}",
            decision,
            hash_record({"interlock_id": interlock_id, "evidence": inp.evidence}),
            None if decision == "PASS" else f"{interlock_id}_blocked",
            tuple(() if decision == "PASS" else policy["reopen_conditions"]),
        )

    handler.__name__ = f"handle_{interlock_id}"
    return handler


POLICIES = {name: default_policy(name) for name in REQUIRED_INTERLOCKS}
HANDLERS = {name: make_handler(name, POLICIES[name]) for name in REQUIRED_INTERLOCKS}
VERIFIERS = {name: make_independent_verifier(name, POLICIES[name]) for name in REQUIRED_INTERLOCKS}


def resolution_audit() -> dict[str, Any]:
    handler_names = {fn.__name__ for fn in HANDLERS.values()}
    verifier_names = {fn.__name__ for fn in VERIFIERS.values()}
    missing_handlers = sorted(set(REQUIRED_INTERLOCKS) - set(HANDLERS))
    missing_verifiers = sorted(set(REQUIRED_INTERLOCKS) - set(VERIFIERS))
    return {
        "status": "PASS" if not missing_handlers and not missing_verifiers and len(handler_names) == len(REQUIRED_INTERLOCKS) and len(verifier_names) == len(REQUIRED_INTERLOCKS) else "FAIL",
        "interlock_count": len(REQUIRED_INTERLOCKS),
        "handler_count": len(HANDLERS),
        "verifier_count": len(VERIFIERS),
        "missing_handlers": missing_handlers,
        "missing_verifiers": missing_verifiers,
        "generic_nonempty_verifier_count": sum("nonempty" in name for name in verifier_names),
    }
