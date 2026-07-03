from controllergate.core.dependency_overlap_grouping import dependency_overlap_audit, dependency_overlap_groups


def test_dependency_overlap_groups_prevent_double_counting():
    groups = dependency_overlap_groups([
        {"name": "black"},
        {"name": "click"},
        {"name": "pip"},
    ])
    audit = dependency_overlap_audit(groups)
    assert groups["status"] == "PASS"
    assert audit["status"] == "PASS"
    assert audit["dependency_overlap_double_count_detected"] is False
