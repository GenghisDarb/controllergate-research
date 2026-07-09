from __future__ import annotations

TERMINAL_STATE_NAMES = [
    "counted_repair",
    "duplicate_replay_candidate",
    "source_only_patch_candidate",
    "pre_repair_materialized",
    "provider_recovery_needed",
    "dependency_recovery_needed",
    "command_boundary_recovery_needed",
    "harness_origin_needed",
    "workspace_purity_blocked",
    "failure_family_decomposition_needed",
    "interpreter_behavior_manual_review",
    "test_expectation_manual_review",
    "unbounded_external_provider",
    "forbidden_evidence_required",
    "not_reproducible",
    "out_of_scope",
    "retired",
    "manual_review",
    "unrecoverable_under_current_policy",
]


def terminal_state_registry() -> dict[str, dict[str, object]]:
    registry: dict[str, dict[str, object]] = {}
    for state in TERMINAL_STATE_NAMES:
        registry[state] = {
            "meaning": state.replace("_", " "),
            "allowed_next_action": "reopen_only_with_new_decision_time_safe_evidence",
            "forbidden_next_action": "patch_generation_without_gate_reopen",
            "count_policy": "no_count_increment" if state != "counted_repair" else "count_increment_requires_count_gate",
            "evidence_required": ["proof_ledger_entry", "hash_pinned_record"],
            "reopen_condition": "new_decision_time_safe_evidence",
            "proof_boundary": "terminal_state_is_not_repair_success",
        }
    return registry


def validate_terminal_state_record(record: dict[str, object]) -> dict[str, object]:
    required = {"meaning", "allowed_next_action", "forbidden_next_action", "count_policy", "evidence_required", "reopen_condition", "proof_boundary"}
    missing = sorted(required - set(record))
    return {"status": "PASS" if not missing else "FAIL", "missing": missing}
