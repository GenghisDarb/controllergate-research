from __future__ import annotations

from typing import Any


def dual_projection_consistency_check(
    *,
    candidate_id: str,
    fragment_plan: dict[str, Any],
    test_facing_projection: dict[str, Any],
    source_facing_projection: dict[str, Any],
) -> dict[str, Any]:
    target_addressed = bool(test_facing_projection.get("target_intent_addressed"))
    source_consistent = bool(source_facing_projection.get("source_repair_point_admissible"))
    fragments_planned = bool(fragment_plan.get("fragment_plan_authorized"))
    if target_addressed and source_consistent and fragments_planned:
        status = "PASS"
        blocker = None
    elif target_addressed and not source_consistent:
        status = "BLOCK"
        blocker = "dual_projection_consistency_failed"
    elif source_consistent and not target_addressed:
        status = "BLOCK"
        blocker = "target_projection_unaddressed"
    else:
        status = "BLOCK"
        blocker = str(fragment_plan.get("blocker") or "fragment_patch_plan_not_generated")
    return {
        "status": status,
        "blocker": blocker,
        "candidate_id": candidate_id,
        "fragment_plan_authorized": fragments_planned,
        "test_facing_projection": test_facing_projection,
        "source_facing_projection": source_facing_projection,
        "patch_admissible": status == "PASS",
    }
