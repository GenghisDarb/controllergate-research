from controllergate.core.structured_fragility_audit import structured_fragility_audit_policy, structured_fragility_status


def test_structured_fragility_diagnostic_cannot_validate_repair_alone():
    policy = structured_fragility_audit_policy()
    status = structured_fragility_status(False, False)
    assert policy["diagnostic_only"] is True
    assert policy["can_increment_repair_count"] is False
    assert status["status"] == "NOT_RUN_NO_PATCH_CANDIDATE"
    assert status["used_as_repair_evidence"] is False
