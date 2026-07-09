from __future__ import annotations

import hashlib
import json

REQUIRED_FAILURE_SIGNATURE_FIELDS = [
    "exception_type",
    "returncode",
    "command_kind",
    "runner_package",
    "target_package",
    "working_directory",
    "python_version",
    "os",
    "dependency_state",
    "missing_module_or_fixture",
    "failing_test_path",
    "failing_test_symbol",
    "source_contact_files",
    "provider_surface",
    "source_surface",
    "harness_surface",
    "workspace_surface",
    "classification",
    "signature_hash",
]

FAILURE_CLASSES = [
    "source_code_failure",
    "provider_failure",
    "command_boundary_failure",
    "workspace_purity_failure",
    "harness_origin_failure",
    "runner_target_failure",
    "fixture_materialization_failure",
    "environment_specific_failure",
    "orthology_transfer_candidate",
    "terminal_unrecoverable_under_current_policy",
]


def signature_hash(signature: dict[str, object]) -> str:
    copy = dict(signature)
    copy.pop("signature_hash", None)
    return hashlib.sha256(json.dumps(copy, sort_keys=True).encode("utf-8")).hexdigest()


def classify_failure_signature(signature: dict[str, object]) -> str:
    exception = str(signature.get("exception_type", "")).lower()
    classification = str(signature.get("classification", ""))
    returncode = signature.get("returncode")
    if classification in FAILURE_CLASSES:
        return classification
    if returncode == 127 or "command not found" in exception:
        return "command_boundary_failure"
    if "modulenotfound" in exception or signature.get("dependency_state") == "missing":
        return "provider_failure"
    if signature.get("missing_module_or_fixture"):
        return "fixture_materialization_failure"
    if signature.get("runner_package") == signature.get("target_package"):
        return "runner_target_failure"
    if not signature.get("source_contact_files"):
        return "environment_specific_failure"
    return "source_code_failure"


def validate_failure_signature(signature: dict[str, object]) -> dict[str, object]:
    missing = [field for field in REQUIRED_FAILURE_SIGNATURE_FIELDS if field not in signature]
    computed = signature_hash(signature)
    class_ = classify_failure_signature(signature)
    return {
        "status": "PASS" if not missing and signature.get("signature_hash") == computed else "FAIL",
        "missing": missing,
        "computed_signature_hash": computed,
        "classification": class_,
        "hash_matches": signature.get("signature_hash") == computed,
    }


def environment_specific_failure_classifier_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "checked_conditions": [
            "returncode_127_command_not_found",
            "module_not_found",
            "fixture_missing",
            "minversion_blocked",
            "runner_target_collision",
            "setuptools_scm_tag_missing",
            "shallow_clone_missing_tags",
            "workspace_import_path_mismatch",
            "stale_workflow_snapshot",
            "provider_backend_unavailable",
            "source_only_patch_partial_improvement",
            "no_safe_patch_candidate_generated",
            "tests_only_source_contact",
            "harness_origin_untrusted",
        ],
        "allowed_classifications": FAILURE_CLASSES,
    }
