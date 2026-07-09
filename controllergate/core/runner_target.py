from __future__ import annotations

RUNNER_TARGET_CLASSES = {
    "runner_target_split_not_required",
    "runner_target_collision_unresolved_self_runner",
    "external_runner_selected_without_import_origin_proof",
    "external_runner_target_import_origin_proven",
    "runner_target_unknown",
}


def classify_runner_target(
    *,
    runner_package: str,
    target_package: str,
    external_runner_selected: bool = False,
    target_import_origin_proven: bool = False,
) -> str:
    if external_runner_selected and target_import_origin_proven:
        return "external_runner_target_import_origin_proven"
    if external_runner_selected and not target_import_origin_proven:
        return "external_runner_selected_without_import_origin_proof"
    if runner_package == target_package:
        return "runner_target_collision_unresolved_self_runner"
    if runner_package and target_package:
        return "runner_target_split_not_required"
    return "runner_target_unknown"


def runner_target_import_origin_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "allowed_classifications": sorted(RUNNER_TARGET_CLASSES),
        "external_runner_requires_import_origin_proof": True,
        "self_testing_project_collision_must_block_or_split": True,
    }
