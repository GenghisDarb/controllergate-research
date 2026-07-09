from __future__ import annotations

SAFE_ABSTENTION_TRIGGERS = [
    "command_boundary_cannot_be_normalized",
    "provider_unbounded",
    "harness_origin_circular",
    "workspace_purity_fails",
    "runner_target_import_origin_unproven",
    "ast_topology_tests_only_before_patch_gate",
    "patch_license_requires_test_mutation",
    "fixed_gold_future_evidence_required",
    "issue_body_fix_text_needed",
    "same_blocker_repeated_without_new_evidence",
    "source_ownership_unestablished",
    "probe_budget_exceeded",
]


def make_abstention_record(
    *,
    candidate_id: str,
    trigger: str,
    evidence_files: list[str],
    attempt_count: int,
    new_information_since_last_attempt: bool,
    terminal_state: str,
    reopen_condition: str,
    next_allowed_action: str,
) -> dict[str, object]:
    continuing_unsafe = trigger in SAFE_ABSTENTION_TRIGGERS
    return {
        "status": "PASS" if continuing_unsafe else "FAIL",
        "candidate_id": candidate_id,
        "trigger": trigger,
        "evidence_files": evidence_files,
        "attempt_count": attempt_count,
        "new_information_since_last_attempt": new_information_since_last_attempt,
        "why_continuing_would_be_unsafe_or_unbounded": "gate would be bypassed without new decision-time-safe evidence",
        "terminal_state": terminal_state,
        "reopen_condition": reopen_condition,
        "next_allowed_action": next_allowed_action,
    }


def safe_abstention_policy() -> dict[str, object]:
    return {"status": "PASS", "triggers": SAFE_ABSTENTION_TRIGGERS, "abstention_is_not_repair_success": True}
