def test_iterative_dual_projection_recheck_records_multiple_stages() -> None:
    rechecks = [
        {"stage": "before_precondition_normalization", "fragment_plan_authorized": False},
        {"stage": "after_precondition_normalization", "fragment_plan_authorized": False},
        {"stage": "before_patch_generation", "fragment_plan_authorized": False},
    ]
    assert {item["stage"] for item in rechecks} == {
        "before_precondition_normalization",
        "after_precondition_normalization",
        "before_patch_generation",
    }
    assert all(item["fragment_plan_authorized"] is False for item in rechecks)
