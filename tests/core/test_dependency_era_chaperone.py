from controllergate.core.dependency_era_chaperone import classify_dependency_precondition, dependency_era_policy


def test_dependency_era_mismatch_blocks_patch_admission():
    result = classify_dependency_precondition("TypeError: unsupported operand type(s) for /: 'tuple' and 'str'", [">=1"])
    assert result["classification"] == "dependency_era_mismatch_candidate"
    assert result["source_patch_authorized"] is False
    assert result["blocker"] == "dependency_api_precondition_unresolved"


def test_latest_unrestricted_dependency_resolution_is_not_accepted():
    policy = dependency_era_policy()
    assert "latest_unrestricted_pip_resolution" in policy["forbidden_resolution_methods"]
    assert policy["patch_before_target_behavior_allowed"] is False
