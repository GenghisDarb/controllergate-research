from __future__ import annotations

import json
from pathlib import Path


BATCH004 = Path("outputs/clean_replication_batch_004")


def _read(path: Path) -> dict[str, object] | list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_issue_derived_harness_policy_requires_hashes_when_used():
    policy = _read(BATCH004 / "issue_derived_harness_policy.json")

    assert policy["issue_text_hash_required_if_used"] is True
    assert policy["generated_harness_hash_required_if_used"] is True
    assert policy["increments_native_count"] is False


def test_issue_derived_attempt_records_no_harness_without_safe_issue_lead():
    attempts = _read(BATCH004 / "issue_derived_attempts.json")
    attempt = attempts[0]

    assert attempt["candidate_class"] == "issue_derived_reproduction_candidate"
    assert attempt["harness_generation_attempted"] is False
    assert attempt["issue_text_hash"] is None
    assert attempt["generated_harness_hash"] is None
    assert attempt["blocker"] == "issue_derived_no_safe_leads"


def test_issue_derived_temporal_guard_records_uncertainty_policy():
    guard = _read(BATCH004 / "issue_text_temporal_guard_batch004.json")

    assert guard["issue_text_hash_required_if_harness_used"] is True
    assert guard["solution_guidance_forbidden"] is True
