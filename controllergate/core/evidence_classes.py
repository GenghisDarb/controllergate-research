from __future__ import annotations

ISSUE_DERIVED_CLASS = "issue_derived_reproduction_candidate"
ISSUE_DERIVED_SCOREABILITY = "ephemeral_test_provenance_only"
NATIVE_CLASS = "native_buggy_tree_test_candidate"


def classify_candidate_evidence(candidate_class: str) -> dict[str, object]:
    if candidate_class == ISSUE_DERIVED_CLASS:
        return {
            "candidate_class": ISSUE_DERIVED_CLASS,
            "scoreability_class": ISSUE_DERIVED_SCOREABILITY,
            "increments_native_count": False,
            "increments_issue_derived_count": True,
        }
    return {
        "candidate_class": NATIVE_CLASS,
        "scoreability_class": "native_buggy_tree_test_provenance",
        "increments_native_count": True,
        "increments_issue_derived_count": False,
    }


def temporal_guard_policy() -> dict[str, object]:
    return {
        "selected_source_commit_at_or_before_issue_creation_when_possible": True,
        "issue_text_used_for_generation_must_not_include_solution_guidance": True,
        "issue_edit_history_unavailable_status": "issue_text_edit_history_uncertain",
        "repair_context_excludes_fix_or_gold_material": True,
        "blockers": [
            "issue_text_temporal_guard_failed",
            "issue_text_edit_history_uncertain",
            "issue_contains_solution_guidance",
            "issue_derived_latent_knowledge_risk_unbounded",
            "issue_derived_harness_context_firewall_failed",
        ],
    }
