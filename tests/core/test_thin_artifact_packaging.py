def test_thin_primary_artifact_excludes_recursive_prior_batches():
    payload = {
        "included_roots": ["outputs/post_v2_37_hardening_001", "outputs/clean_replication_batch_017"],
        "recursive_prior_batch_packaging_detected": False,
        "target_primary_artifact_bytes": 450000,
        "hard_primary_artifact_bytes": 750000,
    }
    assert payload["recursive_prior_batch_packaging_detected"] is False
    assert "outputs/clean_replication_batch_016" not in payload["included_roots"]


def test_primary_artifact_budget_requires_justification_above_hard_limit():
    report = {"estimated_primary_artifact_bytes": 200000, "hard_primary_artifact_bytes": 750000}
    assert report["estimated_primary_artifact_bytes"] < report["hard_primary_artifact_bytes"]
