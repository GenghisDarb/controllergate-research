from controllergate.core.interlock import build_coupled_dependency_interlock_map, interlock_invariant_candidates


def test_coupled_dependency_interlock_map_requires_records() -> None:
    result = build_coupled_dependency_interlock_map(
        candidate_id="darker_skip_glob_failing_test",
        patchable_records=[],
        traceback_files=set(),
        imported_files=set(),
        ast_files=set(),
    )
    assert result["status"] == "BLOCK"
    assert result["blocker"] == "coupled_dependency_interlock_missing"


def test_interlock_invariant_present_for_main_and_import_sorting() -> None:
    result = build_coupled_dependency_interlock_map(
        candidate_id="darker_skip_glob_failing_test",
        patchable_records=[
            {"file_path": "src/darker/__main__.py", "function_or_class": ["main"], "reason_codes": []},
            {"file_path": "src/darker/import_sorting.py", "function_or_class": ["apply_isort"], "reason_codes": []},
        ],
        traceback_files={"src/darker/__main__.py"},
        imported_files={"src/darker/__main__.py", "src/darker/import_sorting.py"},
        ast_files={"src/darker/__main__.py", "src/darker/import_sorting.py"},
    )
    invariants = interlock_invariant_candidates(result)
    assert result["status"] == "PASS"
    assert invariants["status"] == "PASS"
    assert any(item["invariant_id"] == "target_main_isort_skip_glob_relation" and item["present"] for item in invariants["invariants"])
