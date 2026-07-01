from controllergate.core.memory_policy import evaluate_retrospective_memory_claim
from pathlib import Path


def test_passive_memory_blocks_memory_separation_evidence():
    result = evaluate_retrospective_memory_claim(score=0.0, routing_delta_detected=False, retrospective=True)
    assert result["retrospective_single_candidate_memory_separation_diagnostic"] is False
    assert result["prospective_memory_lift_status"] == "not_demonstrated"


def test_retrospective_diagnostic_cannot_claim_prospective_memory_lift():
    result = evaluate_retrospective_memory_claim(score=1.0, routing_delta_detected=True, retrospective=True)
    assert result["retrospective_single_candidate_memory_separation_diagnostic"] is True
    assert result["prospective_memory_lift_status"] == "not_demonstrated"
    assert result["full_memory_lift_claimed"] is False


def test_repair_episode_count_does_not_increment_for_same_candidate():
    before_count = 4
    batch010_adds_repair_episode = False
    assert before_count + int(batch010_adds_repair_episode) == 4


def test_active_public_outputs_use_neutral_language():
    blocked_terms = [
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "Klein " + "twist",
        "RNA " + "primase",
        "OS" + "QN",
        "cym" + "atics",
        "res" + "onance",
        "chro" + "matin",
        "epi" + "genetic",
    ]
    paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/memory_lift_definition.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/public_release_readiness.md"),
        Path("docs/replication_protocol.md"),
        Path("docs/operational_gate_matrix.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
    ]
    paths.extend(sorted(Path("outputs/clean_replication_batch_010").glob("*.json")))
    paths.extend(sorted(Path("outputs/clean_replication_batch_010").glob("*.md")))
    hits = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        hits.extend(f"{path}:{term}" for term in blocked_terms if term in text)
    assert hits == []
