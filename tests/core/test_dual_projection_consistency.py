from controllergate.core.dual_projection import dual_projection_consistency_check


def test_dual_projection_blocks_target_only_fragment() -> None:
    result = dual_projection_consistency_check(
        candidate_id="darker_skip_glob_failing_test",
        fragment_plan={"fragment_plan_authorized": True},
        test_facing_projection={"target_intent_addressed": True},
        source_facing_projection={"source_repair_point_admissible": False},
    )
    assert result["status"] == "BLOCK"
    assert result["blocker"] == "dual_projection_consistency_failed"


def test_dual_projection_blocks_unaddressed_target() -> None:
    result = dual_projection_consistency_check(
        candidate_id="darker_skip_glob_failing_test",
        fragment_plan={"fragment_plan_authorized": True},
        test_facing_projection={"target_intent_addressed": False},
        source_facing_projection={"source_repair_point_admissible": True},
    )
    assert result["status"] == "BLOCK"
    assert result["blocker"] == "target_projection_unaddressed"
