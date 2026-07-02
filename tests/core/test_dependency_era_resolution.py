from controllergate.core.dependency_era_resolution import (
    classify_dependency_lock_candidate,
    decision_time_dependency_evidence_policy,
    dependency_era_resolution_policy,
    dependency_resolution_forbidden_sources,
)


def test_latest_unrestricted_dependency_resolution_is_forbidden():
    policy = dependency_era_resolution_policy()
    assert policy["latest_unrestricted_dependency_resolution_allowed"] is False
    assert "latest_unrestricted_pip_resolution" in policy["forbidden_dependency_evidence"]


def test_dependency_release_metadata_required_for_underconstrained_ranges():
    result = classify_dependency_lock_candidate(declared_ranges=[">=1.0"], release_metadata_records=[])
    assert result["status"] == "BLOCK"
    assert result["blocker"] == "dependency_era_lock_unavailable"


def test_recorded_release_metadata_changes_lock_failure_classification():
    result = classify_dependency_lock_candidate(
        declared_ranges=[">=1.0"],
        release_metadata_records=[{"package": "toml", "version": "0.10.0", "released_at_or_before_issue": True}],
    )
    assert result["status"] == "BLOCK"
    assert result["blocker"] == "decision_time_dependency_lock_invalid"


def test_future_dependency_sources_are_explicitly_forbidden():
    forbidden = dependency_resolution_forbidden_sources()
    assert "fixed_later_commit_dependency_metadata" in forbidden["forbidden_sources"]
    assert "future_tests_or_lock_files" in forbidden["forbidden_sources"]
    assert decision_time_dependency_evidence_policy()["unrecorded_local_state_allowed"] is False
