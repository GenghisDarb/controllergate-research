from __future__ import annotations

from controllergate.core.clean_repair import build_patchable_source_subset


def test_empty_patchable_subset_uses_derivation_blocker() -> None:
    subset = build_patchable_source_subset({"candidate_id": "candidate", "ranked_patchable_sources": []})
    assert subset["status"] == "BLOCK"
    assert subset["blocker"] == "patchable_source_subset_derivation_failed"


def test_forbidden_test_path_is_not_patchable() -> None:
    subset = build_patchable_source_subset(
        {
            "candidate_id": "candidate",
            "ranked_patchable_sources": [
                {
                    "file_path": "src/darker/tests/test_main_isort.py",
                    "patchable": False,
                    "score": 9,
                    "reason_codes": ["test_file"],
                }
            ],
        }
    )
    assert subset["patchable_source_files"] == []
    assert subset["blocker"] == "patchable_source_subset_derivation_failed"
