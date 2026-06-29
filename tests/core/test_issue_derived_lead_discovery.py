from __future__ import annotations

import json
from pathlib import Path


BATCH005 = Path("outputs/clean_replication_batch_005")


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_targeted_issue_path_runs_before_broad_discovery_after_native_failure():
    state = _read(BATCH005 / "consolidated_state_clean_replication_batch_005.json")
    targeted = _read(BATCH005 / "targeted_issue_seed_intake_report.json")
    policy = _read(BATCH005 / "issue_derived_lead_discovery_policy.json")

    if state["native_challenge_candidate_verified"] is False:
        assert targeted["execution_order"] == "after_native_retry_before_broad_issue_discovery"
        assert policy["runs_after_targeted_seed_intake"] is True


def test_issue_derived_fallback_is_not_native_evidence():
    state = _read(BATCH005 / "consolidated_state_clean_replication_batch_005.json")
    claim = _read(BATCH005 / "claim_boundary.json")

    assert state["confirmed_external_native_repair_episodes"] == 3 + state["repair_successes_count"]
    assert claim["issue_derived_evidence_remains_separate"] is True
    assert claim["preliminary_single_candidate_memory_separation_evidence"] is False


def test_zero_issue_leads_require_discovery_blocker():
    state = _read(BATCH005 / "consolidated_state_clean_replication_batch_005.json")
    pool = _read(BATCH005 / "issue_derived_lead_pool.json")
    rejections = _read(BATCH005 / "issue_derived_rejection_ledger.json")

    if state["issue_derived_discovery_attempted"] and pool["lead_count"] == 0:
        blockers = {item["blocker"] for item in rejections}
        assert blockers & {"issue_derived_no_safe_leads", "issue_derived_discovery_network_unavailable"}
