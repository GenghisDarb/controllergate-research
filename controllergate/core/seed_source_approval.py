from __future__ import annotations

from typing import Any

ALLOWED_BATCH068_SOURCE_CLASSES = {
    "manual_artifact_custody",
    "approved_external_issue_source",
    "approved_external_benchmark_source",
    "registry_derived_unused_candidate",
    "orthology_transfer_routing_only",
    "diagnostic_only",
    "rejected_lead",
    "blocked_untrusted_source",
}

PROMOTABLE_BATCH068_SEED_CLASSES = {
    "curated_manual_custody",
    "approved_inferred_registry_derived",
    "approved_external_issue_source",
}

FORBIDDEN_DIRECT_REPAIR_SEED_CLASSES = {
    "already_counted_repair",
    "parked_candidate_without_reopen_evidence",
    "probe_only_environmental",
    "orthology_transfer_routing_only",
    "diagnostic_only",
    "untrusted_source",
    "fixed_patch_derived",
    "gold_patch_derived",
    "future_commit_derived",
    "issue_comment_fix_text_only",
}


def batch068_source_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "allowed_source_classes": sorted(ALLOWED_BATCH068_SOURCE_CLASSES),
        "promotable_future_repair_attempt_seed_classes": sorted(PROMOTABLE_BATCH068_SEED_CLASSES),
        "forbidden_direct_repair_seed_classes": sorted(FORBIDDEN_DIRECT_REPAIR_SEED_CLASSES),
        "patch_generation_allowed": False,
        "patch_application_allowed": False,
        "duplicate_replay_allowed": False,
        "count_gate_allowed": False,
        "memory_opportunity_is_routing_only": True,
        "full_scoring": "NOT_RUN/disallowed",
        "self_maintaining_software": "false/not_demonstrated",
    }


def batch068_rejected_source_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "already_counted_repairs_excluded_from_active_seed_inventory": True,
        "parked_candidates_require_specific_reopen_evidence": True,
        "probe_only_sources_are_diagnostic_until_promoted": True,
        "routing_only_sources_cannot_authorize_patch_generation": True,
        "fixed_gold_future_or_patch_derived_sources_forbidden": True,
        "issue_comment_fix_text_cannot_be_patch_guidance": True,
    }


def approve_batch068_source_class(source_class: str) -> dict[str, Any]:
    allowed = source_class in ALLOWED_BATCH068_SOURCE_CLASSES
    return {
        "status": "PASS" if allowed else "BLOCK",
        "source_class": source_class,
        "allowed_for_batch068_intake": allowed,
        "exact_blocker": None if allowed else "blocked_untrusted_source",
    }
