from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import pytest

from controllergate.evidence.batch098_official_ingest import (
    EXPECTED_MEMBERS,
    EXPECTED_ROW_COUNTS,
    EXPECTED_SHA256,
    claim_boundary_reconciliation,
    inspect_outer_artifact,
    parse_payload_manifest,
    private_content_scan,
    semantic_reconciliation,
    tree_hash,
    verify_extracted_payload,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger"
INGEST = OUTPUT / "batch098_official_ingest"
EXTRACTED = INGEST / "extracted_public_artifact"


def test_committed_official_ingest_complete() -> None:
    manifest, rows = verify_extracted_payload(EXTRACTED)
    assert manifest["status"] == "PASS"
    assert manifest["checked_payload_count"] == 32
    assert manifest["self_entry_count"] == 0
    assert len(rows) == 33
    assert {row["relative_path"] for row in rows} == set(EXPECTED_MEMBERS)


def test_semantic_and_claim_reconciliation() -> None:
    semantic = semantic_reconciliation(EXTRACTED)
    assert semantic["status"] == "PASS"
    assert semantic["observed_row_counts"] == EXPECTED_ROW_COUNTS
    assert semantic["arm_frame_count"] == 48
    assert semantic["baseline_frame_count"] == 32
    assert semantic["terminal_distribution"] == {"INSUFFICIENT_EVIDENCE": 80}
    assert claim_boundary_reconciliation(EXTRACTED)["status"] == "PASS"


def test_official_receipt_and_tree_binding() -> None:
    receipt = json.loads((INGEST / "ingest_receipts" / "batch098_official_ingest_receipt.json").read_text())
    assert receipt["ingest_status"] == "PASS_OFFICIAL_BATCH098_ARTIFACT_INGEST"
    assert receipt["outer_sha256"] == EXPECTED_SHA256
    assert receipt["extracted_tree_hash"] == tree_hash(EXTRACTED)


def test_private_content_scan_passes() -> None:
    scan = private_content_scan(EXTRACTED)
    assert scan["status"] == "PASS"
    assert all(value == 0 for key, value in scan.items() if key.endswith("_count"))


def test_completion_ledger_prerequisite_persistence() -> None:
    ledger = json.loads((ROOT / "configs" / "batch099_master_completion_ledger.json").read_text())
    goals = {row["goal_id"]: row for row in ledger["goals"]}
    assert "CG-GOAL-000-OFFICIAL-BATCH098-INGEST" in goals
    assert all(
        row["goal_id"] == "CG-GOAL-000-OFFICIAL-BATCH098-INGEST" or "CG-GOAL-000-OFFICIAL-BATCH098-INGEST" in row["prerequisites"]
        for row in ledger["goals"]
    )


def test_prompt_contract_binds_ingest_receipt() -> None:
    contract = json.loads((ROOT / "configs" / "batch099_prompt_contract.json").read_text())
    receipt = INGEST / "ingest_receipts" / "batch098_official_ingest_receipt.json"
    import hashlib
    assert contract["batch098_official_ingest_receipt_sha256"] == hashlib.sha256(receipt.read_bytes()).hexdigest()


@pytest.mark.parametrize("payload", [
    "not a zip", "older artifact 8437787693", "compact private artifact",
])
def test_wrong_outer_artifact_is_blocked(tmp_path: Path, payload: str) -> None:
    candidate = tmp_path / "batch098_public_truth_blind_semantic_closure_v2.zip"
    candidate.write_text(payload)
    assert inspect_outer_artifact(candidate, "DIRECT_CODEX_ATTACHMENT")["status"] == "BLOCK"


def test_filename_only_and_rezipped_artifact_are_blocked(tmp_path: Path) -> None:
    candidate = tmp_path / "batch098_public_truth_blind_semantic_closure_v2.zip"
    with zipfile.ZipFile(candidate, "w") as archive:
        archive.writestr("SHA256SUMS.txt", "")
    result = inspect_outer_artifact(candidate, "DIRECT_CODEX_ATTACHMENT")
    assert not result["sha256_match"]
    assert result["status"] == "BLOCK"


def test_manifest_mutation_and_self_entry_are_blocked(tmp_path: Path) -> None:
    text = "0" * 64 + "  payload.json\n" + "1" * 64 + "  SHA256SUMS.txt\n"
    entries, malformed = parse_payload_manifest(text)
    assert not malformed
    assert entries["SHA256SUMS.txt"] == "1" * 64
    shutil.copytree(EXTRACTED, tmp_path / "tree")
    target = tmp_path / "tree" / "public_claim_boundary.json"
    target.write_text(target.read_text() + " ")
    assert verify_extracted_payload(tmp_path / "tree")[0]["status"] == "BLOCK"


@pytest.mark.parametrize("injected", [
    "Detailed Breakdown of Notebooks 1-11",
    '{"truth_record_id":"private"}',
    r"C:\\Users\\private\\truth.json",
    "ghp_" + "a" * 36,
    "gold_patch: secret",
])
def test_private_content_injection_is_blocked(tmp_path: Path, injected: str) -> None:
    (tmp_path / "injected.txt").write_text(injected)
    assert private_content_scan(tmp_path)["status"] == "BLOCK"


def test_claim_promotion_is_blocked(tmp_path: Path) -> None:
    shutil.copytree(EXTRACTED, tmp_path / "tree")
    path = tmp_path / "tree" / "public_claim_boundary.json"
    value = json.loads(path.read_text())
    value["release_decision"] = "PRODUCT_BETA_PASS"
    path.write_text(json.dumps(value))
    assert claim_boundary_reconciliation(tmp_path / "tree")["status"] == "BLOCK"


def test_row_count_and_frame_duplicate_are_blocked(tmp_path: Path) -> None:
    shutil.copytree(EXTRACTED, tmp_path / "tree")
    path = tmp_path / "tree" / "arm_specific_frame_registry_v2.jsonl"
    rows = path.read_text().splitlines()
    rows[-1] = rows[0]
    path.write_text("\n".join(rows) + "\n")
    assert semantic_reconciliation(tmp_path / "tree")["status"] == "BLOCK"


def test_raw_zip_is_not_tracked() -> None:
    import subprocess
    result = subprocess.run(["git", "ls-files", "incoming_artifacts"], cwd=ROOT, capture_output=True, text=True, check=True)
    assert not result.stdout.strip()
