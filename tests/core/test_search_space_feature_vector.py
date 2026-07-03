from controllergate.core.search_space_geometry import build_search_space_feature_vector


def test_feature_vector_records_missing_evidence_explicitly():
    vector = build_search_space_feature_vector(
        candidate_id="darker_issue_112_relative_git_dir",
        candidate_class="issue_derived_reproduction_candidate",
        source_type="public_github_repo",
        repo_url="https://github.com/akaihola/darker",
        source_commit_sha=None,
        issue_url="https://github.com/akaihola/darker/issues/112",
        issue_timestamp_status="PASS",
        dependency_lock_status="ABSENT",
        target_intent_alignment_status="NOT_RUN",
        blocker_if_not_probeable="manual_dependency_lock_absent",
    )

    assert "source_commit_sha" in vector["missing_evidence"]
    assert "dependency_lock_validation" in vector["missing_evidence"]
    assert vector["recommended_next_probe"] == "dependency_lock_probe"
