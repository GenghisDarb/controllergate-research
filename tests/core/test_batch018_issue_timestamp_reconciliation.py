from controllergate.core.dependency_era_resolution import reconcile_issue_timestamp


def test_conflicting_issue_timestamps_are_detected_and_resolved_by_reviewed_evidence():
    result = reconcile_issue_timestamp(
        carried_artifact_issue_created_at="2020-08-05T00:00:00Z",
        seed_issue_created_at="2021-01-02T00:00:00Z",
        verified_public_issue_created_at="2021-01-02T00:00:00Z",
        target_release_version="1.2.2",
        target_release_date="2020-12-30",
        public_issue_evidence_source="manual_reviewed_targeted_seed_batch013_and_batch018_prompt",
    )

    assert result["status"] == "PASS"
    assert result["timestamp_conflict_detected"] is True
    assert result["dependency_cutoff_timestamp"] == "2021-01-02T00:00:00Z"


def test_unresolved_timestamp_conflict_blocks_dependency_lock_validation():
    result = reconcile_issue_timestamp(
        carried_artifact_issue_created_at="2020-08-05T00:00:00Z",
        seed_issue_created_at="2021-01-02T00:00:00Z",
        verified_public_issue_created_at=None,
    )

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "issue_timestamp_reconciliation_failed"
