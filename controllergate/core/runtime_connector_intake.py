from __future__ import annotations

REQUIRED_RUNTIME_CONNECTOR_FIELDS = [
    "candidate_id",
    "repo_url",
    "issue_url",
    "candidate_sha",
    "required_connector",
    "why_needed",
    "required_sdk_runtime_identity",
    "required_hardware_or_simulator_boundary",
    "allowed_environment",
    "forbidden_credentials_handling",
    "security_risk",
    "license_risk",
    "manual_setup_hint",
    "future_automation_hint",
    "connector_output_hashes_required",
    "approval_condition",
    "reopen_condition",
]


def runtime_connector_intake_schema() -> dict[str, object]:
    return {
        "status": "PASS",
        "required_fields": REQUIRED_RUNTIME_CONNECTOR_FIELDS,
        "raw_connector_payload_commit_allowed": False,
        "credentials_commit_allowed": False,
    }


def validate_runtime_connector_request(record: dict[str, object]) -> dict[str, object]:
    missing = [field for field in REQUIRED_RUNTIME_CONNECTOR_FIELDS if field not in record]
    errors: list[str] = []
    if record.get("required_connector") != "aws_neuron_or_nki_runtime_connector":
        errors.append("required_connector_invalid")
    if record.get("forbidden_credentials_handling") != "no_credentials_tokens_or_account_material_committed":
        errors.append("credentials_boundary_invalid")
    if record.get("connector_output_hashes_required") is not True:
        errors.append("connector_output_hashes_not_required")
    return {"status": "PASS" if not missing and not errors else "FAIL", "missing": missing, "errors": errors}
