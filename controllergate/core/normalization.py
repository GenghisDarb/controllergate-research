from __future__ import annotations

ALLOWED_NORMALIZATION = {
    "project_pythonpath",
    "venv_creation",
    "declared_dependency_extra",
    "project_declared_pytest_flag",
    "source_tree_temp_config",
}

FORBIDDEN_NORMALIZATION = {
    "create_test",
    "modify_source",
    "use_later_or_gold_file",
    "use_pull_request_patch",
    "install_undeclared_remote_service",
    "edit_dependency_file",
}


def classify_normalization_step(step_type: str) -> dict[str, object]:
    if step_type in ALLOWED_NORMALIZATION:
        return {"step_type": step_type, "status": "PASS", "blocker": None}
    if step_type in FORBIDDEN_NORMALIZATION:
        return {"step_type": step_type, "status": "BLOCK", "blocker": "environment_normalization_unsafe"}
    return {"step_type": step_type, "status": "REVIEW", "blocker": None}


def evaluate_normalization_plan(steps: list[str]) -> dict[str, object]:
    results = [classify_normalization_step(step) for step in steps]
    blockers = [item["blocker"] for item in results if item["blocker"]]
    return {"status": "BLOCK" if blockers else "PASS", "steps": results, "blockers": blockers}
