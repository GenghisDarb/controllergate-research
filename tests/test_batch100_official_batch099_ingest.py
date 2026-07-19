from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from controllergate.evidence.batch099_official_ingest import (
    EXPECTED_MANIFEST_PAYLOAD_COUNT,
    EXPECTED_MEMBER_COUNT,
    EXPECTED_SHA256,
    claim_reconciliation,
    platform_path,
    private_content_scan,
    semantic_reconciliation,
    tree_hash,
    verify_payload_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock"
INGEST = platform_path(OUTPUT / "batch099_official_ingest")
EXTRACTED = INGEST / "extracted_public_artifact"


def test_official_batch099_ingest_is_complete() -> None:
    receipt = json.loads((INGEST / "ingest_receipts" / "batch099_official_ingest_receipt.json").read_text())
    assert receipt["ingest_status"] == "PASS_OFFICIAL_BATCH099_ARTIFACT_INGEST"
    assert receipt["outer_sha256"] == EXPECTED_SHA256
    assert receipt["member_count"] == EXPECTED_MEMBER_COUNT
    assert receipt["manifest_payload_count"] == EXPECTED_MANIFEST_PAYLOAD_COUNT
    assert receipt["extracted_tree_hash"] == tree_hash(EXTRACTED)


def test_manifest_semantics_claims_and_private_scan_pass() -> None:
    assert verify_payload_manifest(EXTRACTED)["status"] == "PASS"
    assert semantic_reconciliation(EXTRACTED)["status"] == "PASS"
    assert claim_reconciliation(EXTRACTED)["status"] == "PASS"
    assert private_content_scan(EXTRACTED)["status"] == "PASS"


@pytest.mark.parametrize("relative", [
    "causal_differential/batch099_execution_summary.json",
    "causal_differential/batch099_claim_boundary.json",
    "batch098_official_ingest/ingest_receipts/batch098_official_ingest_receipt.json",
])
def test_required_member_mutation_blocks_manifest(tmp_path: Path, relative: str) -> None:
    shutil.copytree(EXTRACTED, tmp_path / "tree")
    target = tmp_path / "tree" / relative
    target.write_bytes(target.read_bytes() + b" ")
    assert verify_payload_manifest(tmp_path / "tree")["status"] == "BLOCK"


def test_raw_zip_and_private_artifacts_are_not_tracked() -> None:
    import subprocess
    tracked = subprocess.run(["git", "ls-files", "incoming_artifacts"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    assert not tracked.strip()
