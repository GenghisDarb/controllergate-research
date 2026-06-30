from controllergate.core.dual_projection import dual_projection_consistency_check


def test_dual_projection_recheck_blocks_until_fragment_plan_authorized() -> None:
    result = dual_projection_consistency_check(
        candidate_id="darker_skip_glob_failing_test",
        fragment_plan={"fragment_plan_authorized": False, "blocker": "target_intent_not_reached"},
        test_facing_projection={"target_intent_addressed": False},
        source_facing_projection={"source_repair_point_admissible": False},
    )
    assert result["status"] == "BLOCK"
    assert result["patch_admissible"] is False
