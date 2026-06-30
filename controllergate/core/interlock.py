from __future__ import annotations

from typing import Any


def build_coupled_dependency_interlock_map(
    *,
    candidate_id: str,
    patchable_records: list[dict[str, Any]],
    traceback_files: set[str],
    imported_files: set[str],
    ast_files: set[str],
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for record in patchable_records:
        path = str(record.get("file_path", ""))
        reason_codes = set(str(item) for item in record.get("reason_codes", []))
        if path in traceback_files:
            reason_codes.add("traceback_membership")
        if path in imported_files:
            reason_codes.add("target_import_membership")
        if path in ast_files:
            reason_codes.add("ast_closure_membership")
        if path.endswith("__main__.py"):
            role = "target_entry"
        elif path.endswith("import_sorting.py"):
            role = "import_sorting_path"
        elif "formatters/" in path:
            role = "formatter_path"
        elif path.endswith("exceptions.py"):
            role = "exception_path"
        else:
            role = "boundary_only"
        records.append(
            {
                "candidate_id": candidate_id,
                "file_path": path,
                "functions_or_classes": record.get("function_or_class", []),
                "imported_by_target_test": path in imported_files,
                "in_traceback": path in traceback_files,
                "in_ast_closure": path in ast_files,
                "calls_or_called_by_another_admitted_source_file": role in {"target_entry", "import_sorting_path", "formatter_path"},
                "reason_codes": sorted(reason_codes),
                "patchable": True,
                "coupling_role": role,
                "risk_if_modified": "medium" if role in {"target_entry", "import_sorting_path", "formatter_path"} else "low",
                "nearby_tests_or_local_regression_candidates": ["src/darker/tests/test_main_isort.py"],
            }
        )
    return {
        "status": "PASS" if records else "BLOCK",
        "blocker": None if records else "coupled_dependency_interlock_missing",
        "candidate_id": candidate_id,
        "admitted_source_count": len(records),
        "records": records,
    }


def interlock_invariant_candidates(interlock_map: dict[str, Any]) -> dict[str, Any]:
    records = interlock_map.get("records", [])
    roles = {str(record.get("coupling_role")) for record in records if isinstance(record, dict)}
    invariants = [
        {
            "invariant_id": "target_main_isort_skip_glob_relation",
            "description": "The target invokes the command entry path with the import-sorting option against a path covered by the skip pattern.",
            "projection_membership": ["target_test", "target_entry", "import_sorting_path"],
            "required_roles": ["target_entry", "import_sorting_path"],
            "present": {"target_entry", "import_sorting_path"}.issubset(roles),
            "patchable": True,
            "risk_notes": "A patch must not change tests, dependency files, registry files, or broad formatter behavior.",
        },
        {
            "invariant_id": "formatter_entry_point_is_precondition_not_primary_intent",
            "description": "Formatter loading appears in the observed traceback, but the target intent remains the import-sorting skip behavior.",
            "projection_membership": ["target_entry", "formatter_path"],
            "required_roles": ["formatter_path"],
            "present": "formatter_path" in roles,
            "patchable": False,
            "risk_notes": "Formatter changes require a source-facing explanation before patch bytes are authorized.",
        },
    ]
    return {
        "status": "PASS" if any(item["present"] for item in invariants) else "BLOCK",
        "blocker": None if any(item["present"] for item in invariants) else "coupled_dependency_interlock_missing",
        "candidate_id": interlock_map.get("candidate_id"),
        "invariants": invariants,
    }
