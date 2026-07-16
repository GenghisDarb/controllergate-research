from __future__ import annotations

from pathlib import Path

from controllergate.reactome_ir.migration import verify_v1_to_v2_migration


ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "outputs/post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction/reactome_reactions.jsonl"
V2 = ROOT / "outputs/post_v2_37_hardening_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure/reactome_structured_rpir_v2_reactions.jsonl"


def test_rpir_v1_to_v2_occurrence_migration_is_complete_and_idempotent() -> None:
    result = verify_v1_to_v2_migration(V1, V2)
    assert result["status"] == "PASS"
    assert result["v1_count"] == result["v2_count"] == 16814
    assert result["missing_count"] == result["extra_count"] == 0
    assert result["idempotent"] is True
