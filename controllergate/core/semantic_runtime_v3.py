from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record
from .interlock_runtime import evaluate_interlocks


RUNTIME_STEPS = (
    "probe_authorization", "immutable_source_materialization", "runtime_identity_establishment",
    "decision_time_provider_resolution", "offline_provider_materialization", "runner_origin_verification",
    "target_origin_verification", "harness_oracle_immutability", "collection_phase_decomposition",
    "failure_family_graph_construction", "elbow_decision", "duplicate_bounded_collection_or_terminal_block",
    "failed_branch_closure_canonical_state_update",
)


STEP_INTERLOCKS = {
    "probe_authorization": ["source_approval", "candidate_seed_classification", "seed_readiness", "cognitive_state_prompt_lock"],
    "immutable_source_materialization": ["artifact_custody", "workspace_purity", "version_origin"],
    "runtime_identity_establishment": ["candidate_isolated_runtime", "cross_environment_orthology"],
    "decision_time_provider_resolution": ["provider_capsule", "cross_environment_orthology"],
    "offline_provider_materialization": ["provider_capsule", "candidate_isolated_runtime"],
    "runner_origin_verification": ["runner_target_split", "version_origin"],
    "target_origin_verification": ["runner_target_split", "harness_origin"],
    "harness_oracle_immutability": ["harness_origin", "workspace_purity"],
    "collection_phase_decomposition": ["command_translation", "step_to_output_contract"],
    "failure_family_graph_construction": ["ast_topology", "failed_branch_closure"],
    "elbow_decision": ["elbow_topology_authorization", "reward_signal", "baseline_drift_precheck"],
    "duplicate_bounded_collection_or_terminal_block": ["duplicate_clean_replay", "count_gate"],
    "failed_branch_closure_canonical_state_update": ["failed_branch_closure", "public_summary_guard", "runtime_activation"],
}


def execute_runtime_path(candidate_id: str, initial_hash: str, facts_by_step: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    transitions = []
    prior_hash = initial_hash
    prior_state = "CG-RXN-011_PASS"
    blocked = False
    for offset, step_id in enumerate(RUNTIME_STEPS, start=12):
        event_id = f"CG-RXN-{offset:03d}"
        facts = facts_by_step[step_id]
        if blocked:
            record = {"event_id": event_id, "candidate_id": candidate_id, "prior_state_hash": prior_hash, "raw_input_hashes": [], "interlocks_evaluated": STEP_INTERLOCKS[step_id], "interlock_decisions": [], "handler_result": {"status": "NOT_RUN"}, "independent_verifier_result": {"status": "NOT_RUN"}, "operation_status": "NOT_RUN", "evidence_status": "NOT_ESTABLISHED", "gate_decision": "BLOCK", "candidate_state": "not_run_upstream_block", "blocker": "upstream_runtime_transition_blocked", "next_action": facts.get("next_action", "close_failed_branch"), "reopen_conditions": ["satisfy_upstream_runtime_transition"], "post_state_hash": ""}
        else:
            evidence_hash = hash_record(facts)
            evaluated = evaluate_interlocks(STEP_INTERLOCKS[step_id], candidate_id=candidate_id, prior_state=prior_state, proposed_next_state=event_id, evidence=facts, evidence_hashes=[evidence_hash])
            requested = facts.get("requested_gate_decision", "PASS")
            decision = "PASS" if evaluated["status"] == "PASS" and requested == "PASS" else "BLOCK"
            record = {"event_id": event_id, "candidate_id": candidate_id, "prior_state_hash": prior_hash, "raw_input_hashes": [evidence_hash], "interlocks_evaluated": STEP_INTERLOCKS[step_id], "interlock_decisions": evaluated["records"], "handler_result": {"status": requested}, "independent_verifier_result": {"status": evaluated["status"]}, "operation_status": facts.get("operation_status", "COMPLETED"), "evidence_status": facts.get("evidence_status", "ESTABLISHED" if decision == "PASS" else "PARTIAL"), "gate_decision": decision, "candidate_state": facts.get("candidate_state", f"{step_id}_{decision.lower()}"), "blocker": None if decision == "PASS" else facts.get("blocker", f"{step_id}_blocked"), "next_action": facts.get("next_action", RUNTIME_STEPS[offset - 11] if offset < 24 else "stop"), "reopen_conditions": [] if decision == "PASS" else facts.get("reopen_conditions", ["provide_missing_evidence"]), "post_state_hash": ""}
            record["interlock_runtime"] = evaluated
        record["post_state_hash"] = hash_record({key: value for key, value in record.items() if key != "post_state_hash"})
        transitions.append(record); prior_hash = record["post_state_hash"]
        if record["gate_decision"] == "BLOCK": blocked = True
        else: prior_state = event_id
    return transitions
