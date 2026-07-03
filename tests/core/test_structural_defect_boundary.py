from controllergate.core.structural_defect_boundary import classify_boundary


def test_dependency_precondition_boundary_is_not_code_defect():
    boundary = classify_boundary(dependency_lock_status="ABSENT", target_intent_alignment=False)

    assert boundary["boundary_class"] == "dependency_precondition_boundary"
    assert "patch_generation_without_empirical_gate" in boundary["forbidden_actions"]


def test_target_intent_boundary_is_not_repair_success():
    boundary = classify_boundary(dependency_lock_status="PASS", target_intent_alignment=False)

    assert boundary["boundary_class"] == "target_intent_boundary"
    assert boundary["claim_boundary"] == "diagnostic_only_until_empirical_validation"
