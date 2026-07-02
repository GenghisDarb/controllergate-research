from controllergate.core.dependency_era_resolution import manual_dependency_lock_schema_valid


def test_manual_dependency_lock_requires_matching_candidate_and_packages():
    assert manual_dependency_lock_schema_valid(
        {
            "candidate_id": "darker_issue_112_relative_git_dir",
            "packages": [
                {
                    "name": "toml",
                    "version": "0.10.0",
                    "decision_time_safe_evidence": {"source": "selected_source_commit_metadata"},
                }
            ],
        }
    )


def test_manual_dependency_lock_rejects_missing_evidence_basis():
    assert not manual_dependency_lock_schema_valid(
        {
            "candidate_id": "darker_issue_112_relative_git_dir",
            "packages": [{"name": "toml", "version": "0.10.0"}],
        }
    )


def test_manual_dependency_lock_rejects_wrong_candidate():
    assert not manual_dependency_lock_schema_valid(
        {
            "candidate_id": "different_candidate",
            "packages": [
                {
                    "name": "toml",
                    "version": "0.10.0",
                    "decision_time_safe_evidence": {"source": "selected_source_commit_metadata"},
                }
            ],
        }
    )
