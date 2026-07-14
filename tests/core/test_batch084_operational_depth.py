from __future__ import annotations

import json
from pathlib import Path

from controllergate.batch084.canary import CANARIES
from controllergate.batch084.historical import execute_historical_amds
from controllergate.batch084.orchestrator import product_beta


ROOT = Path(__file__).resolve().parents[2]


def test_locked_historical_canary_patch_hashes_match_repo_bytes():
    import hashlib
    for spec in CANARIES.values():
        assert hashlib.sha256((ROOT / spec["patch"]).read_bytes()).hexdigest() == spec["patch_sha256"]


def test_historical_amds_executes_real_distinct_evidence_probes(tmp_path: Path):
    result = execute_historical_amds(tmp_path)
    assert result["episodes"] == 8
    rows = [json.loads(line) for line in (tmp_path / "batch084_amds_probe_execution_registry.jsonl").read_text(encoding="utf-8").splitlines()]
    grouped = {}
    for row in rows: grouped.setdefault((row["episode_id"], row["strategy"]), []).append(row)
    assert all(len(items) == 6 for items in grouped.values())
    assert all(len({item["source_sha256"] for item in items}) == 6 for items in grouped.values())
    assert all(item["selection_method"] == "deterministic_constraint_elimination" for item in rows)


def test_historical_product_beta_uses_canonical_cli_and_safe_abstains(tmp_path: Path):
    result = product_beta(tmp_path / "out", tmp_path / "runtime")
    assert result["canonical_cli_used"] is True
    assert result["historical_count_increment"] == 0
    assert all(row["canonical_cli_commands"][0].startswith("controllergate run --manifest") for row in result["episodes"])
    assert all(row["status"] == "SAFE_ABSTENTION" for row in result["episodes"])
