from controllergate.core.dependency_era_resolution import classify_dependency_lock_candidate


def test_valid_manual_lock_can_be_dependency_lock_candidate_without_source_patch():
    result = classify_dependency_lock_candidate(
        declared_ranges=[">=1.0"],
        release_metadata_records=[],
        manual_lock_record={"status": "PASS", "git_tracked": True, "workflow_visible": True},
    )
    assert result["status"] == "PASS"
    assert result["decision_time_dependency_lock_valid"] is True
    assert result["source_patch_authorized"] is False


def test_untracked_manual_lock_does_not_become_lock_candidate():
    result = classify_dependency_lock_candidate(
        declared_ranges=["==1.0"],
        release_metadata_records=[],
        manual_lock_record={"status": "PASS", "git_tracked": False, "workflow_visible": True},
    )
    assert result["status"] == "BLOCK"
    assert result["decision_time_dependency_lock_valid"] is False
