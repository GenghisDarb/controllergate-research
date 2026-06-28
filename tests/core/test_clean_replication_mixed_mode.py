from __future__ import annotations

import json

from controllergate.experiments.replication_batch import run_replication_batch


def test_mixed_mode_reports_empty_lead_pool_after_curated_seed_absence(tmp_path):
    lead_pool = tmp_path / "empty_leads.json"
    lead_pool.write_text(json.dumps({"leads": []}), encoding="utf-8")
    result = run_replication_batch({"candidate_source_mode": "mixed", "full_scoring": False, "lead_pool_path": str(lead_pool)})
    trace = {item["mode"]: item for item in result["candidate_source_mode_trace"]}

    assert trace["curated_seed"]["attempted"] is True
    assert trace["curated_seed"]["blocker"] == "curated_seed_no_valid_seed"
    assert trace["metadata_probe"]["attempted"] is True
    assert trace["issue_derived"]["attempted"] is True
    assert result["exact_blocker"] == "clean_replication_batch_002_lead_pool_empty"
    assert result["candidate_verification_attempts"] == []


def test_mixed_mode_separates_native_and_issue_derived_empty_pool(tmp_path):
    lead_pool = tmp_path / "empty_leads.json"
    lead_pool.write_text(json.dumps({"leads": []}), encoding="utf-8")
    result = run_replication_batch({"candidate_source_mode": "mixed", "full_scoring": False, "lead_pool_path": str(lead_pool)})

    assert result["metadata_probe_attempts"] == []
    assert result["issue_derived_attempts"] == []
    assert all("py_bugger_issue_65" not in str(item) for item in result["candidate_verification_attempts"])
