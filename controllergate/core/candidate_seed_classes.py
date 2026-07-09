from __future__ import annotations

SEED_CLASSES = [
    "curated_manual_custody",
    "inferred_registry_derived",
    "orthology_transfer",
    "probe_only_environmental",
    "already_counted_repair",
    "diagnostic_only",
    "rejected_lead",
    "blocked_untrusted_source",
]

REPAIR_ELIGIBLE_CLASSES = {"curated_manual_custody", "inferred_registry_derived"}

REQUIRED_SEED_FIELDS = [
    "seed_id",
    "candidate_id",
    "source_type",
    "source_url_or_path",
    "source_hash",
    "custody_status",
    "discovered_by",
    "decision_time_safe",
    "label_blind",
    "gold_patch_excluded",
    "future_evidence_excluded",
    "approval_status",
    "approval_requirements",
    "allowed_next_actions",
    "forbidden_next_actions",
    "promotion_required_before_repair",
    "exact_blocker_if_not_approved",
]


def classify_seed_for_repair(seed: dict[str, object]) -> dict[str, object]:
    missing = [field for field in REQUIRED_SEED_FIELDS if field not in seed]
    seed_class = seed.get("source_type")
    errors: list[str] = []
    if seed_class not in SEED_CLASSES:
        errors.append("candidate_seed_class_missing")
    if seed.get("decision_time_safe") is not True:
        errors.append("seed_not_decision_time_safe")
    if seed.get("gold_patch_excluded") is not True or seed.get("future_evidence_excluded") is not True:
        errors.append("forbidden_evidence_not_excluded")
    approved = seed.get("approval_status") == "approved"
    repair_allowed = seed_class in REPAIR_ELIGIBLE_CLASSES and approved and not missing and not errors
    blocker = None
    if not repair_allowed:
        if seed_class == "orthology_transfer":
            blocker = "blocked_unpromoted_orthology_seed_used_for_patch_generation"
        elif seed_class == "inferred_registry_derived" and not approved:
            blocker = "blocked_unpromoted_inferred_seed_used_for_patch_generation"
        elif seed_class in {"probe_only_environmental", "already_counted_repair", "diagnostic_only"}:
            blocker = "manual_artifact_custody_or_external_source_approval_required_for_new_unused_candidate_seed"
        else:
            blocker = seed.get("exact_blocker_if_not_approved") or "blocked_untrusted_source"
    return {
        "status": "PASS" if not missing and not errors else "FAIL",
        "repair_generation_allowed": repair_allowed,
        "missing": missing,
        "errors": errors,
        "blocker": blocker,
    }


def seed_promotion_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "repair_eligible_classes": sorted(REPAIR_ELIGIBLE_CLASSES),
        "orthology_transfer_is_routing_only_until_promoted": True,
        "probe_only_sources_do_not_enter_candidate_inventory": True,
        "already_counted_repairs_excluded": True,
    }
