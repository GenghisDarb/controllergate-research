def test_artifact_lineage_index_preserves_prior_evidence_by_sha():
    index = {
        "status": "PASS",
        "prior_artifacts": [
            {
                "batch": "batch016",
                "artifact_sha256": "c9526a9ab21e5341c4f1a74428429ffb28b9ec964e2cfb7c0e697442b4ff131e",
                "ingest_commit": "171f3f3c",
            }
        ],
    }
    assert index["prior_artifacts"][0]["artifact_sha256"].startswith("c9526a9a")
    assert index["prior_artifacts"][0]["ingest_commit"]


def test_lineage_index_has_no_success_claim():
    index = {"status": "PASS", "lineage_only": True, "repair_success_claim": False}
    assert index["lineage_only"] is True
    assert index["repair_success_claim"] is False
