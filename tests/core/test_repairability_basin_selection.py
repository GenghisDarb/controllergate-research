from __future__ import annotations

from pathlib import Path

from controllergate.core.clean_repair import build_patchable_source_subset, repairability_basin_selection


def test_repairability_basin_selection_ranks_patchable_source(tmp_path: Path):
    source = tmp_path / "src" / "darker" / "__main__.py"
    source.parent.mkdir(parents=True)
    source.write_text("def _drop_changes_on_unedited_lines():\n    return None\n", encoding="utf-8", newline="\n")
    routing = {
        "candidate_id": "candidate",
        "traceback_candidate_source_files": [],
        "imported_candidate_source_files": ["src/darker/__main__.py"],
        "AST_closure_candidate_source_files": ["src/darker/__main__.py"],
    }

    selection = repairability_basin_selection(
        {"candidate_id": "candidate"},
        routing,
        tmp_path,
        {"command_record": {"output_summary": "unchanged drop_changes failure"}},
    )
    subset = build_patchable_source_subset(selection)

    assert selection["status"] == "PASS"
    assert subset["patchable_source_files"] == ["src/darker/__main__.py"]
