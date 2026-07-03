from controllergate.core.permutation_null_audit import permutation_null_audit_policy, permutation_null_audit_result


def test_permutation_nulls_must_be_preregistered_and_valid():
    policy = permutation_null_audit_policy()
    result = permutation_null_audit_result(False)
    assert policy["preregistration_required"] is True
    assert policy["invalid_by_construction_blocks"] is True
    assert result["invalid_by_construction_null_count"] == 0
    assert result["used_as_repair_evidence"] is False
