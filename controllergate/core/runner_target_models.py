from __future__ import annotations

from typing import Any

RUNNER_TARGET_MODEL_IDS = {
    "declared_self_hosted_runner_model",
    "external_runner_target_split_model",
    "blocked_unproven_runner_target_model",
}

FORBIDDEN_RUNNER_TARGET_SHORTCUTS = [
    "external_runner_chosen_without_metadata_authority",
    "external_runner_chosen_only_because_self_runner_failed",
    "self_hosted_runner_allowed_while_version_origin_unresolved",
    "self_hosted_runner_allowed_without_project_local_command_evidence",
    "pythonpath_injection_without_manifest_and_import_origin_proof",
    "rootdir_override_without_project_metadata",
    "minversion_suppression",
    "pyproject_mutation",
    "test_mutation",
    "fixture_mutation",
    "future_docs",
    "modern_pytest_docs",
    "issue_comment_workaround",
    "fixed_gold_future_source",
]

REQUIRED_MODEL_FIELDS = [
    "model_id",
    "candidate_id",
    "runner_identity",
    "target_identity",
    "runner_import_origin",
    "target_import_origin",
    "command_source",
    "declared_by_buggy_checkout_metadata",
    "requires_external_runner",
    "requires_self_hosted_runner",
    "version_origin_required",
    "version_origin_status",
    "working_directory",
    "sys_path_policy",
    "environment_policy",
    "allowed_command_shape",
    "forbidden_command_shape",
    "decision_time_safe",
    "expected_probe",
    "success_criteria",
    "failure_classification",
    "audit_status",
]


def runner_target_model_schema() -> dict[str, Any]:
    return {
        "status": "PASS",
        "model_ids": sorted(RUNNER_TARGET_MODEL_IDS),
        "required_fields": REQUIRED_MODEL_FIELDS,
        "forbidden_shortcuts": FORBIDDEN_RUNNER_TARGET_SHORTCUTS,
    }


def build_runner_target_model(
    *,
    model_id: str,
    candidate_id: str,
    runner_identity: str,
    target_identity: str,
    runner_import_origin: str,
    target_import_origin: str,
    command_source: str,
    declared_by_buggy_checkout_metadata: bool,
    requires_external_runner: bool,
    requires_self_hosted_runner: bool,
    version_origin_status: str,
    working_directory: str,
    sys_path_policy: str,
    environment_policy: str,
    allowed_command_shape: str,
    forbidden_command_shape: list[str],
    decision_time_safe: bool,
    expected_probe: str,
    success_criteria: list[str],
    failure_classification: str,
    audit_status: str,
) -> dict[str, Any]:
    if model_id not in RUNNER_TARGET_MODEL_IDS:
        raise ValueError(f"unknown runner-target model {model_id}")
    return {
        "model_id": model_id,
        "candidate_id": candidate_id,
        "runner_identity": runner_identity,
        "target_identity": target_identity,
        "runner_import_origin": runner_import_origin,
        "target_import_origin": target_import_origin,
        "command_source": command_source,
        "declared_by_buggy_checkout_metadata": declared_by_buggy_checkout_metadata,
        "requires_external_runner": requires_external_runner,
        "requires_self_hosted_runner": requires_self_hosted_runner,
        "version_origin_required": True,
        "version_origin_status": version_origin_status,
        "working_directory": working_directory,
        "sys_path_policy": sys_path_policy,
        "environment_policy": environment_policy,
        "allowed_command_shape": allowed_command_shape,
        "forbidden_command_shape": forbidden_command_shape,
        "decision_time_safe": decision_time_safe,
        "expected_probe": expected_probe,
        "success_criteria": success_criteria,
        "failure_classification": failure_classification,
        "audit_status": audit_status,
    }


def validate_runner_target_model(model: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_MODEL_FIELDS if field not in model]
    errors: list[str] = []
    if model.get("model_id") not in RUNNER_TARGET_MODEL_IDS:
        errors.append("unknown_runner_target_model")
    if model.get("model_id") == "declared_self_hosted_runner_model":
        if model.get("requires_self_hosted_runner") is not True:
            errors.append("self_hosted_model_without_self_hosted_requirement")
        if model.get("requires_external_runner") is not False:
            errors.append("self_hosted_model_requires_external_runner")
    if model.get("model_id") == "external_runner_target_split_model":
        if model.get("requires_external_runner") is not True:
            errors.append("external_model_without_external_requirement")
        if model.get("requires_self_hosted_runner") is not False:
            errors.append("external_model_requires_self_hosted_runner")
    if model.get("version_origin_status") == "pytest_version_origin_missing_tags":
        errors.append("version_origin_unresolved")
    if model.get("audit_status") not in {"PASS", "BLOCK", "NOT_RUN"}:
        errors.append("invalid_audit_status")
    return {"status": "PASS" if not missing and not errors else "FAIL", "missing": missing, "errors": errors}


def select_runner_target_model(
    *,
    self_hosted_status: str,
    external_status: str,
) -> dict[str, Any]:
    if self_hosted_status == "declared_self_hosted_runner_import_origin_proven":
        return {
            "status": "PASS",
            "selected_model": "declared_self_hosted_runner_model",
            "selection_reason": "self-hosted Pytest runner was declared by project-local metadata and import-origin proof passed",
            "blocked": False,
        }
    if external_status == "external_runner_target_import_origin_proven":
        return {
            "status": "PASS",
            "selected_model": "external_runner_target_split_model",
            "selection_reason": "external runner-target split was declared, isolated, and import-origin proof passed",
            "blocked": False,
        }
    return {
        "status": "BLOCK",
        "selected_model": "blocked_unproven_runner_target_model",
        "selection_reason": "neither self-hosted nor external runner-target model was proven without shortcuts",
        "blocked": True,
    }
