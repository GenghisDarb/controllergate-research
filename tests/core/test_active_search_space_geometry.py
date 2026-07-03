from controllergate.core.search_space_geometry import active_search_space_geometry_policy


def test_active_search_space_geometry_cannot_validate_repair():
    policy = active_search_space_geometry_policy()

    assert policy["may_propose_probes"] is True
    assert policy["may_validate_repair"] is False
    assert policy["may_replace_target_validation"] is False
    assert policy["may_replace_artifact_custody"] is False
