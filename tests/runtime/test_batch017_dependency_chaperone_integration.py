from controllergate.runtime.proof_to_action_compiler import ALLOWED_ACTION_TYPES, compile_action_manifest


def test_manual_dependency_lock_request_is_safe_action_type():
    assert "manual_dependency_lock_request" in ALLOWED_ACTION_TYPES


def test_dependency_precondition_does_not_compile_to_runtime_action():
    action = compile_action_manifest(
        {
            "status": "BLOCK",
            "target_validation": "NOT_RUN",
            "duplicate_replay": "NOT_RUN",
            "post_patch_constraint_revalidation": "NOT_RUN",
            "no_overreach_validation": "NOT_RUN",
        },
        ["provenance"],
        "manual_dependency_lock_request",
    )
    assert action["status"] == "PASS"
    assert action["action_type"] == "manual_dependency_lock_request"
    assert action["executes_action"] is False
