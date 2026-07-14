import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_poetry_matrix_is_frozen_one_factor_then_bounded_pairwise():
    value = json.loads((ROOT / "configs/batch084_poetry_differential_preregistration.json").read_text(encoding="utf-8"))
    assert len(value["stage_one_factors"]) == 13
    assert value["repetitions_per_arm"] == 2
    assert value["unrestricted_combinatorial_search"] is False
    assert value["preregistered_pairwise_hypotheses"] == [
        ["absolute_versus_relative_working_path", "powershell_versus_direct_process"],
        ["HOME", "cache_directory"],
    ]
