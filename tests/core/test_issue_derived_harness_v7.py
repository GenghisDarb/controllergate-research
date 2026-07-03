import json
from pathlib import Path


def test_harness_v7_waits_for_target_intent_and_keeps_evidence_separate():
    base = Path("outputs/clean_replication_batch_022")
    if base.exists():
        policy = json.loads((base / "issue_derived_harness_v7_policy.json").read_text(encoding="utf-8"))
        result = json.loads((base / "issue_derived_harness_v7_verification_result.json").read_text(encoding="utf-8"))
        claim = json.loads((base / "claim_boundary_batch022.json").read_text(encoding="utf-8"))
        assert policy["requires_target_intent_alignment"] is True
        assert policy["future_fixed_gold_pr_evidence_forbidden"] is True
        assert result["harness_generated"] is False
        assert claim["native_repair_episode_count"] == 4
        assert claim["memory_lift"] == "not_demonstrated"
