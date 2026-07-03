from controllergate.core.patch_structure_sensitivity import patch_structure_sensitivity_policy, patch_structure_sensitivity_result


def test_patch_structure_sensitivity_waits_for_patch_and_empirical_gates():
    policy = patch_structure_sensitivity_policy()
    result = patch_structure_sensitivity_result(False, False)
    assert policy["requires_patch_candidate"] is True
    assert policy["requires_empirical_target_validation"] is True
    assert policy["can_replace_repair_validation"] is False
    assert result["status"] == "NOT_RUN_NO_PATCH_CANDIDATE"
