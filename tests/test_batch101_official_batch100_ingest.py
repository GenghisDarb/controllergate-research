from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from controllergate.evidence.batch100_official_ingest import (
    EXPECTED_MANIFEST_PAYLOAD_COUNT,
    EXPECTED_MEMBER_COUNT,
    EXPECTED_SHA256,
    claim_reconciliation,
    inspect_outer_artifact,
    semantic_reconciliation,
    verify_top_level_manifests,
)


def _artifact() -> Path:
    candidates = [
        Path("incoming_artifacts/batch101_batch100_official_ingest/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_artifacts.zip"),
        Path.home() / "Downloads" / "post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_artifacts.zip",
    ]
    for path in candidates:
        if path.is_file():
            return path
    pytest.skip("locked Batch100 artifact is not present")


def test_locked_outer_artifact_identity() -> None:
    custody, _ = inspect_outer_artifact(_artifact(), "DIRECT_CODEX_ATTACHMENT")
    assert custody["status"] == "PASS"
    assert custody["member_count"] == EXPECTED_MEMBER_COUNT
    assert custody["observed_sha256"] == EXPECTED_SHA256


def test_all_three_top_level_manifests(tmp_path: Path) -> None:
    with zipfile.ZipFile(_artifact()) as archive:
        archive.extractall(tmp_path)
    result = verify_top_level_manifests(tmp_path)
    assert result["status"] == "PASS"
    assert all(row["checked_payload_count"] == EXPECTED_MANIFEST_PAYLOAD_COUNT for row in result["manifests"].values())
    assert all(row["self_entry_count"] == 0 for row in result["manifests"].values())


def test_semantic_and_claim_reconciliation(tmp_path: Path) -> None:
    with zipfile.ZipFile(_artifact()) as archive:
        archive.extractall(tmp_path)
    assert semantic_reconciliation(tmp_path)["status"] == "PASS"
    assert claim_reconciliation(tmp_path)["status"] == "PASS"


def test_wrong_outer_artifact_is_rejected(tmp_path: Path) -> None:
    wrong = tmp_path / "wrong.zip"
    wrong.write_bytes(b"not the locked artifact")
    with pytest.raises((zipfile.BadZipFile, ValueError, OSError)):
        custody, _ = inspect_outer_artifact(wrong, "DIRECT_CODEX_ATTACHMENT")
        if custody["status"] != "PASS":
            raise ValueError("rejected")


def test_prompt_contract_is_hash_bound() -> None:
    contract = json.loads(Path("configs/batch101_prompt_contract.json").read_text(encoding="utf-8"))
    assert contract["contract_hash"] == "a082fdc2d8f47570780fe47834d8a7ee62e94c54ad2271412d8908c51370bc28"
    assert len(contract["contract_hash"]) == len(hashlib.sha256().hexdigest())
