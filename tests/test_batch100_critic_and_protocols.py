from __future__ import annotations

import json
from pathlib import Path

from controllergate.evidence.batch100_independent_critic import findings


ROOT = Path(__file__).resolve().parents[1]


def test_all_future_protocols_remain_protocol_ready() -> None:
    names = (
        "historical_cohort_expansion_protocol_v1.json", "abstention_required_cohort_protocol_v1.json",
        "mixed_failure_cohort_protocol_v1.json", "prospective_validation_protocol_v1.json",
        "memory_lift_validation_protocol_v1.json", "protected_repair_protocol_v1.json",
        "external_replication_protocol_v1.json", "product_beta_exit_criteria_v1.json",
        "self_maintaining_software_evidence_protocol_v1.json",
    )
    for name in names:
        record = json.loads((ROOT / "configs" / name).read_text(encoding="utf-8"))
        assert record["status"] == "PROTOCOL_READY"
        assert "validation completion" in record["authority_forbidden"]


def test_critic_rejects_claim_and_count_mutations() -> None:
    from scripts.run_batch100_independent_critic import base_record

    record = base_record()
    record["repair_count_increment"] = 1
    record["product_beta"] = "pass"
    assert "repair_count_incremented" in findings(record)
    assert "product_beta_promoted" in findings(record)


def test_mutation_campaign_has_fifty_rejections() -> None:
    path = ROOT / "outputs/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock/critic/batch100_semantic_mutation_campaign_summary.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["semantic_mutations_executed"] >= 50
    assert record["semantic_mutations_rejected"] == record["semantic_mutations_executed"]
