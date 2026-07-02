from controllergate.runtime.proof_to_action_compiler import compile_action_manifest


def test_manual_lock_absence_compiles_to_safe_non_executing_action():
    action = compile_action_manifest(
        {
            "status": "BLOCK",
            "target_validation": "NOT_RUN",
            "duplicate_replay": "NOT_RUN",
            "post_patch_constraint_revalidation": "NOT_RUN",
            "no_overreach_validation": "NOT_RUN",
        },
        ["manual_dependency_lock_absent"],
        "manual_dependency_lock_request",
    )

    assert action["status"] == "PASS"
    assert action["action_type"] == "manual_dependency_lock_request"
    assert action["executes_action"] is False
