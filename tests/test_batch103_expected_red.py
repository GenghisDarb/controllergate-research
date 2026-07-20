import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RED = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization/batch103_pre_isomorphism_reactome_closure_expected_failure.json"


def test_batch103_expected_red_is_sealed_and_complete():
    report = json.loads(EXPECTED_RED.read_text())
    assert report["status"] == "BATCH103_PRE_ISOMORPHISM_REACTOME_CLOSURE_FAIL_EXPECTED"
    assert report["boundary_commit"] == "17ce08e828dfe5c5c0c77ad162188723af53607b"
    assert report["finding_count"] == 45
    assert len(report["findings"]) == 45
    assert all(
        {
            "commit",
            "path",
            "symbol",
            "line_range",
            "source_authority",
            "risk",
            "required_correction",
            "red_to_green_test",
        }.issubset(row)
        for row in report["findings"]
    )


def test_batch103_expected_red_covers_mandatory_boundaries():
    report = json.loads(EXPECTED_RED.read_text())
    ids = {row["finding_id"] for row in report["findings"]}
    assert "legacy_chapter_round_robin_primitive_assignment" in ids
    assert "all_reactome_scenarios_use_plan_maturation" in ids
    assert "mcm_fourteen_nucleosome_196bp_claim_unsafe" in ids
    assert "no_source_grounded_reactome_planner" in ids
    assert "no_canonical_isomorphism_authority_registry" in ids
