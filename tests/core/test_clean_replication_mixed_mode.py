from __future__ import annotations

from controllergate.experiments.replication_batch import run_replication_batch


def test_mixed_mode_progresses_after_curated_seed_absence():
    result = run_replication_batch({"candidate_source_mode": "mixed", "full_scoring": False})
    trace = {item["mode"]: item for item in result["candidate_source_mode_trace"]}

    assert trace["curated_seed"]["attempted"] is True
    assert trace["curated_seed"]["blocker"] == "curated_seed_no_valid_seed"
    assert trace["metadata_probe"]["attempted"] is True
    assert trace["issue_derived"]["attempted"] is True
    assert result["exact_blocker"] == "clean_replication_batch_002_no_verified_candidates"
    assert result["candidate_verification_attempts"]


def test_mixed_mode_separates_native_and_issue_derived_attempts():
    result = run_replication_batch({"candidate_source_mode": "mixed", "full_scoring": False})

    assert result["metadata_probe_attempts"][0]["blocker"] == "metadata_probe_no_verified_candidates"
    assert result["issue_derived_attempts"][0]["blocker"] == "issue_derived_no_verified_candidates"
    assert all("py_bugger_issue_65" not in str(item) for item in result["candidate_verification_attempts"])
