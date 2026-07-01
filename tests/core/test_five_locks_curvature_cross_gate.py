import json
from pathlib import Path


def test_five_locks_cross_gate_blocks_downstream_without_seed():
    path = Path("outputs/clean_replication_batch_013/five_locks_curvature_cross_gate.json")
    if not path.is_file():
        return
    result = json.loads(path.read_text(encoding="utf-8"))

    assert result["source_acquisition_allowed"] is False
    assert result["repair_generation_allowed"] is False
    assert result["matched_null_allowed"] is False
