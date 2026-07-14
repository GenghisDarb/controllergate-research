from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def test_prompt_identity_rejects_stale_batch() -> None:
    value=json.loads((ROOT/"configs/batch083_prompt_contract.json").read_text(encoding="utf-8"))
    assert value["prompt_sentinel"]=="BEGIN_BATCH083_INTEGRATED_CONTINUATION"
    assert value["new_batch"].endswith("batch083_reaction_product_cross_area_wave1g") and value["old_batch_rerun_forbidden"]


def test_loose_end_registry_preserves_historical_ids_and_product_dimensions() -> None:
    current=[json.loads(line) for line in (ROOT/"configs/controllergate_loose_end_registry_v2.jsonl").read_text(encoding="utf-8").splitlines()]
    historical=[json.loads(line) for line in (ROOT/"configs/historical_requirement_registry_v1.jsonl").read_text(encoding="utf-8").splitlines()]
    ids={row["requirement_id"] for row in current};assert {row["requirement_id"] for row in historical}<=ids
    assert {"CG-GAP-002","CG-GAP-003","CG-GAP-004","CG-GAP-005","CG-GAP-006","CG-GAP-013"}<=ids


def test_batch083_official_result_directory_is_bound_to_ingest_record() -> None:
    output = ROOT / "outputs/post_v2_37_hardening_batch083_reaction_product_cross_area_wave1g"
    ingest = json.loads((ROOT / "evidence/official_ingests/batch083_artifact_ingest.json").read_text(encoding="utf-8"))
    assert output.is_dir()
    assert ingest["ingestion"]["status"] == "PASS"
    assert ingest["ingested_output_directory"] == output.relative_to(ROOT).as_posix()
    assert ingest["artifact_sha256"] == "81dc63a786d8d19a71b98874db909db20df7173e794b410e6f04eff1a60ab65e"
    assert ingest["raw_zip_committed"] is False
