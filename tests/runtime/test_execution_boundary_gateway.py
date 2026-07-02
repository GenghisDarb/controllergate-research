from controllergate.runtime.execution_boundary_gateway import build_crossing_record


def test_unverified_actions_cannot_cross_execution_boundary():
    record = build_crossing_record(
        source_hash="a" * 64,
        policy_hash="b" * 64,
        action_manifest={"status": "PASS", "action": "patch_ready_for_review"},
        claim_boundary={"full_scoring": "NOT_RUN/disallowed"},
        verified=False,
    )
    assert record["status"] == "BLOCK"
    assert record["direct_runtime_mutation_allowed"] is False
