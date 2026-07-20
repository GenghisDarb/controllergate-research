import json
from pathlib import Path

from controllergate.evidence.batch101_official_ingest import (
    EXPECTED_MANIFEST_COUNTS,
    execution_origin_reconciliation,
    inspect_artifact,
    platform_path,
    semantic_reconciliation,
    verify_manifests,
    verify_sealed_member_tree,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch102_fresh_exact_counterfactual_execution_necessity_sufficiency_ownership_closure"
INGEST = OUT / "batch101_official_ingest"


def test_official_batch101_ingest_receipt_and_exact_identity():
    receipt = json.loads((INGEST / "ingest_receipts/batch101_official_ingest_receipt.json").read_text())
    assert receipt["ingest_status"] == "PASS_OFFICIAL_BATCH101_ARTIFACT_INGEST"
    assert receipt["member_count"] == 75
    assert receipt["manifest_counts"] == EXPECTED_MANIFEST_COUNTS


def test_all_manifests_and_semantic_counts_pass():
    extracted = platform_path(INGEST / "extracted_public_artifact")
    assert verify_manifests(extracted)["status"] == "PASS"
    semantic = semantic_reconciliation(extracted)
    assert semantic["status"] == "PASS"
    assert semantic["raw_replay_records"] == 56
    assert semantic["semantically_reproducible_cells"] == 28


def test_sealed_member_tree_is_cross_platform_and_byte_bound():
    extracted = platform_path(INGEST / "extracted_public_artifact")
    receipt = json.loads((INGEST / "ingest_receipts/batch101_official_ingest_receipt.json").read_text())
    assert verify_sealed_member_tree(extracted, INGEST / "custody/batch101_official_extracted_member_manifest.jsonl", receipt["extracted_tree_hash"])


def test_execution_origin_correction_rejects_fresh_batch101_claim():
    origin = execution_origin_reconciliation(platform_path(INGEST / "extracted_public_artifact"))
    assert origin["status"] == "PASS"
    assert origin["fresh_Batch101_candidate_operation_count"] == 0
    assert origin["inherited_Batch100_raw_replay_count"] == 56
    assert origin["new_candidate_execution_claim_allowed"] is False


def test_wrong_artifact_identity_is_blocked(tmp_path):
    fake = tmp_path / "wrong.zip"
    fake.write_bytes(b"not the artifact")
    try:
        inspect_artifact(fake, "DIRECT_CODEX_ATTACHMENT")
    except Exception:
        return
    raise AssertionError("wrong artifact was accepted")
