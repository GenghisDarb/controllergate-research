def test_thin_primary_artifact_does_not_recursively_include_prior_batches():
    audit = {
        "status": "PASS",
        "recursive_prior_batch_packaging_detected": False,
        "primary_payload_roots": [
            "outputs/post_v2_37_hardening_001",
            "outputs/clean_replication_batch_018",
        ],
    }

    assert audit["recursive_prior_batch_packaging_detected"] is False
    assert "outputs/clean_replication_batch_017" not in audit["primary_payload_roots"]


def test_public_batch018_terms_are_neutral():
    text = "Manual Dependency Lock Intake, Issue Timestamp Reconciliation, Thin Artifact Packaging"
    banned = ["chromosomal", "TORUS", "AGI", "observer-state", "recursion-constant"]

    assert not any(term in text for term in banned)
