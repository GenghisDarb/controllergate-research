import hashlib
import json
from pathlib import Path

from controllergate.evidence.batch102_official_ingest import (
    EXPECTED_MANIFEST_COUNTS,
    inspect_artifact,
    platform_path,
    semantic_reconciliation,
    verify_manifests,
    verify_sealed_member_tree,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization"
INGEST = OUT / "batch102_official_ingest"


def test_official_batch102_ingest_receipt_and_exact_identity():
    receipt = json.loads(
        (INGEST / "ingest_receipts/batch102_official_ingest_receipt.json").read_text()
    )
    assert receipt["ingest_status"] == "PASS_OFFICIAL_BATCH102_ARTIFACT_INGEST"
    assert receipt["member_count"] == 139
    assert receipt["manifest_counts"] == EXPECTED_MANIFEST_COUNTS


def test_all_manifests_and_batch102_semantic_counts_pass():
    extracted = platform_path(INGEST / "extracted_public_artifact")
    assert verify_manifests(extracted)["status"] == "PASS"
    semantic = semantic_reconciliation(extracted)
    assert semantic["status"] == "PASS"
    assert semantic["registered_cells"] == 70
    assert semantic["fresh_executed_cells"] == 18
    assert semantic["blocked_cells"] == 52
    assert semantic["controller_audit_terminals"] == 90


def test_sealed_member_tree_is_cross_platform_and_byte_bound():
    extracted = platform_path(INGEST / "extracted_public_artifact")
    receipt = json.loads(
        (INGEST / "ingest_receipts/batch102_official_ingest_receipt.json").read_text()
    )
    assert verify_sealed_member_tree(
        extracted,
        INGEST / "custody/batch102_official_extracted_member_manifest.jsonl",
        receipt["extracted_tree_hash"],
    )


def test_wrong_batch102_artifact_identity_is_blocked(tmp_path):
    fake = tmp_path / "wrong.zip"
    fake.write_bytes(b"not the artifact")
    try:
        inspect_artifact(fake, "DIRECT_CODEX_ATTACHMENT")
    except Exception:
        return
    raise AssertionError("wrong Batch102 artifact was accepted")


def test_batch103_prompt_contract_is_byte_and_boundary_bound():
    contract = json.loads((ROOT / "configs/batch103_prompt_contract.json").read_text())
    recorded_hash = contract.pop("contract_hash")
    observed_hash = hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert recorded_hash == observed_hash
    assert contract["batch102_artifact_sha256"] == (
        "d45393bc45b5eff2b6bcbe81524a9acbd98eb7e68902a24e08d3f3e5c78466c2"
    )
    assert contract["ordinary_patch_authority"] is False
    assert contract["protected_actuation"] is False
