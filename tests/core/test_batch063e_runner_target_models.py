from __future__ import annotations

from controllergate.core.runner_target_models import (
    FORBIDDEN_RUNNER_TARGET_SHORTCUTS,
    build_runner_target_model,
    runner_target_model_schema,
    select_runner_target_model,
    validate_runner_target_model,
)


def test_runner_target_schema_forbids_blind_external_runner() -> None:
    schema = runner_target_model_schema()
    assert "external_runner_chosen_without_metadata_authority" in schema["forbidden_shortcuts"]
    assert "declared_self_hosted_runner_model" in schema["model_ids"]


def test_self_hosted_model_validates_when_version_origin_is_preserved() -> None:
    model = build_runner_target_model(
        model_id="declared_self_hosted_runner_model",
        candidate_id="pytest_13895_pytest9_skiptest_behavior",
        runner_identity="candidate pytest checkout",
        target_identity="candidate pytest checkout",
        runner_import_origin="candidate/src/pytest",
        target_import_origin="candidate/src/pytest",
        command_source="pyproject.toml [tool.pytest] + tox.ini commands",
        declared_by_buggy_checkout_metadata=True,
        requires_external_runner=False,
        requires_self_hosted_runner=True,
        version_origin_status="pytest_version_origin_normalized_from_predeclared_ancestor_tag_authority",
        working_directory="candidate checkout",
        sys_path_policy="manifested candidate src path only",
        environment_policy="isolated runtime",
        allowed_command_shape="python -m pytest testing -q --tb=no",
        forbidden_command_shape=FORBIDDEN_RUNNER_TARGET_SHORTCUTS,
        decision_time_safe=True,
        expected_probe="import pytest origin probe",
        success_criteria=["pytest.__file__ under candidate checkout"],
        failure_classification="declared_self_hosted_runner_unproven",
        audit_status="PASS",
    )
    assert validate_runner_target_model(model)["status"] == "PASS"


def test_selector_prefers_proven_self_hosted_model() -> None:
    result = select_runner_target_model(
        self_hosted_status="declared_self_hosted_runner_import_origin_proven",
        external_status="external_runner_target_import_origin_proven",
    )
    assert result["selected_model"] == "declared_self_hosted_runner_model"


def test_selector_blocks_when_no_model_is_proven() -> None:
    result = select_runner_target_model(
        self_hosted_status="declared_self_hosted_runner_unproven",
        external_status="external_runner_target_import_origin_unproven",
    )
    assert result["status"] == "BLOCK"
    assert result["selected_model"] == "blocked_unproven_runner_target_model"
