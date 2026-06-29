from __future__ import annotations

from pathlib import Path

from controllergate.core.clean_repair import imported_candidate_sources, source_files_from_failure_text


def test_project_source_frames_create_patchable_candidates(tmp_path: Path) -> None:
    checkout = tmp_path
    source = checkout / "src/darker/import_sorting.py"
    source.parent.mkdir(parents=True)
    source.write_text("def sort_imports():\n    return None\n", encoding="utf-8")
    summary = "Traceback\n  File \"src/darker/import_sorting.py\", line 1, in sort_imports\nAssertionError"
    assert source_files_from_failure_text(checkout, summary) == ["src/darker/import_sorting.py"]


def test_target_test_imports_candidate_source(tmp_path: Path) -> None:
    checkout = tmp_path
    test_path = checkout / "src/darker/tests/test_main_isort.py"
    test_path.parent.mkdir(parents=True)
    (checkout / "src/darker").mkdir(parents=True, exist_ok=True)
    (checkout / "src/darker/import_sorting.py").write_text("def sort_imports():\n    return None\n", encoding="utf-8")
    test_path.write_text("from darker.import_sorting import sort_imports\n", encoding="utf-8")
    assert imported_candidate_sources(checkout, "src/darker/tests/test_main_isort.py") == ["src/darker/import_sorting.py"]
