from controllergate.core.dependency_era_resolution import validate_manual_dependency_lock_record


def test_manual_dependency_lock_requires_evidence_basis_for_each_version():
    lock = {
        "candidate_id": "darker_issue_112_relative_git_dir",
        "packages": [{"name": "darker", "version": "1.2.2"}],
        "issue_created_at": "2021-01-02T00:00:00Z",
        "forbidden_evidence_attestation": {
            "fixed_commit_used": False,
            "later_commit_used": False,
            "gold_patch_used": False,
            "pr_patch_used": False,
            "future_test_used": False,
            "hidden_label_used": False,
        },
    }

    result = validate_manual_dependency_lock_record(lock, dependency_cutoff_timestamp="2021-01-02T00:00:00Z")

    assert result["status"] == "BLOCK"
    assert "manual_dependency_lock_missing_evidence_basis" in result["blockers"]


def test_future_evidence_in_manual_dependency_lock_blocks():
    lock = {
        "candidate_id": "darker_issue_112_relative_git_dir",
        "packages": [{"name": "darker", "version": "1.2.2", "evidence_basis": [{"source": "reviewed"}]}],
        "issue_created_at": "2021-01-02T00:00:00Z",
        "forbidden_evidence_attestation": {
            "fixed_commit_used": False,
            "later_commit_used": True,
            "gold_patch_used": False,
            "pr_patch_used": False,
            "future_test_used": False,
            "hidden_label_used": False,
        },
    }

    result = validate_manual_dependency_lock_record(lock, dependency_cutoff_timestamp="2021-01-02T00:00:00Z")

    assert result["status"] == "BLOCK"
    assert "manual_dependency_lock_uses_future_evidence" in result["blockers"]
